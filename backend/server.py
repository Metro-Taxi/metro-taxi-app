from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import secrets
import math
import asyncio
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
from emergentintegrations.llm.openai import OpenAITextToSpeech

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
# ALGORITHME CENTRAL MÉTRO-TAXI
# ============================================
# Objectifs:
# 1. Associer usagers aux véhicules allant dans leur direction
# 2. Optimiser les trajets avec transbordements (max 2)
# 3. Réduire temps d'attente des usagers
# 4. Maximiser le taux de remplissage des véhicules
# 5. Segments optimisés entre 1.5km et 3km
# ============================================

# Constants for algorithm
SEGMENT_MIN_KM = 1.5  # Minimum segment distance
SEGMENT_MAX_KM = 3.0  # Maximum segment distance (suggest transfer after)
MAX_PICKUP_DISTANCE_KM = 2.0  # Maximum pickup distance
MAX_TRANSFERS = 2  # Maximum number of transfers allowed
DIRECTION_THRESHOLD = 60  # Minimum direction score for compatibility (0-100)

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

def calculate_eta_minutes(distance_km: float, avg_speed_kmh: float = 25) -> int:
    """Calculate estimated time of arrival in minutes"""
    if distance_km <= 0:
        return 0
    return max(1, int((distance_km / avg_speed_kmh) * 60))

def calculate_matching_score(driver: dict, user_lat: float, user_lng: float,
                              dest_lat: float, dest_lng: float) -> dict:
    """
    Calculate comprehensive matching score for a driver
    Score components:
    - Distance score (40 points max) - closer is better
    - Direction score (40 points max) - same direction is better
    - Seats score (20 points max) - more available seats is better
    """
    if not driver.get('location'):
        return {"score": 0, "distance": float('inf'), "direction_score": 0, "seats_score": 0, "eta_minutes": 0}
    
    driver_lat = driver['location']['lat']
    driver_lng = driver['location']['lng']
    
    # Distance to user (pickup distance)
    distance = calculate_distance(user_lat, user_lng, driver_lat, driver_lng)
    
    # Distance score: max 40 points, penalize 20 points per km
    distance_score = max(0, 40 - (distance * 20))
    
    # Direction score (max 40 points)
    driver_dest = driver.get('destination', {})
    direction_raw = calculate_direction_score(
        dest_lat, dest_lng,
        driver_dest.get('lat') if driver_dest else None, 
        driver_dest.get('lng') if driver_dest else None,
        driver_lat, driver_lng
    )
    direction_score = direction_raw * 0.4  # Scale to max 40 points
    
    # Seats score (more seats = better, max 20 points)
    available_seats = driver.get('available_seats', 0)
    seats_score = min(20, available_seats * 5)
    
    total_score = distance_score + direction_score + seats_score
    
    # Calculate ETA
    eta = calculate_eta_minutes(distance)
    
    # Calculate how far driver can take user towards destination
    driver_dest_lat = driver_dest.get('lat') if driver_dest else None
    driver_dest_lng = driver_dest.get('lng') if driver_dest else None
    
    segment_distance = 0
    if driver_dest_lat and driver_dest_lng:
        # Distance driver will travel towards user's destination
        segment_distance = calculate_distance(driver_lat, driver_lng, driver_dest_lat, driver_dest_lng)
    
    return {
        "score": round(total_score, 2),
        "distance_km": round(distance, 2),
        "direction_score": round(direction_raw, 2),
        "direction_score_weighted": round(direction_score, 2),
        "seats_score": round(seats_score, 2),
        "eta_minutes": eta,
        "segment_distance_km": round(segment_distance, 2),
        "needs_transfer": segment_distance > 0 and direction_raw < DIRECTION_THRESHOLD
    }

