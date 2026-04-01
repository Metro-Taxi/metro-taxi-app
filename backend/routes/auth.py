"""
Routes API pour l'authentification et la gestion des comptes
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
import uuid
import asyncio
import os
import bcrypt
import jwt
import secrets

# Imports locaux
from database import db
from models.schemas import (
    UserRegister, LoginRequest, EmailVerificationRequest
)
from services.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

# JWT Configuration - initialized from server.py
JWT_SECRET = os.environ.get('JWT_SECRET', 'metro-taxi-secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


# ============================================
# HELPER FUNCTIONS
# ============================================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)


# ============================================
# REGISTRATION ROUTES
# ============================================

@router.post("/register/user")
async def register_user(data: UserRegister, request: Request):
    """Register a new user account"""
    # Import send_verification_email from server (to avoid circular imports)
    from server import send_verification_email
    
    existing = await db.users.find_one({"email": data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    user_id = str(uuid.uuid4())
    verification_token = generate_verification_token()
    
    user_doc = {
        "id": user_id,
        "first_name": data.first_name,
        "last_name": data.last_name,
        "email": data.email,
        "phone": data.phone,
        "password": hash_password(data.password),
        "role": "user",
        "email_verified": False,
        "verification_token": verification_token,
        "subscription_active": False,
        "subscription_expires": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Create response before inserting to avoid ObjectId contamination
    user_response = {k: v for k, v in user_doc.items() if k not in ["password", "verification_token"]}
    
    await db.users.insert_one(user_doc)
    
    # Store verification token separately for easy lookup
    await db.email_verifications.insert_one({
        "token": verification_token,
        "user_id": user_id,
        "user_type": "user",
        "email": data.email,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    })
    
    # Generate verification URL
    host_url = os.environ.get("FRONTEND_URL", "https://metro-taxi-demo.emergent.host")
    verification_url = f"{host_url}/verify-email?token={verification_token}"
    
    # Get language from Accept-Language header
    accept_lang = request.headers.get("accept-language", "fr")
    lang = accept_lang.split(",")[0].split("-")[0] if accept_lang else "fr"
    
    # Send verification email (async, non-blocking)
    asyncio.create_task(send_verification_email(
        email=data.email,
        name=data.first_name,
        verification_url=verification_url,
        lang=lang
    ))
    
    token = create_token(user_id, "user")
    return {
        "token": token, 
        "user": user_response,
        "verification_url": verification_url,
        "message": "Un email de vérification a été envoyé"
    }


# ============================================
# EMAIL VERIFICATION ROUTES
# ============================================

@router.post("/verify-email")
async def verify_email(data: EmailVerificationRequest):
    """Verify user email with token"""
    verification = await db.email_verifications.find_one({"token": data.token}, {"_id": 0})
    
    if not verification:
        return {
            "message": "Votre compte est déjà vérifié ! Vous pouvez vous connecter.",
            "verified": True,
            "already_verified": True
        }
    
    # Check expiration
    expires_at = datetime.fromisoformat(verification["expires_at"])
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token de vérification expiré")
    
    user_type = verification["user_type"]
    user_id = verification["user_id"]
    
    # Update user/driver as verified
    if user_type == "user":
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"email_verified": True}}
        )
    else:
        await db.drivers.update_one(
            {"id": user_id},
            {"$set": {"email_verified": True}}
        )
    
    # Delete verification token
    await db.email_verifications.delete_one({"token": data.token})
    
    return {"message": "Email vérifié avec succès", "verified": True}


@router.get("/verification-status")
async def get_verification_status(current_user: dict = Depends(get_current_user)):
    """Get current user's email verification status"""
    user_id = current_user["user_id"]
    role = current_user["role"]
    
    if role == "user":
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "email_verified": 1})
        return {"email_verified": user.get("email_verified", False) if user else False}
    elif role == "driver":
        driver = await db.drivers.find_one({"id": user_id}, {"_id": 0, "email_verified": 1})
        return {"email_verified": driver.get("email_verified", False) if driver else False}
    
    return {"email_verified": True}  # Admin always verified


@router.post("/resend-verification")
async def resend_verification(current_user: dict = Depends(get_current_user), request: Request = None):
    """Resend verification email"""
    from server import send_verification_email
    
    user_id = current_user["user_id"]
    role = current_user["role"]
    
    if role == "user":
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        if user.get("email_verified"):
            return {"message": "Email déjà vérifié"}
        email = user["email"]
        name = user.get("first_name", "Utilisateur")
        user_type = "user"
    elif role == "driver":
        driver = await db.drivers.find_one({"id": user_id}, {"_id": 0})
        if not driver:
            raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
        if driver.get("email_verified"):
            return {"message": "Email déjà vérifié"}
        email = driver["email"]
        name = driver.get("first_name", "Chauffeur")
        user_type = "driver"
    else:
        return {"message": "Vérification non requise"}
    
    # Delete old tokens
    await db.email_verifications.delete_many({"user_id": user_id})
    
    # Create new token
    verification_token = generate_verification_token()
    await db.email_verifications.insert_one({
        "token": verification_token,
        "user_id": user_id,
        "user_type": user_type,
        "email": email,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    })
    
    # Generate verification URL
    host_url = os.environ.get("FRONTEND_URL", "https://metro-taxi-demo.emergent.host")
    verification_url = f"{host_url}/verify-email?token={verification_token}"
    
    # Send verification email (async, non-blocking)
    asyncio.create_task(send_verification_email(
        email=email,
        name=name,
        verification_url=verification_url,
        lang="fr"
    ))
    
    return {"message": "Email de vérification renvoyé", "verification_url": verification_url}


# ============================================
# LOGIN ROUTES
# ============================================

@router.post("/login")
async def login(data: LoginRequest):
    """Authenticate user and return JWT token"""
    # Check users first
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if user and verify_password(data.password, user["password"]):
        user_data = {k: v for k, v in user.items() if k != "password"}
        if user.get("role") == "admin":
            token = create_token(user["id"], "admin")
            return {"token": token, "admin": user_data}
        else:
            token = create_token(user["id"], "user")
            return {"token": token, "user": user_data}
    
    # Check drivers
    driver = await db.drivers.find_one({"email": data.email}, {"_id": 0})
    if driver and verify_password(data.password, driver["password"]):
        if not driver.get("is_validated"):
            raise HTTPException(status_code=403, detail="Compte en attente de validation admin")
        token = create_token(driver["id"], "driver")
        return {"token": token, "driver": {k: v for k, v in driver.items() if k != "password"}}
    
    # Check admin collection (legacy)
    admin = await db.admins.find_one({"email": data.email}, {"_id": 0})
    if admin and verify_password(data.password, admin["password"]):
        token = create_token(admin["id"], "admin")
        return {"token": token, "admin": {k: v for k, v in admin.items() if k != "password"}}
    
    raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user's profile"""
    user_id = current_user["user_id"]
    role = current_user["role"]
    
    if role == "user":
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if user:
            return {"user": user}
    elif role == "driver":
        driver = await db.drivers.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if driver:
            return {"driver": driver}
    elif role == "admin":
        admin = await db.users.find_one({"id": user_id, "role": "admin"}, {"_id": 0, "password": 0})
        if admin:
            return {"admin": admin}
        admin = await db.admins.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if admin:
            return {"admin": admin}
    
    raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
