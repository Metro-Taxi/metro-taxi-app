from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import secrets
import math
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from bson import ObjectId
import json
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET', 'metro-taxi-secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Subscription Plans
SUBSCRIPTION_PLANS = {
    "24h": {"name": "24 heures", "price": 6.99, "duration_hours": 24},
    "1week": {"name": "1 semaine", "price": 16.99, "duration_hours": 168},
    "1month": {"name": "1 mois", "price": 53.99, "duration_hours": 720}
}

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============================================
# MATCHING ALGORITHM HELPER FUNCTIONS
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

def calculate_direction_score(user_dest_lat: float, user_dest_lng: float, 
                               driver_dest_lat: float, driver_dest_lng: float,
                               driver_lat: float, driver_lng: float) -> float:
    """Calculate how well the user's destination aligns with the driver's direction (0-100)"""
    if not driver_dest_lat or not driver_dest_lng:
        return 50  # Default score if driver has no destination
    
    # Vector from driver to driver's destination
    driver_vector = (driver_dest_lat - driver_lat, driver_dest_lng - driver_lng)
    # Vector from driver to user's destination
    user_vector = (user_dest_lat - driver_lat, user_dest_lng - driver_lng)
    
    # Calculate dot product and magnitudes
    dot_product = driver_vector[0] * user_vector[0] + driver_vector[1] * user_vector[1]
    mag_driver = math.sqrt(driver_vector[0]**2 + driver_vector[1]**2)
    mag_user = math.sqrt(user_vector[0]**2 + user_vector[1]**2)
    
    if mag_driver == 0 or mag_user == 0:
        return 50
    
    # Cosine similarity (-1 to 1), convert to 0-100
    cos_sim = dot_product / (mag_driver * mag_user)
    return max(0, min(100, (cos_sim + 1) * 50))

def calculate_matching_score(driver: dict, user_lat: float, user_lng: float,
                              dest_lat: float, dest_lng: float) -> dict:
    """Calculate overall matching score for a driver"""
    if not driver.get('location'):
        return {"score": 0, "distance": float('inf'), "direction_score": 0, "seats_score": 0}
    
    driver_lat = driver['location']['lat']
    driver_lng = driver['location']['lng']
    
    # Distance score (closer = better, max 40 points)
    distance = calculate_distance(user_lat, user_lng, driver_lat, driver_lng)
    distance_score = max(0, 40 - (distance * 10))  # Penalize 10 points per km
    
    # Direction score (max 40 points)
    driver_dest = driver.get('destination', {})
    direction_score = calculate_direction_score(
        dest_lat, dest_lng,
        driver_dest.get('lat'), driver_dest.get('lng'),
        driver_lat, driver_lng
    ) * 0.4  # Scale to max 40 points
    
    # Seats score (more seats = better, max 20 points)
    available_seats = driver.get('available_seats', 0)
    seats_score = min(20, available_seats * 5)
    
    total_score = distance_score + direction_score + seats_score
    
    return {
        "score": round(total_score, 2),
        "distance": round(distance, 2),
        "direction_score": round(direction_score, 2),
        "seats_score": round(seats_score, 2)
    }