def find_optimal_transfer_point(start_lat: float, start_lng: float, 
                                 end_lat: float, end_lng: float,
                                 target_distance_km: float = SEGMENT_MAX_KM) -> dict:
    """Find optimal transfer point along the route at target distance"""
    total_distance = calculate_distance(start_lat, start_lng, end_lat, end_lng)
    
    if total_distance <= target_distance_km:
        return {"lat": end_lat, "lng": end_lng, "distance_from_start": total_distance}
    
    # Calculate fraction of journey for transfer point
    fraction = target_distance_km / total_distance
    
    # Linear interpolation for transfer point
    transfer_lat = start_lat + (end_lat - start_lat) * fraction
    transfer_lng = start_lng + (end_lng - start_lng) * fraction
    
    return {
        "lat": round(transfer_lat, 6),
        "lng": round(transfer_lng, 6),
        "distance_from_start": round(target_distance_km, 2)
    }

async def find_drivers_for_segment(start_lat: float, start_lng: float,
                                    end_lat: float, end_lng: float,
                                    exclude_driver_ids: List[str] = None) -> List[dict]:
    """Find drivers compatible with a specific segment"""
    if exclude_driver_ids is None:
        exclude_driver_ids = []
    
    query = {
        "is_active": True, 
        "is_validated": True, 
        "location": {"$ne": None},
        "available_seats": {"$gt": 0}
    }
    
    if exclude_driver_ids:
        query["id"] = {"$nin": exclude_driver_ids}
    
    drivers = await db.drivers.find(query, {"_id": 0, "password": 0}).to_list(100)
    
    compatible_drivers = []
    for driver in drivers:
        driver_lat = driver['location']['lat']
        driver_lng = driver['location']['lng']
        
        # Check pickup distance
        pickup_distance = calculate_distance(start_lat, start_lng, driver_lat, driver_lng)
        if pickup_distance > MAX_PICKUP_DISTANCE_KM:
            continue
        
        # Check direction compatibility
        dest = driver.get('destination') or {}
        direction_score = calculate_direction_score(
            end_lat, end_lng,
            dest.get('lat') if dest else None,
            dest.get('lng') if dest else None,
            driver_lat, driver_lng
        )
        
        if direction_score >= DIRECTION_THRESHOLD or not driver.get('destination'):
            compatible_drivers.append({
                **driver,
                "pickup_distance_km": round(pickup_distance, 2),
                "direction_score": round(direction_score, 2),
                "eta_minutes": calculate_eta_minutes(pickup_distance)
            })
    
    # Sort by pickup distance
    compatible_drivers.sort(key=lambda x: x['pickup_distance_km'])
    return compatible_drivers

