"""
Dépendances d'authentification pour les routes FastAPI
"""
import jwt
from fastapi import Request, HTTPException

# Configuration JWT - sera initialisée depuis server.py
JWT_SECRET = None
JWT_ALGORITHM = "HS256"


def init_auth(secret: str, algorithm: str = "HS256"):
    """Initialize auth configuration"""
    global JWT_SECRET, JWT_ALGORITHM
    JWT_SECRET = secret
    JWT_ALGORITHM = algorithm


async def get_current_user(request: Request) -> dict:
    """Extract and validate JWT token from request headers"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Non autorisé")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")


def require_admin(current_user: dict):
    """Check if user has admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