async def find_transfer_options(user_lat: float, user_lng: float, 
                                 dest_lat: float, dest_lng: float) -> List[dict]:
    """Find transfer (transbordement) options for optimized routing"""
    drivers = await db.drivers.find(
        {"is_active": True, "is_validated": True, "location": {"$ne": None}},
        {"_id": 0, "password": 0}
    ).to_list(100)
    
    if len(drivers) < 2:
        return []
    
    transfers = []
    direct_distance = calculate_distance(user_lat, user_lng, dest_lat, dest_lng)
    
    # Find potential transfer points (midpoint area)
    mid_lat = (user_lat + dest_lat) / 2
    mid_lng = (user_lng + dest_lng) / 2
    
    # Find first leg drivers (from user to midpoint area)
    first_leg_drivers = []
    for driver in drivers:
        if driver.get('available_seats', 0) < 1:
            continue
        driver_lat = driver['location']['lat']
        driver_lng = driver['location']['lng']
        
        # Check if driver is near user and heading towards midpoint
        dist_to_user = calculate_distance(user_lat, user_lng, driver_lat, driver_lng)
        if dist_to_user < 3:  # Within 3km
            first_leg_drivers.append(driver)
    
    # Find second leg drivers (from midpoint to destination)
    second_leg_drivers = []
    for driver in drivers:
        if driver.get('available_seats', 0) < 1:
            continue
        driver_lat = driver['location']['lat']
        driver_lng = driver['location']['lng']
        
        # Check if driver is near midpoint and heading towards destination
        dist_to_mid = calculate_distance(mid_lat, mid_lng, driver_lat, driver_lng)
        if dist_to_mid < 3:  # Within 3km
            dest = driver.get('destination', {})
            if dest:
                dest_direction = calculate_direction_score(
                    dest_lat, dest_lng,
                    dest.get('lat'), dest.get('lng'),
                    driver_lat, driver_lng
                )
                if dest_direction > 60:  # Good direction match
                    second_leg_drivers.append(driver)
    
    # Create transfer combinations
    for first_driver in first_leg_drivers[:3]:
        for second_driver in second_leg_drivers[:3]:
            if first_driver['id'] == second_driver['id']:
                continue
            
            # Calculate transfer efficiency
            first_pickup_dist = calculate_distance(
                user_lat, user_lng,
                first_driver['location']['lat'], first_driver['location']['lng']
            )
            
            transfer_point_lat = (first_driver['location']['lat'] + second_driver['location']['lat']) / 2
            transfer_point_lng = (first_driver['location']['lng'] + second_driver['location']['lng']) / 2
            
            second_dropoff_dist = calculate_distance(
                second_driver['location']['lat'], second_driver['location']['lng'],
                dest_lat, dest_lng
            )
            
            total_transfer_dist = first_pickup_dist + second_dropoff_dist
            
            # Only suggest if transfer is reasonably efficient
            if total_transfer_dist < direct_distance * 1.5:
                transfers.append({
                    "type": "transfer",
                    "first_driver": {
                        "id": first_driver['id'],
                        "name": first_driver['first_name'],
                        "vehicle": first_driver['vehicle_plate'],
                        "vehicle_type": first_driver['vehicle_type']
                    },
                    "second_driver": {
                        "id": second_driver['id'],
                        "name": second_driver['first_name'],
                        "vehicle": second_driver['vehicle_plate'],
                        "vehicle_type": second_driver['vehicle_type']
                    },
                    "transfer_point": {
                        "lat": transfer_point_lat,
                        "lng": transfer_point_lng
                    },
                    "estimated_efficiency": round((1 - total_transfer_dist / direct_distance) * 100, 1)
                })
    
    # Sort by efficiency and return top 3
    transfers.sort(key=lambda x: x['estimated_efficiency'], reverse=True)
    return transfers[:3]

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_types: Dict[str, str] = {}  # user_id -> "user" or "driver"

    async def connect(self, websocket: WebSocket, user_id: str, user_type: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_types[user_id] = user_type

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_types:
            del self.user_types[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

    async def broadcast_to_drivers(self, message: dict):
        for user_id, user_type in self.user_types.items():
            if user_type == "driver" and user_id in self.active_connections:
                await self.active_connections[user_id].send_json(message)

    async def broadcast_to_users(self, message: dict):
        for user_id, user_type in self.user_types.items():
            if user_type == "user" and user_id in self.active_connections:
                await self.active_connections[user_id].send_json(message)

manager = ConnectionManager()

# Pydantic Models
class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str

class DriverRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str
    vehicle_plate: str
    vehicle_type: str
    seats: int
    vtc_license: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    role: str
    subscription_active: bool = False
    subscription_expires: Optional[str] = None
    created_at: str

class DriverResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    vehicle_plate: str
    vehicle_type: str
    seats: int
    vtc_license: str
    is_active: bool
    is_validated: bool
    role: str
    created_at: str

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    available_seats: Optional[int] = None

class RideRequestCreate(BaseModel):
    driver_id: str
    pickup_lat: float
    pickup_lng: float
    destination_lat: float
    destination_lng: float

class RideRequestResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    user_name: str
    driver_id: str
    pickup_lat: float
    pickup_lng: float
    destination_lat: float
    destination_lng: float
    status: str
    created_at: str

class CheckoutRequest(BaseModel):
    plan_id: str
    origin_url: str

class AdminStats(BaseModel):
    total_users: int
    total_drivers: int
    active_subscriptions: int
    active_rides: int

class MatchingRequest(BaseModel):
    user_lat: float
    user_lng: float
    dest_lat: float
    dest_lng: float

class EmailVerificationRequest(BaseModel):
    token: str

class RideProgressUpdate(BaseModel):
    ride_id: str
    status: str  # "pickup", "in_progress", "near_destination", "completed"
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None

# Helper functions
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

async def get_current_user(request: Request) -> dict:
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

# Auth Routes
@api_router.post("/auth/register/user")
async def register_user(data: UserRegister, request: Request):
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
    host_url = str(request.headers.get("origin", ""))
    verification_url = f"{host_url}/verify-email?token={verification_token}"
    
    token = create_token(user_id, "user")
    return {
        "token": token, 
        "user": user_response,
        "verification_url": verification_url,
        "message": "Un email de vérification a été envoyé"
    }

@api_router.post("/auth/register/driver")
async def register_driver(data: DriverRegister, request: Request):
    existing = await db.drivers.find_one({"email": data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    driver_id = str(uuid.uuid4())
    verification_token = generate_verification_token()
    
    driver_doc = {
        "id": driver_id,
        "first_name": data.first_name,
        "last_name": data.last_name,
        "email": data.email,
        "phone": data.phone,
        "password": hash_password(data.password),
        "vehicle_plate": data.vehicle_plate,
        "vehicle_type": data.vehicle_type,
        "seats": data.seats,
        "vtc_license": data.vtc_license,
        "is_active": False,
        "is_validated": False,
        "email_verified": False,
        "verification_token": verification_token,
        "role": "driver",
        "location": None,
        "destination": None,
        "available_seats": data.seats,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Create response before inserting to avoid ObjectId contamination
    driver_response = {k: v for k, v in driver_doc.items() if k not in ["password", "verification_token"]}
    
    await db.drivers.insert_one(driver_doc)
    
    # Store verification token
    await db.email_verifications.insert_one({
        "token": verification_token,
        "user_id": driver_id,
        "user_type": "driver",
        "email": data.email,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    })
    
    host_url = str(request.headers.get("origin", ""))
    verification_url = f"{host_url}/verify-email?token={verification_token}"
    
    token = create_token(driver_id, "driver")
    return {
        "token": token, 
        "driver": driver_response,
        "verification_url": verification_url,
        "message": "Un email de vérification a été envoyé"
    }

# Email Verification Routes
@api_router.post("/auth/verify-email")
async def verify_email(data: EmailVerificationRequest):
    verification = await db.email_verifications.find_one({"token": data.token}, {"_id": 0})
    
    if not verification:
        raise HTTPException(status_code=400, detail="Token de vérification invalide")
    
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

@api_router.get("/auth/verification-status")
async def get_verification_status(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    role = current_user["role"]
    
    if role == "user":
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "email_verified": 1})
        return {"email_verified": user.get("email_verified", False) if user else False}
    elif role == "driver":
        driver = await db.drivers.find_one({"id": user_id}, {"_id": 0, "email_verified": 1})
        return {"email_verified": driver.get("email_verified", False) if driver else False}
    
    return {"email_verified": True}  # Admin always verified

@api_router.post("/auth/resend-verification")
async def resend_verification(current_user: dict = Depends(get_current_user), request: Request = None):
    user_id = current_user["user_id"]
    role = current_user["role"]
    
    if role == "user":
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        if user.get("email_verified"):
            return {"message": "Email déjà vérifié"}
        email = user["email"]
        user_type = "user"
    elif role == "driver":
        driver = await db.drivers.find_one({"id": user_id}, {"_id": 0})
        if not driver:
            raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
        if driver.get("email_verified"):
            return {"message": "Email déjà vérifié"}
        email = driver["email"]
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
    
    host_url = str(request.headers.get("origin", "")) if request else ""
    verification_url = f"{host_url}/verify-email?token={verification_token}"
    
    return {"message": "Email de vérification renvoyé", "verification_url": verification_url}

@api_router.post("/auth/login")
async def login(data: LoginRequest):
    # Check users first
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if user and verify_password(data.password, user["password"]):
        token = create_token(user["id"], "user")
        return {"token": token, "user": {k: v for k, v in user.items() if k != "password"}}
    
    # Check drivers
    driver = await db.drivers.find_one({"email": data.email}, {"_id": 0})
    if driver and verify_password(data.password, driver["password"]):
        if not driver.get("is_validated"):
            raise HTTPException(status_code=403, detail="Compte en attente de validation admin")
        token = create_token(driver["id"], "driver")
        return {"token": token, "driver": {k: v for k, v in driver.items() if k != "password"}}
    
    # Check admin
    admin = await db.admins.find_one({"email": data.email}, {"_id": 0})
    if admin and verify_password(data.password, admin["password"]):
        token = create_token(admin["id"], "admin")
        return {"token": token, "admin": {k: v for k, v in admin.items() if k != "password"}}
    
    raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
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
        admin = await db.admins.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if admin:
            return {"admin": admin}
    
    raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

# Subscription & Payment Routes
@api_router.get("/subscriptions/plans")
async def get_subscription_plans():
    return {"plans": SUBSCRIPTION_PLANS}

@api_router.post("/payments/checkout")
async def create_checkout(data: CheckoutRequest, request: Request, current_user: dict = Depends(get_current_user)):
    if data.plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Plan invalide")
    
    plan = SUBSCRIPTION_PLANS[data.plan_id]
    user_id = current_user["user_id"]
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_key = os.environ.get('STRIPE_API_KEY')
    
    stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url=webhook_url)
    
    success_url = f"{data.origin_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{data.origin_url}/subscription"
    
    checkout_request = CheckoutSessionRequest(
        amount=float(plan["price"]),
        currency="eur",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": user_id, "plan_id": data.plan_id}
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    transaction = {
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "user_id": user_id,
        "plan_id": data.plan_id,
        "amount": plan["price"],
        "currency": "eur",
        "status": "pending",
        "payment_status": "initiated",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction)
    
    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_key = os.environ.get('STRIPE_API_KEY')
    
    stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url=webhook_url)
    status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction and subscription if paid
    if status.payment_status == "paid":
        transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
        if transaction and transaction.get("payment_status") != "paid":
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"status": "completed", "payment_status": "paid"}}
            )
            
            # Activate subscription
            plan = SUBSCRIPTION_PLANS.get(transaction["plan_id"])
            if plan:
                expires_at = datetime.now(timezone.utc) + timedelta(hours=plan["duration_hours"])
                await db.users.update_one(
                    {"id": transaction["user_id"]},
                    {"$set": {
                        "subscription_active": True,
                        "subscription_expires": expires_at.isoformat(),
                        "subscription_plan": transaction["plan_id"]
                    }}
                )
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_key = os.environ.get('STRIPE_API_KEY')
    
    stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url=webhook_url)
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        if webhook_response.payment_status == "paid":
            session_id = webhook_response.session_id
            transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
            
            if transaction:
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {"status": "completed", "payment_status": "paid"}}
                )
                
                plan = SUBSCRIPTION_PLANS.get(transaction["plan_id"])
                if plan:
                    expires_at = datetime.now(timezone.utc) + timedelta(hours=plan["duration_hours"])
                    await db.users.update_one(
                        {"id": transaction["user_id"]},
                        {"$set": {
                            "subscription_active": True,
                            "subscription_expires": expires_at.isoformat(),
                            "subscription_plan": transaction["plan_id"]
                        }}
                    )
        
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return {"status": "error"}