async def calculate_multi_transfer_route(user_lat: float, user_lng: float,
                                          dest_lat: float, dest_lng: float) -> dict:
    """
    Calculate optimal route with up to 2 transfers
    Returns complete route plan with segments and transfer points
    """
    total_distance = calculate_distance(user_lat, user_lng, dest_lat, dest_lng)
    
    result = {
        "total_distance_km": round(total_distance, 2),
        "direct_route_possible": False,
        "segments": [],
        "transfer_points": [],
        "total_transfers": 0,
        "estimated_total_time_minutes": 0,
        "route_efficiency": 0
    }
    
    # Try to find direct route first
    direct_drivers = await find_drivers_for_segment(user_lat, user_lng, dest_lat, dest_lng)
    
    if direct_drivers:
        best_direct = direct_drivers[0]
        # Check if driver can cover most of the journey
        if best_direct['direction_score'] >= 70:
            result["direct_route_possible"] = True
            result["segments"] = [{
                "type": "direct",
                "start": {"lat": user_lat, "lng": user_lng},
                "end": {"lat": dest_lat, "lng": dest_lng},
                "distance_km": total_distance,
                "driver": best_direct,
                "eta_minutes": best_direct['eta_minutes'] + calculate_eta_minutes(total_distance)
            }]
            result["estimated_total_time_minutes"] = result["segments"][0]["eta_minutes"]
            result["route_efficiency"] = 100
            return result
    
    # Need transfers - calculate optimal segments
    if total_distance <= SEGMENT_MAX_KM * 2:
        # One transfer should suffice
        num_segments = 2
    else:
        # May need 2 transfers
        num_segments = min(3, max(2, int(total_distance / SEGMENT_MAX_KM) + 1))
    
    segment_distance = total_distance / num_segments
    segments = []
    transfer_points = []
    current_lat, current_lng = user_lat, user_lng
    used_driver_ids = []
    total_time = 0
    
    for i in range(num_segments):
        is_last_segment = (i == num_segments - 1)
        
        if is_last_segment:
            segment_end_lat, segment_end_lng = dest_lat, dest_lng
        else:
            # Calculate transfer point
            transfer = find_optimal_transfer_point(
                current_lat, current_lng, dest_lat, dest_lng, segment_distance
            )
            segment_end_lat = transfer['lat']
            segment_end_lng = transfer['lng']
            transfer_points.append({
                "index": i + 1,
                "location": {"lat": segment_end_lat, "lng": segment_end_lng},
                "type": "transbordement"
            })
        
        # Find driver for this segment
        segment_drivers = await find_drivers_for_segment(
            current_lat, current_lng, 
            segment_end_lat, segment_end_lng,
            used_driver_ids
        )
        
        segment_data = {
            "index": i + 1,
            "start": {"lat": round(current_lat, 6), "lng": round(current_lng, 6)},
            "end": {"lat": round(segment_end_lat, 6), "lng": round(segment_end_lng, 6)},
            "distance_km": round(calculate_distance(current_lat, current_lng, segment_end_lat, segment_end_lng), 2),
            "driver": segment_drivers[0] if segment_drivers else None,
            "alternative_drivers": segment_drivers[1:4] if len(segment_drivers) > 1 else []
        }
        
        if segment_drivers:
            used_driver_ids.append(segment_drivers[0]['id'])
            segment_data["eta_minutes"] = segment_drivers[0]['eta_minutes'] + calculate_eta_minutes(segment_data["distance_km"])
            total_time += segment_data["eta_minutes"]
        else:
            segment_data["eta_minutes"] = calculate_eta_minutes(segment_data["distance_km"]) + 5  # Add wait time
            total_time += segment_data["eta_minutes"]
        
        segments.append(segment_data)
        current_lat, current_lng = segment_end_lat, segment_end_lng
    
    result["segments"] = segments
    result["transfer_points"] = transfer_points
    result["total_transfers"] = len(transfer_points)
    result["estimated_total_time_minutes"] = total_time
    
    # Calculate efficiency (100% = optimal, lower = less efficient)
    actual_distance = sum(s["distance_km"] for s in segments)
    result["route_efficiency"] = round((total_distance / actual_distance) * 100, 1) if actual_distance > 0 else 0
    
    return result

async def find_compatible_passengers_for_driver(driver_id: str) -> List[dict]:
    """Find passengers compatible with driver's route"""
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0, "password": 0})
    if not driver or not driver.get('location') or not driver.get('destination'):
        return []
    
    driver_lat = driver['location']['lat']
    driver_lng = driver['location']['lng']
    driver_dest_lat = driver['destination']['lat']
    driver_dest_lng = driver['destination']['lng']
    
    # Get users with active subscriptions and location
    users = await db.users.find(
        {"subscription_active": True, "location": {"$ne": None}},
        {"_id": 0, "password": 0, "verification_token": 0}
    ).to_list(100)
    
    # Get pending ride requests
    pending_requests = await db.ride_requests.find(
        {"status": "pending"},
        {"_id": 0}
    ).to_list(100)
    
    pending_user_ids = {r["user_id"]: r for r in pending_requests}
    
    compatible_passengers = []
    for user in users:
        user_lat = user['location']['lat']
        user_lng = user['location']['lng']
        
        # Check if user is close enough for pickup
        pickup_distance = calculate_distance(driver_lat, driver_lng, user_lat, user_lng)
        if pickup_distance > MAX_PICKUP_DISTANCE_KM:
            continue
        
        # Check if user has a pending request with destination
        pending = pending_user_ids.get(user['id'])
        if pending:
            user_dest_lat = pending['destination_lat']
            user_dest_lng = pending['destination_lng']
            
            # Check direction compatibility
            direction_score = calculate_direction_score(
                user_dest_lat, user_dest_lng,
                driver_dest_lat, driver_dest_lng,
                driver_lat, driver_lng
            )
            
            if direction_score >= DIRECTION_THRESHOLD:
                compatible_passengers.append({
                    "user_id": user['id'],
                    "name": f"{user['first_name']} {user['last_name']}",
                    "location": user['location'],
                    "destination": {"lat": user_dest_lat, "lng": user_dest_lng},
                    "pickup_distance_km": round(pickup_distance, 2),
                    "direction_score": round(direction_score, 2),
                    "eta_minutes": calculate_eta_minutes(pickup_distance),
                    "has_pending_request": True,
                    "request_id": pending['id']
                })
    
    # Sort by direction score then pickup distance
    compatible_passengers.sort(key=lambda x: (-x['direction_score'], x['pickup_distance_km']))
    return compatible_passengers

