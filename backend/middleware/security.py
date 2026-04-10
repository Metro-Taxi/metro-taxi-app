"""
Security Middleware for Métro-Taxi Application
Protection contre:
- Attaques par force brute (login)
- Rate limiting (DDoS)
- Injection SQL/NoSQL
- XSS et CSRF
- Tentatives de hacking
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timezone, timedelta
from typing import Dict, Set
import re
import logging
import hashlib

logger = logging.getLogger(__name__)

# ============================================
# RATE LIMITER CONFIGURATION
# ============================================
limiter = Limiter(key_func=get_remote_address)

# ============================================
# SECURITY CONFIGURATION
# ============================================
# Blocked IPs (temporary bans)
blocked_ips: Dict[str, datetime] = {}
# Failed login attempts tracker
failed_login_attempts: Dict[str, Dict] = {}
# Suspicious activity tracker
suspicious_activity: Dict[str, int] = {}

# Thresholds
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15
MAX_SUSPICIOUS_SCORE = 10
IP_BAN_DURATION_MINUTES = 30
SUSPICIOUS_PATTERNS = [
    r"<script",
    r"javascript:",
    r"on\w+\s*=",
    r"\.\./",
    r"etc/passwd",
    r"select\s+.*\s+from",
    r"union\s+select",
    r"drop\s+table",
    r"insert\s+into",
    r"delete\s+from",
    r"\$where",
    r"\$gt",
    r"\$lt",
    r"\$ne",
    r"\$regex",
    r"admin'--",
    r"' or '1'='1",
    r"1=1",
]

# Sensitive endpoints requiring stricter limits
SENSITIVE_ENDPOINTS = {
    "/api/auth/login": "5/minute",
    "/api/auth/register": "3/minute",
    "/api/driver/register": "3/minute",
    "/api/admin/": "10/minute",
    "/api/payments/": "5/minute",
}

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_client_ip(request: Request) -> str:
    """Extract real client IP, considering proxies"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def is_ip_blocked(ip: str) -> bool:
    """Check if IP is currently blocked"""
    if ip in blocked_ips:
        if datetime.now(timezone.utc) < blocked_ips[ip]:
            return True
        else:
            del blocked_ips[ip]
    return False

def block_ip(ip: str, duration_minutes: int = IP_BAN_DURATION_MINUTES):
    """Temporarily block an IP"""
    blocked_ips[ip] = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
    logger.warning(f"🚫 IP BLOCKED: {ip} for {duration_minutes} minutes")

def detect_suspicious_content(content: str) -> bool:
    """Detect potentially malicious content"""
    if not content:
        return False
    content_lower = content.lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, content_lower, re.IGNORECASE):
            return True
    return False

def sanitize_input(value: str) -> str:
    """Basic input sanitization"""
    if not isinstance(value, str):
        return value
    # Remove potential script tags and dangerous characters
    value = re.sub(r'<[^>]*>', '', value)
    value = value.replace('$', '').replace('{', '').replace('}', '')
    return value.strip()

def increment_suspicious_score(ip: str, reason: str):
    """Track suspicious activity from an IP"""
    if ip not in suspicious_activity:
        suspicious_activity[ip] = 0
    suspicious_activity[ip] += 1
    logger.warning(f"⚠️ Suspicious activity from {ip}: {reason} (Score: {suspicious_activity[ip]})")
    
    if suspicious_activity[ip] >= MAX_SUSPICIOUS_SCORE:
        block_ip(ip, IP_BAN_DURATION_MINUTES * 2)
        suspicious_activity[ip] = 0

# ============================================
# LOGIN PROTECTION
# ============================================