# Driver Location Routes
@api_router.post("/drivers/location")
async def update_driver_location(data: LocationUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    update_data = {
        "location": {"lat": data.latitude, "lng": data.longitude},
        "location_updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if data.destination_lat and data.destination_lng:
        update_data["destination"] = {"lat": data.destination_lat, "lng": data.destination_lng}
    
    if data.available_seats is not None:
        update_data["available_seats"] = data.available_seats
    
    await db.drivers.update_one({"id": driver_id}, {"$set": update_data})
    
    # Broadcast to users
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0, "password": 0})
    if driver and driver.get("is_active") and driver.get("is_validated"):
        await manager.broadcast_to_users({
            "type": "driver_location_update",
            "driver": driver
        })
    
    return {"status": "ok"}

@api_router.get("/drivers/available")
async def get_available_drivers(current_user: dict = Depends(get_current_user)):
    drivers = await db.drivers.find(
        {"is_active": True, "is_validated": True, "location": {"$ne": None}},
        {"_id": 0, "password": 0}
    ).to_list(100)
    return {"drivers": drivers}

# ============================================
# MATCHING ALGORITHM ENDPOINTS
# ============================================

@api_router.post("/matching/find-drivers")
async def find_matching_drivers(data: MatchingRequest, current_user: dict = Depends(get_current_user)):
    """Find best matching drivers based on distance, direction, and availability"""
    drivers = await db.drivers.find(
        {"is_active": True, "is_validated": True, "location": {"$ne": None}, "available_seats": {"$gt": 0}},
        {"_id": 0, "password": 0}
    ).to_list(100)
    
    matched_drivers = []
    for driver in drivers:
        match_info = calculate_matching_score(
            driver, data.user_lat, data.user_lng, data.dest_lat, data.dest_lng
        )
        if match_info["score"] > 10:  # Minimum score threshold
            matched_drivers.append({
                **driver,
                "matching": match_info
            })
    
    # Sort by score descending
    matched_drivers.sort(key=lambda x: x["matching"]["score"], reverse=True)
    
    return {"drivers": matched_drivers[:10]}  # Return top 10