async def find_transfer_options(user_lat: float, user_lng: float, 
                                 dest_lat: float, dest_lng: float) -> List[dict]:
    """Find single transfer options (legacy compatibility + enhanced)"""
    drivers = await db.drivers.find(
        {"is_active": True, "is_validated": True, "location": {"$ne": None}, "available_seats": {"$gt": 0}},
        {"_id": 0, "password": 0}
    ).to_list(100)
    
    if len(drivers) < 2:
        return []
    
    transfers = []
    direct_distance = calculate_distance(user_lat, user_lng, dest_lat, dest_lng)
    
    # Find optimal transfer point
    transfer_point = find_optimal_transfer_point(user_lat, user_lng, dest_lat, dest_lng)
    
    # Find first leg drivers (pickup to transfer)
    first_leg_drivers = await find_drivers_for_segment(
        user_lat, user_lng, transfer_point['lat'], transfer_point['lng']
    )
    
    # Find second leg drivers (transfer to destination)
    second_leg_drivers = await find_drivers_for_segment(
        transfer_point['lat'], transfer_point['lng'], dest_lat, dest_lng
    )
    
    # Create transfer combinations
    for first_driver in first_leg_drivers[:5]:
        for second_driver in second_leg_drivers[:5]:
            if first_driver['id'] == second_driver['id']:
                continue
            
            first_segment_dist = calculate_distance(
                user_lat, user_lng, transfer_point['lat'], transfer_point['lng']
            )
            second_segment_dist = calculate_distance(
                transfer_point['lat'], transfer_point['lng'], dest_lat, dest_lng
            )
            
            total_time = (
                first_driver['eta_minutes'] + 
                calculate_eta_minutes(first_segment_dist) +
                3 +  # Transfer wait time
                calculate_eta_minutes(second_segment_dist)
            )
            
            efficiency = round((direct_distance / (first_segment_dist + second_segment_dist)) * 100, 1)
            
            transfers.append({
                "type": "single_transfer",
                "first_driver": {
                    "id": first_driver['id'],
                    "name": first_driver['first_name'],
                    "vehicle": first_driver['vehicle_plate'],
                    "vehicle_type": first_driver['vehicle_type'],
                    "pickup_eta_minutes": first_driver['eta_minutes'],
                    "direction_score": first_driver['direction_score']
                },
                "second_driver": {
                    "id": second_driver['id'],
                    "name": second_driver['first_name'],
                    "vehicle": second_driver['vehicle_plate'],
                    "vehicle_type": second_driver['vehicle_type'],
                    "direction_score": second_driver['direction_score']
                },
                "transfer_point": transfer_point,
                "first_segment_km": round(first_segment_dist, 2),
                "second_segment_km": round(second_segment_dist, 2),
                "total_time_minutes": total_time,
                "efficiency_percent": efficiency
            })
    
    # Sort by efficiency
    transfers.sort(key=lambda x: x['efficiency_percent'], reverse=True)
    return transfers[:5]

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

