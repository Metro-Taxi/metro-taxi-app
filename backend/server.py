from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
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
    "1month": {"name": "1 mois", "price": 50.99, "duration_hours": 720}
}

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

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
async def register_user(data: UserRegister):
    existing = await db.users.find_one({"email": data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "first_name": data.first_name,
        "last_name": data.last_name,
        "email": data.email,
        "phone": data.phone,
        "password": hash_password(data.password),
        "role": "user",
        "subscription_active": False,
        "subscription_expires": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id, "user")
    user_response = {k: v for k, v in user_doc.items() if k != "password"}
    return {"token": token, "user": user_response}

@api_router.post("/auth/register/driver")
async def register_driver(data: DriverRegister):
    existing = await db.drivers.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    driver_id = str(uuid.uuid4())
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
        "role": "driver",
        "location": None,
        "destination": None,
        "available_seats": data.seats,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.drivers.insert_one(driver_doc)
    
    token = create_token(driver_id, "driver")
    return {"token": token, "driver": {k: v for k, v in driver_doc.items() if k != "password"}}

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
            {"user_id": user_id, "status": {"$in": ["pending", "accepted"]}},
            {"_id": 0}
        )
    else:
        ride = await db.ride_requests.find_one(
            {"driver_id": user_id, "status": "accepted"},
            {"_id": 0}
        )
    
    return {"ride": ride}

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
