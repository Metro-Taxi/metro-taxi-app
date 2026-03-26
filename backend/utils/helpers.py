# Utility functions and constants for Métro-Taxi backend

import bcrypt
import jwt
import secrets
from datetime import datetime, timezone, timedelta

# JWT Configuration
JWT_SECRET = None  # Set from environment
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def init_jwt(secret: str):
    global JWT_SECRET
    JWT_SECRET = secret

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, role: str) -> str:
    """Create a JWT token for a user"""
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and validate a JWT token"""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

def generate_verification_token() -> str:
    """Generate a secure random verification token"""
    return secrets.token_urlsafe(32)

# Subscription Plans (prices in cents to avoid floating point issues)
SUBSCRIPTION_PLANS = {
    "24h": {"name": "24 heures", "price": 6.99, "price_cents": 699, "duration_hours": 24},
    "week": {"name": "1 semaine", "price": 16.99, "price_cents": 1699, "duration_hours": 168},
    "month": {"name": "1 mois", "price": 53.99, "price_cents": 5399, "duration_hours": 720}
}

# Driver earnings rate
DRIVER_RATE_PER_KM = 1.50

# Payout configuration
PAYOUT_DAY = 10  # Day of month for automatic payouts
MIN_PAYOUT_AMOUNT = 10.0  # Minimum amount for payout