@api_router.post("/matching/optimal-route")
async def get_optimal_route(data: MatchingRequest, current_user: dict = Depends(get_current_user)):
    """
    Calculate optimal route with automatic transfer optimization
    Returns complete route plan with segments (1.5-3km) and up to 2 transfers
    """
    route = await calculate_multi_transfer_route(
        data.user_lat, data.user_lng, data.dest_lat, data.dest_lng
    )
    
    return {
        "route": route,
        "algorithm_config": {
            "segment_min_km": SEGMENT_MIN_KM,
            "segment_max_km": SEGMENT_MAX_KM,
            "max_transfers": MAX_TRANSFERS,
            "direction_threshold": DIRECTION_THRESHOLD
        }
    }

@api_router.get("/matching/driver-passengers/{driver_id}")
async def get_driver_compatible_passengers(driver_id: str, current_user: dict = Depends(get_current_user)):
    """Get passengers compatible with driver's route direction"""
    if current_user["role"] != "driver" and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    passengers = await find_compatible_passengers_for_driver(driver_id)
    
    return {
        "passengers": passengers,
        "count": len(passengers),
        "auto_match_enabled": True
    }

@api_router.get("/matching/network-status")
async def get_network_status(current_user: dict = Depends(get_current_user)):
    """Get real-time network status - available vehicles, coverage, etc."""
    active_drivers = await db.drivers.find(
        {"is_active": True, "is_validated": True, "location": {"$ne": None}},
        {"_id": 0, "password": 0}
    ).to_list(1000)
    
    total_seats = sum(d.get('available_seats', 0) for d in active_drivers)
    
    # Calculate network coverage (approximate bounding box)
    if active_drivers:
        lats = [d['location']['lat'] for d in active_drivers]
        lngs = [d['location']['lng'] for d in active_drivers]
        coverage_area = {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lng": min(lngs),
            "max_lng": max(lngs)
        }
    else:
        coverage_area = None
    
    # Active rides
    active_rides = await db.ride_requests.count_documents(
        {"status": {"$in": ["accepted", "pickup", "in_progress"]}}
    )
    
    # Pending requests
    pending_requests = await db.ride_requests.count_documents({"status": "pending"})
    
    return {
        "network_status": "active" if active_drivers else "limited",
        "active_vehicles": len(active_drivers),
        "total_available_seats": total_seats,
        "active_rides": active_rides,
        "pending_requests": pending_requests,
        "coverage_area": coverage_area,
        "vehicles": [{
            "id": d["id"],
            "location": d["location"],
            "destination": d.get("destination"),
            "vehicle_type": d["vehicle_type"],
            "available_seats": d.get("available_seats", 0),
            "direction_bearing": calculate_bearing(
                d["location"]["lat"], d["location"]["lng"],
                d["destination"]["lat"], d["destination"]["lng"]
            ) if d.get("destination") else None
        } for d in active_drivers]
    }