def record_failed_login(ip: str, email: str = None):
    """Record a failed login attempt"""
    if ip not in failed_login_attempts:
        failed_login_attempts[ip] = {
            "count": 0,
            "first_attempt": datetime.now(timezone.utc),
            "locked_until": None,
            "emails": set()
        }
    
    data = failed_login_attempts[ip]
    data["count"] += 1
    if email:
        data["emails"].add(email)
    
    logger.warning(f"🔐 Failed login attempt from {ip} (Count: {data['count']}, Email: {email})")
    
    if data["count"] >= MAX_FAILED_LOGIN_ATTEMPTS:
        data["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)
        logger.warning(f"🔒 IP {ip} locked out for {LOGIN_LOCKOUT_MINUTES} minutes after {data['count']} failed attempts")
        
        # If trying many different emails, it's likely a brute force attack
        if len(data["emails"]) > 3:
            block_ip(ip, IP_BAN_DURATION_MINUTES * 2)

def is_login_allowed(ip: str) -> tuple[bool, str]:
    """Check if login is allowed from this IP"""
    if ip in failed_login_attempts:
        data = failed_login_attempts[ip]
        if data["locked_until"]:
            if datetime.now(timezone.utc) < data["locked_until"]:
                remaining = (data["locked_until"] - datetime.now(timezone.utc)).seconds // 60
                return False, f"Too many failed attempts. Try again in {remaining + 1} minutes."
            else:
                # Reset after lockout period
                failed_login_attempts[ip] = {
                    "count": 0,
                    "first_attempt": datetime.now(timezone.utc),
                    "locked_until": None,
                    "emails": set()
                }
    return True, ""

def clear_failed_login(ip: str):
    """Clear failed login attempts after successful login"""
    if ip in failed_login_attempts:
        del failed_login_attempts[ip]

# ============================================
# SECURITY MIDDLEWARE
# ============================================

class SecurityMiddleware(BaseHTTPMiddleware):
    """Main security middleware"""
    
    async def dispatch(self, request: Request, call_next):
        client_ip = get_client_ip(request)
        path = request.url.path
        method = request.method
        
        # 1. Check if IP is blocked
        if is_ip_blocked(client_ip):
            logger.warning(f"🚫 Blocked IP {client_ip} attempted to access {path}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied. Your IP has been temporarily blocked."}
            )
        
        # 2. Check for suspicious URL patterns
        full_url = str(request.url)
        if detect_suspicious_content(full_url):
            increment_suspicious_score(client_ip, f"Suspicious URL: {full_url[:100]}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid request"}
            )
        
        # 3. Check query parameters for injection attempts
        for key, value in request.query_params.items():
            if detect_suspicious_content(value):
                increment_suspicious_score(client_ip, f"Suspicious query param: {key}={value[:50]}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid request parameters"}
                )
        
        # 4. Check for login lockout (only for login endpoint)
        if "/api/auth/login" in path and method == "POST":
            allowed, message = is_login_allowed(client_ip)
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": message}
                )
        
        # 5. Log the request for monitoring
        if "/api/admin" in path or "/api/payments" in path:
            logger.info(f"📝 Sensitive endpoint accessed: {method} {path} from {client_ip}")
        
        # 6. Continue with request
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"❌ Error processing request from {client_ip}: {str(e)}")
            raise

# ============================================
# RATE LIMIT ERROR HANDLER
# ============================================

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors"""
    client_ip = get_client_ip(request)
    increment_suspicious_score(client_ip, f"Rate limit exceeded: {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Too many requests. Please slow down.",
            "retry_after": "60 seconds"
        }
    )

# ============================================
# SECURITY HEADERS MIDDLEWARE
# ============================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(self), microphone=()"
        
        # Cache control for sensitive endpoints
        if "/api/admin" in request.url.path or "/api/payments" in request.url.path:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        
        return response

# ============================================
# ADMIN SECURITY FUNCTIONS
# ============================================

def get_security_stats() -> dict:
    """Get security statistics for admin dashboard"""
    now = datetime.now(timezone.utc)
    
    return {
        "blocked_ips_count": len(blocked_ips),
        "blocked_ips": [
            {"ip": ip, "expires": exp.isoformat()} 
            for ip, exp in blocked_ips.items() if exp > now
        ],
        "failed_login_ips_count": len(failed_login_attempts),
        "suspicious_ips": [
            {"ip": ip, "score": score}
            for ip, score in suspicious_activity.items()
            if score > 0
        ],
        "lockouts_active": sum(
            1 for data in failed_login_attempts.values() 
            if data.get("locked_until") and data["locked_until"] > now
        )
    }

def manual_block_ip(ip: str, duration_minutes: int = 60) -> bool:
    """Manually block an IP (admin function)"""
    block_ip(ip, duration_minutes)
    return True

def manual_unblock_ip(ip: str) -> bool:
    """Manually unblock an IP (admin function)"""
    if ip in blocked_ips:
        del blocked_ips[ip]
        logger.info(f"✅ IP {ip} manually unblocked")
        return True
    return False
