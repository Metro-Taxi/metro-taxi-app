"""
Fonctions utilitaires pour l'application Métro-Taxi
"""
import math
import bcrypt
import jwt
import secrets
from datetime import datetime, timezone, timedelta

# JWT Configuration - sera initialisé depuis config
JWT_SECRET = None
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def init_jwt(secret: str):
    """Initialize JWT secret from environment"""
    global JWT_SECRET
    JWT_SECRET = secret


# ============================================
# GEO CALCULATION FUNCTIONS
# ============================================

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points in km using Haversine formula"""
    R = 6371  # Earth's radius in km
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def calculate_bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate bearing (direction angle) from point 1 to point 2 in degrees"""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lng = math.radians(lng2 - lng1)
    
    x = math.sin(delta_lng) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lng)
    
    bearing = math.atan2(x, y)
    return (math.degrees(bearing) + 360) % 360


def calculate_eta_minutes(distance_km: float, avg_speed_kmh: float = 25) -> int:
    """Calculate estimated time of arrival in minutes"""
    if distance_km <= 0:
        return 0
    return max(1, int((distance_km / avg_speed_kmh) * 60))


def is_point_in_region(lat: float, lng: float, bounds: dict) -> bool:
    """Check if a geographic point is within region bounds"""
    return (bounds['south'] <= lat <= bounds['north'] and
            bounds['west'] <= lng <= bounds['east'])


# ============================================
# AUTH HELPER FUNCTIONS
# ============================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_token(user_id: str, role: str) -> str:
    """Create a JWT token for authentication"""
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
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)


# ============================================
# DATA SANITIZATION FUNCTIONS
# ============================================

def remove_object_id(doc: dict) -> dict:
    """Remove MongoDB _id from a document"""
    if doc is None:
        return None
    return {k: v for k, v in doc.items() if k != "_id"}


def sanitize_documents(docs: list) -> list:
    """Remove _id from a list of documents"""
    return [remove_object_id(doc) for doc in docs if doc]


# ============================================
# CONFIGURATION CONSTANTS
# ============================================

# Subscription Plans (prices in cents to avoid floating point issues)
SUBSCRIPTION_PLANS = {
    "24h": {"name": "24 heures", "price": 6.99, "price_cents": 699, "duration_hours": 24},
    "1week": {"name": "1 semaine", "price": 16.99, "price_cents": 1699, "duration_hours": 168},
    "1month": {"name": "1 mois", "price": 53.99, "price_cents": 5399, "duration_hours": 720}
}

# Driver earnings rate
DRIVER_RATE_PER_KM = 1.50

# Payout configuration
PAYOUT_DAY = 10  # Day of month for automatic payouts
MIN_PAYOUT_AMOUNT = 10.0  # Minimum amount for payout

# Algorithm Constants
SEGMENT_MIN_KM = 1.5  # Minimum segment distance
SEGMENT_MAX_KM = 3.0  # Maximum segment distance
MAX_PICKUP_DISTANCE_KM = 2.0  # Maximum pickup distance
MAX_TRANSFERS = 2  # Maximum number of transfers
DIRECTION_THRESHOLD = 60  # Minimum direction score