@api_router.get("/matching/suggestions/{user_id}")
async def get_ride_suggestions(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get personalized ride suggestions based on user location and nearby drivers"""
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
            if distance < MAX_PICKUP_DISTANCE_KM:
                suggestions.append({
                    "driver_id": driver["id"],
                    "driver_name": driver["first_name"],
                    "vehicle": driver["vehicle_plate"],
                    "vehicle_type": driver["vehicle_type"],
                    "destination": driver["destination"],
                    "distance_km": round(distance, 2),
                    "available_seats": driver["available_seats"],
                    "eta_minutes": calculate_eta_minutes(distance),
                    "direction_bearing": calculate_bearing(
                        driver["location"]["lat"], driver["location"]["lng"],
                        driver["destination"]["lat"], driver["destination"]["lng"]
                    )
                })
    
    suggestions.sort(key=lambda x: x["distance_km"])
    return {"suggestions": suggestions[:10]}

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

# Admin - Get subscription statistics
@api_router.get("/admin/subscriptions")
async def get_subscription_stats(current_user: dict = Depends(get_current_user)):
    """Get detailed subscription statistics for admin"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    now = datetime.now(timezone.utc)
    
    # Get all users with subscription info
    users = await db.users.find({}, {"_id": 0, "password": 0, "verification_token": 0}).to_list(1000)
    
    active_subscriptions = []
    expired_subscriptions = []
    expiring_soon = []  # Within 24 hours
    
    for user in users:
        sub_info = {
            "id": user["id"],
            "name": f"{user['first_name']} {user['last_name']}",
            "email": user["email"],
            "plan": user.get("subscription_plan"),
            "expires": user.get("subscription_expires"),
            "active": user.get("subscription_active", False)
        }
        
        if user.get("subscription_active"):
            expires_str = user.get("subscription_expires")
            if expires_str:
                try:
                    expires = datetime.fromisoformat(expires_str)
                    if expires < now:
                        expired_subscriptions.append(sub_info)
                    elif expires < now + timedelta(hours=24):
                        expiring_soon.append(sub_info)
                        active_subscriptions.append(sub_info)
                    else:
                        active_subscriptions.append(sub_info)
                except (ValueError, TypeError):
                    active_subscriptions.append(sub_info)
            else:
                active_subscriptions.append(sub_info)
        elif user.get("subscription_expires"):
            expired_subscriptions.append(sub_info)
    
    return {
        "summary": {
            "total_active": len(active_subscriptions),
            "total_expired": len(expired_subscriptions),
            "expiring_soon_24h": len(expiring_soon)
        },
        "active_subscriptions": active_subscriptions,
        "expired_subscriptions": expired_subscriptions,
        "expiring_soon": expiring_soon
    }

# Admin - Manually deactivate expired subscriptions
@api_router.post("/admin/subscriptions/cleanup")
async def cleanup_expired_subscriptions(current_user: dict = Depends(get_current_user)):
    """Manually trigger cleanup of all expired subscriptions"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    now = datetime.now(timezone.utc)
    
    # Find and deactivate all expired subscriptions
    expired_users = await db.users.find({
        "subscription_active": True,
        "subscription_expires": {"$ne": None}
    }, {"_id": 0, "id": 1, "subscription_expires": 1, "email": 1}).to_list(1000)
    
    deactivated = []
    for user in expired_users:
        expires_str = user.get("subscription_expires")
        if expires_str:
            try:
                expires = datetime.fromisoformat(expires_str)
                if expires < now:
                    await db.users.update_one(
                        {"id": user["id"]},
                        {"$set": {"subscription_active": False}}
                    )
                    deactivated.append(user.get("email", user["id"]))
            except (ValueError, TypeError):
                pass
    
    return {
        "message": f"{len(deactivated)} abonnement(s) expiré(s) désactivé(s)",
        "deactivated_users": deactivated
    }

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

# ============================================
# TEXT-TO-SPEECH API FOR VIDEO VOICEOVER
# ============================================

# Video voiceover scripts for each language
VIDEO_SCRIPTS = {
    "fr": """Métro-Taxi, le système de déplacement intelligent par covoiturage.
Bienvenue sur Métro-Taxi, le réseau de mobilité urbaine par abonnement.
En choisissant le covoiturage intelligent, vous contribuez à la protection de l'environnement en réduisant votre empreinte carbone.
Inscrivez-vous et choisissez votre forfait. Localisez les véhicules allant dans votre direction.
Demandez à monter d'un simple clic. Le chauffeur vous récupère et vous dépose où vous voulez.
Grâce à notre système de transbordement intelligent, changez de véhicule en route pour atteindre votre destination.
Métro-Taxi, vos trajets sans limites, pour un avenir plus vert.""",

    "en": """Métro-Taxi, the intelligent ridesharing transportation system.
Welcome to Métro-Taxi, the subscription-based urban mobility network.
By choosing intelligent ridesharing, you contribute to environmental protection by reducing your carbon footprint.
Sign up and choose your plan. Locate vehicles heading in your direction.
Request a ride with a single click. The driver picks you up and drops you off wherever you want.
Thanks to our intelligent transfer system, switch vehicles along the way to reach your destination.
Métro-Taxi, your rides without limits, for a greener future.""",

    "es": """Métro-Taxi, el sistema de transporte inteligente por coche compartido.
Bienvenido a Métro-Taxi, la red de movilidad urbana por suscripción.
Al elegir el coche compartido inteligente, contribuyes a la protección del medio ambiente reduciendo tu huella de carbono.
Regístrate y elige tu plan. Localiza vehículos que van en tu dirección.
Solicita un viaje con un solo clic. El conductor te recoge y te deja donde quieras.
Gracias a nuestro sistema inteligente de transbordo, cambia de vehículo en ruta para llegar a tu destino.
Métro-Taxi, tus viajes sin límites, para un futuro más verde.""",

    "pt": """Métro-Taxi, o sistema de transporte inteligente por boleias partilhadas.
Bem-vindo ao Métro-Taxi, a rede de mobilidade urbana por assinatura.
Ao escolher boleias partilhadas inteligentes, contribui para a proteção do ambiente reduzindo a sua pegada de carbono.
Registe-se e escolha o seu plano. Localize veículos que vão na sua direção.
Peça uma viagem com um clique. O motorista apanha-o e deixa-o onde quiser.
Graças ao nosso sistema inteligente de transbordo, mude de veículo no caminho para chegar ao seu destino.
Métro-Taxi, as suas viagens sem limites, para um futuro mais verde.""",

    "no": """Métro-Taxi, det intelligente samkjøringssystemet.
Velkommen til Métro-Taxi, det abonnementsbaserte bymobilitetsnettverket.
Ved å velge intelligent samkjøring bidrar du til miljøvern ved å redusere ditt karbonavtrykk.
Registrer deg og velg din plan. Finn kjøretøy som går i din retning.
Be om en tur med ett klikk. Sjåføren henter deg og setter deg av hvor du vil.
Takket være vårt intelligente overgangssystem kan du bytte kjøretøy underveis for å nå målet ditt.
Métro-Taxi, dine turer uten grenser, for en grønnere fremtid.""",

    "sv": """Métro-Taxi, det intelligenta samåkningssystemet.
Välkommen till Métro-Taxi, det prenumerationsbaserade stadsmobilitetsnätverket.
Genom att välja intelligent samåkning bidrar du till miljöskydd genom att minska ditt koldioxidavtryck.
Registrera dig och välj din plan. Hitta fordon som åker i din riktning.
Begär en resa med ett klick. Föraren hämtar dig och släpper av dig var du vill.
Tack vare vårt intelligenta övergångssystem kan du byta fordon på vägen för att nå ditt mål.
Métro-Taxi, dina resor utan gränser, för en grönare framtid.""",

    "da": """Métro-Taxi, det intelligente samkørselssystem.
Velkommen til Métro-Taxi, det abonnementsbaserede bymobilitetsnetværk.
Ved at vælge intelligent samkørsel bidrager du til miljøbeskyttelse ved at reducere dit CO2-aftryk.
Tilmeld dig og vælg din plan. Find køretøjer, der kører i din retning.
Anmod om en tur med ét klik. Chaufføren henter dig og sætter dig af, hvor du vil.
Takket være vores intelligente overgangssystem kan du skifte køretøj undervejs for at nå dit mål.
Métro-Taxi, dine ture uden grænser, for en grønnere fremtid.""",

    "zh": """Métro-Taxi，智能拼车出行系统。
欢迎来到Métro-Taxi，订阅式城市交通网络。
选择智能拼车，您将通过减少碳足迹为环境保护做出贡献。
注册并选择您的计划。找到前往您方向的车辆。
一键请求乘车。司机会接您并送您到想去的地方。
借助我们的智能换乘系统，您可以在途中换乘车辆以到达目的地。
Métro-Taxi，无限出行，共创绿色未来。""",

    "ur": """میٹرو ٹیکسی، ذہین رائیڈ شیئرنگ ٹرانسپورٹ سسٹم۔
میٹرو ٹیکسی میں خوش آمدید، سبسکرپشن پر مبنی شہری نقل و حمل کا نیٹ ورک۔
ذہین رائیڈ شیئرنگ کا انتخاب کرکے، آپ اپنے کاربن فوٹ پرنٹ کو کم کرکے ماحولیاتی تحفظ میں حصہ ڈالتے ہیں۔
رجسٹر کریں اور اپنا پلان منتخب کریں۔ اپنی سمت جانے والی گاڑیاں تلاش کریں۔
ایک کلک سے سفر کی درخواست کریں۔ ڈرائیور آپ کو لے کر جہاں چاہیں چھوڑ دے گا۔
ہمارے ذہین ٹرانسفر سسٹم کی بدولت، اپنی منزل تک پہنچنے کے لیے راستے میں گاڑی بدلیں۔
میٹرو ٹیکسی، بے حد سفر، سبز مستقبل کے لیے۔"""
}

class TTSRequest(BaseModel):
    language: str = Field(..., description="Language code (fr, en, es, pt, no, sv, da, zh, ur)")
    voice: str = Field(default="nova", description="Voice to use")

@api_router.post("/tts/voiceover")
async def generate_voiceover(request: TTSRequest):
    """Generate voiceover audio for the promotional video in the specified language"""
    if request.language not in VIDEO_SCRIPTS:
        raise HTTPException(status_code=400, detail=f"Language '{request.language}' not supported")
    
    script = VIDEO_SCRIPTS[request.language]
    
    try:
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="TTS API key not configured")
        
        tts = OpenAITextToSpeech(api_key=api_key)
        
        # Generate speech
        audio_bytes = await tts.generate_speech(
            text=script,
            model="tts-1",
            voice=request.voice,
            speed=1.0,
            response_format="mp3"
        )
        
        # Return audio as response
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=voiceover_{request.language}.mp3"
            }
        )
        
    except Exception as e:
        logging.error(f"TTS generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating voiceover: {str(e)}")

@api_router.get("/tts/languages")
async def get_available_languages():
    """Get list of available languages for voiceover"""
    return {
        "languages": [
            {"code": "fr", "name": "Français", "flag": "🇫🇷"},
            {"code": "en", "name": "English", "flag": "🇬🇧"},
            {"code": "es", "name": "Español", "flag": "🇪🇸"},
            {"code": "pt", "name": "Português", "flag": "🇵🇹"},
            {"code": "no", "name": "Norsk", "flag": "🇳🇴"},
            {"code": "sv", "name": "Svenska", "flag": "🇸🇪"},
            {"code": "da", "name": "Dansk", "flag": "🇩🇰"},
            {"code": "zh", "name": "中文", "flag": "🇨🇳"},
            {"code": "ur", "name": "اردو", "flag": "🇵🇰"}
        ]
    }

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

# ============================================
# AUTOMATIC SUBSCRIPTION EXPIRATION CHECK
# ============================================
async def check_expired_subscriptions():
    """Background task to automatically deactivate expired subscriptions"""
    while True:
        try:
            now = datetime.now(timezone.utc)
            
            # Find all users with active subscriptions that have expired
            expired_users = await db.users.find({
                "subscription_active": True,
                "subscription_expires": {"$ne": None}
            }, {"_id": 0, "id": 1, "subscription_expires": 1, "email": 1}).to_list(1000)
            
            deactivated_count = 0
            for user in expired_users:
                expires_str = user.get("subscription_expires")
                if expires_str:
                    try:
                        expires = datetime.fromisoformat(expires_str)
                        if expires < now:
                            await db.users.update_one(
                                {"id": user["id"]},
                                {"$set": {"subscription_active": False}}
                            )
                            deactivated_count += 1
                            logging.info(f"Subscription expired and deactivated for user: {user.get('email', user['id'])}")
                    except (ValueError, TypeError) as e:
                        logging.error(f"Error parsing expiration date for user {user['id']}: {e}")
            
            if deactivated_count > 0:
                logging.info(f"Deactivated {deactivated_count} expired subscription(s)")
            
        except Exception as e:
            logging.error(f"Error checking expired subscriptions: {e}")
        
        # Check every 5 minutes
        await asyncio.sleep(300)

@app.on_event("startup")
async def start_subscription_checker():
    """Start the background subscription expiration checker"""
    asyncio.create_task(check_expired_subscriptions())
    logging.info("Subscription expiration checker started (runs every 5 minutes)")

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