@api_router.post("/matching/transfers")
async def find_transfer_routes(data: MatchingRequest, current_user: dict = Depends(get_current_user)):
    """Find transfer (transbordement) options for optimized routing"""
    transfers = await find_transfer_options(
        data.user_lat, data.user_lng, data.dest_lat, data.dest_lng
    )
    
    return {"transfers": transfers, "count": len(transfers)}

@api_router.get("/matching/suggestions/{user_id}")
async def get_ride_suggestions(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get personalized ride suggestions based on user location and common destinations"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    user_location = user.get("location")
    if not user_location:
        return {"suggestions": [], "message": "Position utilisateur non disponible"}
    
    # Find available drivers
    drivers = await db.drivers.find(
        {"is_active": True, "is_validated": True, "location": {"$ne": None}, "available_seats": {"$gt": 0}},
        {"_id": 0, "password": 0}
    ).to_list(50)
    
    suggestions = []
    for driver in drivers:
        if driver.get("destination"):
            distance = calculate_distance(
                user_location["lat"], user_location["lng"],
                driver["location"]["lat"], driver["location"]["lng"]
            )
            if distance < 5:  # Within 5km
                suggestions.append({
                    "driver_id": driver["id"],
                    "driver_name": driver["first_name"],
                    "vehicle": driver["vehicle_plate"],
                    "vehicle_type": driver["vehicle_type"],
                    "destination": driver["destination"],
                    "distance_km": round(distance, 2),
                    "available_seats": driver["available_seats"]
                })
    
    suggestions.sort(key=lambda x: x["distance_km"])
    return {"suggestions": suggestions[:5]}

@api_router.post("/drivers/toggle-active")
async def toggle_driver_active(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
    
    if not driver:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    new_status = not driver.get("is_active", False)
    await db.drivers.update_one({"id": driver_id}, {"$set": {"is_active": new_status}})
    
    return {"is_active": new_status}

# Ride Request Routes
@api_router.post("/rides/request")
async def create_ride_request(data: RideRequestCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "user":
        raise HTTPException(status_code=403, detail="Accès réservé aux usagers")
    
    user_id = current_user["user_id"]
    
    # Check subscription
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user.get("subscription_active"):
        raise HTTPException(status_code=403, detail="Abonnement requis")
    
    # Check expiration
    expires_str = user.get("subscription_expires")
    if expires_str:
        expires = datetime.fromisoformat(expires_str)
        if expires < datetime.now(timezone.utc):
            await db.users.update_one({"id": user_id}, {"$set": {"subscription_active": False}})
            raise HTTPException(status_code=403, detail="Abonnement expiré")
    
    ride_id = str(uuid.uuid4())
    ride_doc = {
        "id": ride_id,
        "user_id": user_id,
        "user_name": f"{user['first_name']} {user['last_name']}",
        "driver_id": data.driver_id,
        "pickup_lat": data.pickup_lat,
        "pickup_lng": data.pickup_lng,
        "destination_lat": data.destination_lat,
        "destination_lng": data.destination_lng,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.ride_requests.insert_one(ride_doc)
    
    # Notify driver
    await manager.send_personal_message({
        "type": "ride_request",
        "ride": {k: v for k, v in ride_doc.items()}
    }, data.driver_id)
    
    return {"ride": {k: v for k, v in ride_doc.items()}}

@api_router.get("/rides/pending")
async def get_pending_rides(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    rides = await db.ride_requests.find(
        {"driver_id": driver_id, "status": "pending"},
        {"_id": 0}
    ).to_list(100)
    
    return {"rides": rides}

@api_router.post("/rides/{ride_id}/accept")
async def accept_ride(ride_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    ride = await db.ride_requests.find_one({"id": ride_id, "driver_id": driver_id}, {"_id": 0})
    
    if not ride:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    await db.ride_requests.update_one(
        {"id": ride_id},
        {"$set": {"status": "accepted", "accepted_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Reduce available seats
    await db.drivers.update_one({"id": driver_id}, {"$inc": {"available_seats": -1}})
    
    # Notify user
    await manager.send_personal_message({
        "type": "ride_accepted",
        "ride_id": ride_id
    }, ride["user_id"])
    
    return {"status": "accepted"}

@api_router.post("/rides/{ride_id}/reject")
async def reject_ride(ride_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    ride = await db.ride_requests.find_one({"id": ride_id, "driver_id": driver_id}, {"_id": 0})
    
    if not ride:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    await db.ride_requests.update_one({"id": ride_id}, {"$set": {"status": "rejected"}})
    
    # Notify user
    await manager.send_personal_message({
        "type": "ride_rejected",
        "ride_id": ride_id
    }, ride["user_id"])
    
    return {"status": "rejected"}

@api_router.post("/rides/{ride_id}/complete")
async def complete_ride(ride_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    ride = await db.ride_requests.find_one({"id": ride_id, "driver_id": driver_id}, {"_id": 0})
    
    if not ride:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    await db.ride_requests.update_one(
        {"id": ride_id},
        {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Restore available seats
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
    await db.drivers.update_one({"id": driver_id}, {"$inc": {"available_seats": 1}})
    
    # Notify user
    await manager.send_personal_message({
        "type": "ride_completed",
        "ride_id": ride_id
    }, ride["user_id"])
    
    return {"status": "completed"}

@api_router.get("/rides/active")
async def get_active_ride(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    role = current_user["role"]
    
    if role == "user":
        ride = await db.ride_requests.find_one(
            {"user_id": user_id, "status": {"$in": ["pending", "accepted", "pickup", "in_progress"]}},
            {"_id": 0}
        )
    else:
        ride = await db.ride_requests.find_one(
            {"driver_id": user_id, "status": {"$in": ["accepted", "pickup", "in_progress"]}},
            {"_id": 0}
        )
    
    return {"ride": ride}

# ============================================
# RIDE PROGRESS TRACKING
# ============================================

@api_router.post("/rides/{ride_id}/progress")
async def update_ride_progress(ride_id: str, data: RideProgressUpdate, current_user: dict = Depends(get_current_user)):
    """Update ride progress status with real-time tracking"""
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    ride = await db.ride_requests.find_one({"id": ride_id, "driver_id": driver_id}, {"_id": 0})
    
    if not ride:
        raise HTTPException(status_code=404, detail="Trajet non trouvé")
    
    valid_statuses = ["pickup", "in_progress", "near_destination", "completed"]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Statut invalide")
    
    update_data = {
        "status": data.status,
        f"{data.status}_at": datetime.now(timezone.utc).isoformat()
    }
    
    if data.current_lat and data.current_lng:
        update_data["current_location"] = {"lat": data.current_lat, "lng": data.current_lng}
    
    # Calculate progress percentage
    if data.status == "pickup":
        update_data["progress_percent"] = 10
    elif data.status == "in_progress":
        update_data["progress_percent"] = 50
    elif data.status == "near_destination":
        update_data["progress_percent"] = 90
    elif data.status == "completed":
        update_data["progress_percent"] = 100
        await db.drivers.update_one({"id": driver_id}, {"$inc": {"available_seats": 1}})
    
    await db.ride_requests.update_one({"id": ride_id}, {"$set": update_data})
    
    # Notify user in real-time
    status_messages = {
        "pickup": "Le chauffeur arrive pour vous récupérer",
        "in_progress": "Vous êtes en route vers votre destination",
        "near_destination": "Vous approchez de votre destination",
        "completed": "Vous êtes arrivé à destination"
    }
    
    await manager.send_personal_message({
        "type": "ride_progress",
        "ride_id": ride_id,
        "status": data.status,
        "message": status_messages.get(data.status, ""),
        "progress_percent": update_data.get("progress_percent", 0),
        "current_location": update_data.get("current_location")
    }, ride["user_id"])
    
    return {
        "status": data.status,
        "progress_percent": update_data.get("progress_percent", 0),
        "message": status_messages.get(data.status, "")
    }

@api_router.get("/rides/{ride_id}/tracking")
async def get_ride_tracking(ride_id: str, current_user: dict = Depends(get_current_user)):
    """Get detailed tracking information for a ride"""
    user_id = current_user["user_id"]
    role = current_user["role"]
    
    if role == "user":
        ride = await db.ride_requests.find_one({"id": ride_id, "user_id": user_id}, {"_id": 0})
    else:
        ride = await db.ride_requests.find_one({"id": ride_id, "driver_id": user_id}, {"_id": 0})
    
    if not ride:
        raise HTTPException(status_code=404, detail="Trajet non trouvé")
    
    # Get driver info for tracking
    driver = await db.drivers.find_one({"id": ride["driver_id"]}, {"_id": 0, "password": 0})
    
    tracking_info = {
        "ride": ride,
        "driver": {
            "id": driver["id"] if driver else None,
            "name": f"{driver['first_name']} {driver['last_name']}" if driver else None,
            "vehicle": driver["vehicle_plate"] if driver else None,
            "vehicle_type": driver["vehicle_type"] if driver else None,
            "current_location": driver.get("location") if driver else None
        },
        "progress": {
            "status": ride.get("status"),
            "percent": ride.get("progress_percent", 0),
            "current_location": ride.get("current_location"),
            "pickup_location": {"lat": ride["pickup_lat"], "lng": ride["pickup_lng"]},
            "destination": {"lat": ride["destination_lat"], "lng": ride["destination_lng"]}
        },
        "timeline": {
            "requested_at": ride.get("created_at"),
            "accepted_at": ride.get("accepted_at"),
            "pickup_at": ride.get("pickup_at"),
            "in_progress_at": ride.get("in_progress_at"),
            "near_destination_at": ride.get("near_destination_at"),
            "completed_at": ride.get("completed_at")
        }
    }
    
    return tracking_info

# User Location Route
@api_router.post("/users/location")
async def update_user_location(data: LocationUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "user":
        raise HTTPException(status_code=403, detail="Accès réservé aux usagers")
    
    user_id = current_user["user_id"]
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "location": {"lat": data.latitude, "lng": data.longitude},
            "location_updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"status": "ok"}

# Admin Routes
@api_router.get("/admin/stats")
async def get_admin_stats(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    total_users = await db.users.count_documents({})
    total_drivers = await db.drivers.count_documents({})
    active_subscriptions = await db.users.count_documents({"subscription_active": True})
    active_rides = await db.ride_requests.count_documents({"status": "accepted"})
    
    return {
        "total_users": total_users,
        "total_drivers": total_drivers,
        "active_subscriptions": active_subscriptions,
        "active_rides": active_rides
    }

@api_router.get("/admin/drivers")
async def get_all_drivers(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    drivers = await db.drivers.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return {"drivers": drivers}

@api_router.post("/admin/drivers/{driver_id}/validate")
async def validate_driver(driver_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    result = await db.drivers.update_one(
        {"id": driver_id},
        {"$set": {"is_validated": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    return {"status": "validated"}

@api_router.post("/admin/drivers/{driver_id}/deactivate")
async def deactivate_driver(driver_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    result = await db.drivers.update_one(
        {"id": driver_id},
        {"$set": {"is_validated": False, "is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    return {"status": "deactivated"}

@api_router.get("/admin/users")
async def get_all_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return {"users": users}

# Admin - Get all virtual cards
@api_router.get("/admin/cards")
async def get_all_virtual_cards(current_user: dict = Depends(get_current_user)):
    """Get all user virtual cards for admin view"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    users = await db.users.find({}, {"_id": 0, "password": 0, "verification_token": 0}).to_list(1000)
    
    cards = []
    for user in users:
        cards.append({
            "id": user["id"],
            "card_number": f"MT-{user['id'][:8].upper()}",
            "name": f"{user['first_name']} {user['last_name']}",
            "email": user["email"],
            "phone": user["phone"],
            "email_verified": user.get("email_verified", False),
            "subscription_active": user.get("subscription_active", False),
            "subscription_plan": user.get("subscription_plan"),
            "subscription_expires": user.get("subscription_expires"),
            "created_at": user.get("created_at")
        })
    
    return {"cards": cards, "total": len(cards)}

# Admin - Get single user card details
@api_router.get("/admin/cards/{user_id}")
async def get_admin_user_card(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get detailed virtual card for a specific user (admin view)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0, "verification_token": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Get ride history
    rides = await db.ride_requests.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)
    
    card = {
        "id": user["id"],
        "card_number": f"MT-{user['id'][:8].upper()}",
        "name": f"{user['first_name']} {user['last_name']}",
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "email": user["email"],
        "phone": user["phone"],
        "email_verified": user.get("email_verified", False),
        "subscription_active": user.get("subscription_active", False),
        "subscription_plan": user.get("subscription_plan"),
        "subscription_expires": user.get("subscription_expires"),
        "created_at": user.get("created_at"),
        "recent_rides": rides[:5],
        "total_rides": len(rides)
    }
    
    return {"card": card}

# Virtual Card Route
@api_router.get("/users/{user_id}/card")
async def get_user_card(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "user" and current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    card = {
        "id": user["id"],
        "name": f"{user['first_name']} {user['last_name']}",
        "phone": user["phone"],
        "subscription_active": user.get("subscription_active", False),
        "subscription_plan": user.get("subscription_plan"),
        "subscription_expires": user.get("subscription_expires")
    }
    
    return {"card": card}

# Create default admin
@app.on_event("startup")
async def create_default_admin():
    admin = await db.admins.find_one({"email": "admin@metrotaxi.fr"})
    if not admin:
        admin_doc = {
            "id": str(uuid.uuid4()),
            "email": "admin@metrotaxi.fr",
            "password": hash_password("admin123"),
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.admins.insert_one(admin_doc)
        logging.info("Default admin created: admin@metrotaxi.fr / admin123")

# WebSocket endpoint
@app.websocket("/ws/{user_id}/{user_type}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, user_type: str):
    await manager.connect(websocket, user_id, user_type)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(user_id)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
