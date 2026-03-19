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
import resend
import stripe
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
from emergentintegrations.llm.openai import OpenAITextToSpeech

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Stripe configuration
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY

JWT_SECRET = os.environ.get('JWT_SECRET', 'metro-taxi-secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Resend configuration
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Subscription Plans
SUBSCRIPTION_PLANS = {
    "24h": {"name": "24 heures", "price": 6.99, "duration_hours": 24},
    "1week": {"name": "1 semaine", "price": 16.99, "duration_hours": 168},
    "1month": {"name": "1 mois", "price": 53.99, "duration_hours": 720}
}

# Driver Revenue Configuration
DRIVER_RATE_PER_KM = 1.50  # €1.50 per kilometer
PAYOUT_DAY = 10  # Day of month for automatic payouts

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
    iban: Optional[str] = None
    bic: Optional[str] = None

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
    iban: Optional[str] = None
    bic: Optional[str] = None

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

# ============================================
# PUSH NOTIFICATIONS MODELS
# ============================================
class PushSubscription(BaseModel):
    endpoint: str
    keys: Dict[str, str]
    user_id: Optional[str] = None
    user_type: str = "user"  # "user" or "driver"

class NotificationPayload(BaseModel):
    title: str
    body: str
    icon: Optional[str] = "/icons/icon-192x192.png"
    badge: Optional[str] = "/icons/icon-72x72.png"
    data: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, str]]] = None

# ============================================
# RIDE HISTORY MODELS
# ============================================
class RideHistoryFilter(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    page: int = 1
    limit: int = 20

# ============================================
# RATING SYSTEM MODELS
# ============================================
class RatingCreate(BaseModel):
    ride_id: str
    driver_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class RatingResponse(BaseModel):
    id: str
    ride_id: str
    user_id: str
    driver_id: str
    rating: int
    comment: Optional[str]
    created_at: str

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

async def send_verification_email(email: str, name: str, verification_url: str, lang: str = "fr"):
    """Send verification email using Resend"""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, skipping email")
        return False
    
    # Email templates per language
    templates = {
        "fr": {
            "subject": "Vérifiez votre email - Métro-Taxi",
            "title": "Bienvenue sur Métro-Taxi !",
            "greeting": f"Bonjour {name},",
            "message": "Merci de vous être inscrit sur Métro-Taxi. Pour activer votre compte, veuillez cliquer sur le bouton ci-dessous :",
            "button": "Vérifier mon email",
            "footer": "Ce lien expire dans 24 heures.",
            "ignore": "Si vous n'avez pas créé de compte, vous pouvez ignorer cet email."
        },
        "en": {
            "subject": "Verify your email - Métro-Taxi",
            "title": "Welcome to Métro-Taxi!",
            "greeting": f"Hello {name},",
            "message": "Thank you for signing up for Métro-Taxi. To activate your account, please click the button below:",
            "button": "Verify my email",
            "footer": "This link expires in 24 hours.",
            "ignore": "If you didn't create an account, you can ignore this email."
        },
        "es": {
            "subject": "Verifica tu email - Métro-Taxi",
            "title": "¡Bienvenido a Métro-Taxi!",
            "greeting": f"Hola {name},",
            "message": "Gracias por registrarte en Métro-Taxi. Para activar tu cuenta, haz clic en el botón de abajo:",
            "button": "Verificar mi email",
            "footer": "Este enlace expira en 24 horas.",
            "ignore": "Si no creaste una cuenta, puedes ignorar este email."
        },
        "de": {
            "subject": "Bestätigen Sie Ihre E-Mail - Métro-Taxi",
            "title": "Willkommen bei Métro-Taxi!",
            "greeting": f"Hallo {name},",
            "message": "Vielen Dank für Ihre Anmeldung bei Métro-Taxi. Um Ihr Konto zu aktivieren, klicken Sie bitte auf die Schaltfläche unten:",
            "button": "E-Mail bestätigen",
            "footer": "Dieser Link läuft in 24 Stunden ab.",
            "ignore": "Wenn Sie kein Konto erstellt haben, können Sie diese E-Mail ignorieren."
        },
        "pt": {
            "subject": "Verifique seu email - Métro-Taxi",
            "title": "Bem-vindo ao Métro-Taxi!",
            "greeting": f"Olá {name},",
            "message": "Obrigado por se registrar no Métro-Taxi. Para ativar sua conta, clique no botão abaixo:",
            "button": "Verificar meu email",
            "footer": "Este link expira em 24 horas.",
            "ignore": "Se você não criou uma conta, pode ignorar este email."
        }
    }
    
    # Get template for language (default to French)
    t = templates.get(lang[:2], templates["fr"])
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #0a0a0a;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 40px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #18181b; border-radius: 8px; overflow: hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="background-color: #FFD60A; padding: 30px; text-align: center;">
                                <h1 style="margin: 0; color: #000; font-size: 28px; font-weight: bold;">MÉTRO-TAXI</h1>
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <h2 style="color: #ffffff; margin: 0 0 20px 0; font-size: 24px;">{t['title']}</h2>
                                <p style="color: #a1a1aa; margin: 0 0 10px 0; font-size: 16px;">{t['greeting']}</p>
                                <p style="color: #a1a1aa; margin: 0 0 30px 0; font-size: 16px;">{t['message']}</p>
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center">
                                            <a href="{verification_url}" style="display: inline-block; background-color: #FFD60A; color: #000; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-weight: bold; font-size: 16px;">{t['button']}</a>
                                        </td>
                                    </tr>
                                </table>
                                <p style="color: #71717a; margin: 30px 0 0 0; font-size: 14px;">{t['footer']}</p>
                                <p style="color: #52525b; margin: 20px 0 0 0; font-size: 12px;">{t['ignore']}</p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #09090b; padding: 20px 30px; text-align: center;">
                                <p style="color: #52525b; margin: 0; font-size: 12px;">© 2026 Métro-Taxi. Système de déplacement intelligent par covoiturage.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": t['subject'],
            "html": html_content
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Verification email sent to {email}, ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send verification email to {email}: {str(e)}")
        return False

async def send_subscription_confirmation_email(email: str, name: str, plan_name: str, expires_at: str, lang: str = "fr"):
    """Send subscription confirmation email using Resend"""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, skipping email")
        return False
    
    templates = {
        "fr": {
            "subject": "Abonnement activé - Métro-Taxi",
            "title": "Votre abonnement est actif !",
            "greeting": f"Bonjour {name},",
            "message": f"Votre abonnement <strong>{plan_name}</strong> a été activé avec succès.",
            "valid_until": f"Valide jusqu'au : <strong>{expires_at}</strong>",
            "cta": "Accéder à mon compte",
            "enjoy": "Profitez de trajets illimités sur tout le réseau Métro-Taxi !"
        },
        "en": {
            "subject": "Subscription activated - Métro-Taxi",
            "title": "Your subscription is active!",
            "greeting": f"Hello {name},",
            "message": f"Your <strong>{plan_name}</strong> subscription has been successfully activated.",
            "valid_until": f"Valid until: <strong>{expires_at}</strong>",
            "cta": "Access my account",
            "enjoy": "Enjoy unlimited rides across the entire Métro-Taxi network!"
        }
    }
    
    t = templates.get(lang[:2], templates["fr"])
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #0a0a0a;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 40px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #18181b; border-radius: 8px;">
                        <tr>
                            <td style="background-color: #22c55e; padding: 30px; text-align: center;">
                                <h1 style="margin: 0; color: #fff; font-size: 28px;">✓ {t['title']}</h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px 30px;">
                                <p style="color: #a1a1aa; margin: 0 0 10px 0; font-size: 16px;">{t['greeting']}</p>
                                <p style="color: #ffffff; margin: 0 0 20px 0; font-size: 18px;">{t['message']}</p>
                                <p style="color: #FFD60A; margin: 0 0 30px 0; font-size: 16px;">{t['valid_until']}</p>
                                <p style="color: #a1a1aa; margin: 0; font-size: 14px;">{t['enjoy']}</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background-color: #09090b; padding: 20px; text-align: center;">
                                <p style="color: #52525b; margin: 0; font-size: 12px;">© 2026 Métro-Taxi</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": t['subject'],
            "html": html_content
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Subscription email sent to {email}, ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send subscription email to {email}: {str(e)}")
        return False

async def send_payout_notification_email(email: str, name: str, amount: float, total_km: float, rides_count: int, months: list, payout_date: str, lang: str = "fr"):
    """Send payout notification email to driver when payment is processed"""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, skipping payout email")
        return False
    
    months_str = ", ".join(months) if months else "N/A"
    
    templates = {
        "fr": {
            "subject": f"Virement effectué - €{amount:.2f} - Métro-Taxi",
            "title": "Virement effectué !",
            "greeting": f"Bonjour {name},",
            "message": f"Votre virement mensuel a été traité avec succès.",
            "amount_label": "Montant viré",
            "amount": f"€{amount:.2f}",
            "details_title": "Détails du virement",
            "km_label": "Kilomètres parcourus",
            "km_value": f"{total_km:.1f} km",
            "rides_label": "Nombre de trajets",
            "rides_value": f"{rides_count}",
            "period_label": "Période",
            "period_value": months_str,
            "date_label": "Date du virement",
            "date_value": payout_date,
            "note": "Le virement sera crédité sur votre compte bancaire sous 2-3 jours ouvrés.",
            "thanks": "Merci pour votre engagement avec Métro-Taxi !"
        },
        "en": {
            "subject": f"Payout processed - €{amount:.2f} - Métro-Taxi",
            "title": "Payout processed!",
            "greeting": f"Hello {name},",
            "message": f"Your monthly payout has been successfully processed.",
            "amount_label": "Amount transferred",
            "amount": f"€{amount:.2f}",
            "details_title": "Payout details",
            "km_label": "Kilometers driven",
            "km_value": f"{total_km:.1f} km",
            "rides_label": "Number of rides",
            "rides_value": f"{rides_count}",
            "period_label": "Period",
            "period_value": months_str,
            "date_label": "Payout date",
            "date_value": payout_date,
            "note": "The transfer will be credited to your bank account within 2-3 business days.",
            "thanks": "Thank you for your commitment with Métro-Taxi!"
        }
    }
    
    t = templates.get(lang[:2], templates["fr"])
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #0a0a0a;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 40px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #18181b; border-radius: 8px;">
                        <tr>
                            <td style="background-color: #FFD60A; padding: 30px; text-align: center;">
                                <h1 style="margin: 0; color: #000; font-size: 28px;">💰 {t['title']}</h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px 30px;">
                                <p style="color: #a1a1aa; margin: 0 0 10px 0; font-size: 16px;">{t['greeting']}</p>
                                <p style="color: #ffffff; margin: 0 0 30px 0; font-size: 18px;">{t['message']}</p>
                                
                                <!-- Amount Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #22c55e; border-radius: 8px; margin-bottom: 30px;">
                                    <tr>
                                        <td style="padding: 25px; text-align: center;">
                                            <p style="color: rgba(255,255,255,0.8); margin: 0 0 5px 0; font-size: 14px;">{t['amount_label']}</p>
                                            <p style="color: #fff; margin: 0; font-size: 36px; font-weight: bold;">{t['amount']}</p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Details -->
                                <p style="color: #FFD60A; margin: 0 0 15px 0; font-size: 16px; font-weight: bold;">{t['details_title']}</p>
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 25px;">
                                    <tr>
                                        <td style="padding: 10px 0; border-bottom: 1px solid #27272a;">
                                            <span style="color: #71717a; font-size: 14px;">{t['km_label']}</span>
                                        </td>
                                        <td style="padding: 10px 0; border-bottom: 1px solid #27272a; text-align: right;">
                                            <span style="color: #fff; font-size: 14px; font-weight: bold;">{t['km_value']}</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0; border-bottom: 1px solid #27272a;">
                                            <span style="color: #71717a; font-size: 14px;">{t['rides_label']}</span>
                                        </td>
                                        <td style="padding: 10px 0; border-bottom: 1px solid #27272a; text-align: right;">
                                            <span style="color: #fff; font-size: 14px; font-weight: bold;">{t['rides_value']}</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0; border-bottom: 1px solid #27272a;">
                                            <span style="color: #71717a; font-size: 14px;">{t['period_label']}</span>
                                        </td>
                                        <td style="padding: 10px 0; border-bottom: 1px solid #27272a; text-align: right;">
                                            <span style="color: #fff; font-size: 14px;">{t['period_value']}</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0;">
                                            <span style="color: #71717a; font-size: 14px;">{t['date_label']}</span>
                                        </td>
                                        <td style="padding: 10px 0; text-align: right;">
                                            <span style="color: #fff; font-size: 14px;">{t['date_value']}</span>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="color: #a1a1aa; margin: 0 0 20px 0; font-size: 13px; padding: 15px; background-color: #27272a; border-radius: 6px;">
                                    ℹ️ {t['note']}
                                </p>
                                
                                <p style="color: #FFD60A; margin: 0; font-size: 14px; text-align: center;">{t['thanks']}</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background-color: #09090b; padding: 20px; text-align: center;">
                                <p style="color: #52525b; margin: 0; font-size: 12px;">© 2026 Métro-Taxi - Plateforme de transport partagé</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": t['subject'],
            "html": html_content
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Payout notification email sent to {email}, ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send payout email to {email}: {str(e)}")
        return False

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
        "iban": data.iban,
        "bic": data.bic,
        "is_active": False,
        "is_validated": True,  # Auto-validated at registration
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

class BankInfoUpdate(BaseModel):
    iban: str
    bic: str

@api_router.put("/drivers/bank-info")
async def update_driver_bank_info(data: BankInfoUpdate, current_user: dict = Depends(get_current_user)):
    """Update driver's bank account information (IBAN + BIC/SWIFT)"""
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
    
    if not driver:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    await db.drivers.update_one(
        {"id": driver_id}, 
        {"$set": {"iban": data.iban, "bic": data.bic}}
    )
    
    return {"message": "Informations bancaires mises à jour", "iban": data.iban, "bic": data.bic}

@api_router.get("/drivers/bank-info")
async def get_driver_bank_info(current_user: dict = Depends(get_current_user)):
    """Get driver's bank account information"""
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0, "iban": 1, "bic": 1})
    
    if not driver:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    return {"iban": driver.get("iban"), "bic": driver.get("bic")}

# Driver Earnings Routes
@api_router.get("/drivers/earnings")
async def get_driver_earnings(current_user: dict = Depends(get_current_user)):
    """Get driver's earnings summary"""
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    now = datetime.now(timezone.utc)
    current_month = now.strftime("%Y-%m")
    
    # Get current month earnings
    current_earnings = await db.driver_earnings.find_one(
        {"driver_id": driver_id, "month": current_month},
        {"_id": 0}
    )
    
    # Get all earnings history
    earnings_cursor = db.driver_earnings.find(
        {"driver_id": driver_id},
        {"_id": 0}
    ).sort("month", -1).limit(12)
    
    earnings_history = await earnings_cursor.to_list(length=12)
    
    # Calculate totals
    total_km = sum(e.get("total_km", 0) for e in earnings_history)
    total_revenue = sum(e.get("total_revenue", 0) for e in earnings_history)
    total_rides = sum(e.get("rides_count", 0) for e in earnings_history)
    
    # Get pending payouts
    pending_payouts = await db.driver_earnings.find(
        {"driver_id": driver_id, "payout_status": "pending"},
        {"_id": 0}
    ).to_list(length=12)
    
    pending_amount = sum(p.get("total_revenue", 0) for p in pending_payouts)
    
    return {
        "current_month": {
            "month": current_month,
            "total_km": current_earnings.get("total_km", 0) if current_earnings else 0,
            "total_revenue": current_earnings.get("total_revenue", 0) if current_earnings else 0,
            "rides_count": current_earnings.get("rides_count", 0) if current_earnings else 0,
            "payout_status": current_earnings.get("payout_status", "pending") if current_earnings else "pending"
        },
        "totals": {
            "total_km": round(total_km, 2),
            "total_revenue": round(total_revenue, 2),
            "total_rides": total_rides
        },
        "pending_payout": round(pending_amount, 2),
        "rate_per_km": DRIVER_RATE_PER_KM,
        "payout_day": PAYOUT_DAY,
        "history": earnings_history
    }

@api_router.get("/drivers/earnings/history")
async def get_driver_earnings_history(current_user: dict = Depends(get_current_user)):
    """Get detailed earnings history for a driver"""
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    
    # Get all completed rides with earnings
    rides_cursor = db.ride_requests.find(
        {"driver_id": driver_id, "status": "completed", "driver_revenue": {"$exists": True}},
        {"_id": 0, "id": 1, "user_name": 1, "completed_at": 1, "total_km": 1, "driver_revenue": 1, "pickup_km": 1, "ride_km": 1}
    ).sort("completed_at", -1).limit(50)
    
    rides = await rides_cursor.to_list(length=50)
    
    return {"rides": rides}

@api_router.get("/drivers/payouts")
async def get_driver_payouts(current_user: dict = Depends(get_current_user)):
    """Get payout history for a driver"""
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    
    payouts_cursor = db.driver_payouts.find(
        {"driver_id": driver_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(24)
    
    payouts = await payouts_cursor.to_list(length=24)
    
    return {"payouts": payouts}

# Admin Routes for Driver Payouts
@api_router.get("/admin/driver-earnings")
async def admin_get_all_driver_earnings(current_user: dict = Depends(get_current_user)):
    """Admin: Get all drivers' earnings summary for current month"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    now = datetime.now(timezone.utc)
    current_month = now.strftime("%Y-%m")
    
    # Get all pending earnings
    pending_cursor = db.driver_earnings.find(
        {"payout_status": "pending"},
        {"_id": 0}
    )
    pending_earnings = await pending_cursor.to_list(length=1000)
    
    # Enrich with driver info
    result = []
    for earning in pending_earnings:
        driver = await db.drivers.find_one(
            {"id": earning["driver_id"]},
            {"_id": 0, "first_name": 1, "last_name": 1, "email": 1, "iban": 1, "bic": 1}
        )
        if driver:
            result.append({
                **earning,
                "driver_name": f"{driver.get('first_name', '')} {driver.get('last_name', '')}",
                "driver_email": driver.get("email"),
                "has_bank_info": bool(driver.get("iban") and driver.get("bic")),
                "iban": driver.get("iban"),
                "bic": driver.get("bic")
            })
    
    total_pending = sum(e.get("total_revenue", 0) for e in result)
    
    return {
        "current_month": current_month,
        "payout_day": PAYOUT_DAY,
        "rate_per_km": DRIVER_RATE_PER_KM,
        "total_pending": round(total_pending, 2),
        "drivers_count": len(result),
        "earnings": result
    }

@api_router.post("/admin/process-payouts")
async def admin_process_payouts(current_user: dict = Depends(get_current_user)):
    """Admin: Process all pending payouts (manual trigger)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    now = datetime.now(timezone.utc)
    
    # Get all pending earnings with bank info
    pending_cursor = db.driver_earnings.find({"payout_status": "pending"}, {"_id": 0})
    pending_earnings = await pending_cursor.to_list(length=1000)
    
    processed = []
    errors = []
    
    for earning in pending_earnings:
        driver = await db.drivers.find_one(
            {"id": earning["driver_id"]},
            {"_id": 0, "first_name": 1, "last_name": 1, "email": 1, "iban": 1, "bic": 1}
        )
        
        if not driver:
            errors.append({"driver_id": earning["driver_id"], "error": "Driver not found"})
            continue
            
        if not driver.get("iban") or not driver.get("bic"):
            errors.append({
                "driver_id": earning["driver_id"],
                "driver_name": f"{driver.get('first_name', '')} {driver.get('last_name', '')}",
                "error": "Missing bank information (IBAN/BIC)"
            })
            continue
        
        # Create payout record
        payout_id = str(uuid.uuid4())
        payout_doc = {
            "id": payout_id,
            "driver_id": earning["driver_id"],
            "driver_name": f"{driver.get('first_name', '')} {driver.get('last_name', '')}",
            "driver_email": driver.get("email"),
            "iban": driver.get("iban"),
            "bic": driver.get("bic"),
            "month": earning["month"],
            "total_km": earning.get("total_km", 0),
            "total_revenue": earning.get("total_revenue", 0),
            "rides_count": earning.get("rides_count", 0),
            "status": "processed",  # In production, would be "pending_transfer" until bank confirms
            "created_at": now.isoformat(),
            "processed_by": current_user["user_id"]
        }
        
        await db.driver_payouts.insert_one(payout_doc)
        
        # Update earning status
        await db.driver_earnings.update_one(
            {"driver_id": earning["driver_id"], "month": earning["month"]},
            {"$set": {"payout_status": "paid", "payout_id": payout_id, "paid_at": now.isoformat()}}
        )
        
        processed.append({
            "driver_id": earning["driver_id"],
            "driver_name": f"{driver.get('first_name', '')} {driver.get('last_name', '')}",
            "amount": earning.get("total_revenue", 0),
            "month": earning["month"]
        })
    
    return {
        "processed_count": len(processed),
        "errors_count": len(errors),
        "total_amount": sum(p["amount"] for p in processed),
        "processed": processed,
        "errors": errors
    }

@api_router.get("/admin/payouts-history")
async def admin_get_payouts_history(current_user: dict = Depends(get_current_user)):
    """Admin: Get all payouts history"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    payouts_cursor = db.driver_payouts.find({}, {"_id": 0}).sort("created_at", -1).limit(100)
    payouts = await payouts_cursor.to_list(length=100)
    
    return {"payouts": payouts}

# ============================================
# STRIPE CONNECT - DRIVER PAYOUTS
# ============================================

def get_country_from_iban(iban: str) -> str:
    """Extract country code from IBAN"""
    if iban and len(iban) >= 2:
        return iban[:2].upper()
    return "FR"  # Default to France

def is_stripe_connect_available() -> bool:
    """Check if Stripe Connect is available (requires real API key, not sk_test_emergent)"""
    if not STRIPE_API_KEY:
        return False
    # The emergent test key doesn't support Connect API
    if STRIPE_API_KEY == "sk_test_emergent":
        return False
    return True

@api_router.get("/stripe-connect/config")
async def get_stripe_connect_config():
    """Get Stripe Connect configuration status"""
    connect_available = is_stripe_connect_available()
    
    return {
        "stripe_connect_available": connect_available,
        "message": "Stripe Connect actif - virements SEPA disponibles" if connect_available 
                   else "Stripe Connect non configuré - une vraie clé API Stripe est requise pour les virements SEPA",
        "payout_day": PAYOUT_DAY,
        "rate_per_km": DRIVER_RATE_PER_KM,
        "requirements": {
            "description": "Pour activer Stripe Connect (virements réels vers les comptes bancaires des chauffeurs)",
            "steps": [
                "1. Créer un compte Stripe sur https://dashboard.stripe.com",
                "2. Activer Stripe Connect dans les paramètres",
                "3. Obtenir une clé API (sk_live_xxx ou sk_test_xxx)",
                "4. Configurer la clé dans STRIPE_API_KEY du backend .env"
            ]
        }
    }

@api_router.post("/drivers/stripe-connect/create-account")
async def create_stripe_connect_account(current_user: dict = Depends(get_current_user)):
    """Create a Stripe Connect Express account for a driver"""
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    if not is_stripe_connect_available():
        raise HTTPException(
            status_code=503, 
            detail="Stripe Connect non disponible. Une vraie clé API Stripe est requise (pas sk_test_emergent). Veuillez configurer STRIPE_API_KEY avec votre clé Stripe."
        )
    
    driver_id = current_user["user_id"]
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
    
    if not driver:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    # Check if driver already has a Stripe account
    if driver.get("stripe_account_id"):
        # Return existing account with onboarding link if not complete
        try:
            account = stripe.Account.retrieve(driver["stripe_account_id"])
            if not account.details_submitted:
                # Generate new onboarding link
                account_link = stripe.AccountLink.create(
                    account=driver["stripe_account_id"],
                    refresh_url="https://metro-taxi.com/driver/stripe-refresh",
                    return_url="https://metro-taxi.com/driver/stripe-complete",
                    type="account_onboarding"
                )
                return {
                    "status": "pending_onboarding",
                    "stripe_account_id": driver["stripe_account_id"],
                    "onboarding_url": account_link.url,
                    "message": "Compte Stripe existant - Veuillez compléter la vérification"
                }
            return {
                "status": "exists",
                "stripe_account_id": driver["stripe_account_id"],
                "message": "Compte Stripe déjà configuré"
            }
        except stripe.error.StripeError:
            pass
    
    try:
        country = get_country_from_iban(driver["iban"]) if driver.get("iban") else "FR"
        
        # Create Stripe Connect Express account (simpler, works with France)
        account = stripe.Account.create(
            type="express",
            country=country,
            email=driver["email"],
            capabilities={
                "transfers": {"requested": True},
            },
            business_type="individual",
            business_profile={
                "mcc": "4121",  # Taxicabs and Limousines
                "product_description": "Chauffeur VTC partenaire Métro-Taxi"
            },
            metadata={
                "driver_id": driver_id,
                "platform": "metro-taxi"
            }
        )
        
        # Create account onboarding link
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url="https://metro-taxi.com/driver/stripe-refresh",
            return_url="https://metro-taxi.com/driver/stripe-complete",
            type="account_onboarding"
        )
        
        # Save Stripe account ID to driver record
        await db.drivers.update_one(
            {"id": driver_id},
            {"$set": {
                "stripe_account_id": account.id,
                "stripe_account_type": "express",
                "stripe_account_created_at": datetime.now(timezone.utc).isoformat(),
                "stripe_onboarding_complete": False
            }}
        )
        
        logging.info(f"Stripe Connect Express account created for driver {driver_id}: {account.id}")
        
        return {
            "status": "created",
            "stripe_account_id": account.id,
            "onboarding_url": account_link.url,
            "message": "Compte Stripe créé ! Cliquez sur le lien pour compléter la vérification."
        }
        
    except stripe.error.StripeError as e:
        logging.error(f"Stripe error creating account for driver {driver_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erreur Stripe: {str(e)}")

@api_router.get("/drivers/stripe-connect/status")
async def get_stripe_connect_status(current_user: dict = Depends(get_current_user)):
    """Get driver's Stripe Connect account status"""
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe non configuré")
    
    driver_id = current_user["user_id"]
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
    
    if not driver:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    if not driver.get("stripe_account_id"):
        return {
            "has_stripe_account": False,
            "message": "Aucun compte Stripe Connect"
        }
    
    try:
        account = stripe.Account.retrieve(driver["stripe_account_id"])
        
        return {
            "has_stripe_account": True,
            "stripe_account_id": account.id,
            "charges_enabled": account.charges_enabled,
            "payouts_enabled": account.payouts_enabled,
            "requirements": {
                "currently_due": account.requirements.currently_due if account.requirements else [],
                "eventually_due": account.requirements.eventually_due if account.requirements else [],
                "disabled_reason": account.requirements.disabled_reason if account.requirements else None
            }
        }
    except stripe.error.StripeError as e:
        logging.error(f"Stripe error getting account status for driver {driver_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erreur Stripe: {str(e)}")

@api_router.post("/admin/stripe-connect/process-payout/{driver_id}")
async def admin_process_stripe_payout(driver_id: str, current_user: dict = Depends(get_current_user)):
    """Admin: Process a real Stripe payout for a specific driver"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe non configuré")
    
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
    if not driver:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    if not driver.get("stripe_account_id"):
        raise HTTPException(status_code=400, detail="Le chauffeur n'a pas de compte Stripe Connect")
    
    # Get pending earnings for this driver
    pending_earnings = await db.driver_earnings.find(
        {"driver_id": driver_id, "payout_status": "pending"},
        {"_id": 0}
    ).to_list(length=100)
    
    if not pending_earnings:
        return {"message": "Aucun revenu en attente pour ce chauffeur", "amount": 0}
    
    total_amount = sum(e.get("total_revenue", 0) for e in pending_earnings)
    
    if total_amount <= 0:
        return {"message": "Montant insuffisant pour un virement", "amount": 0}
    
    try:
        now = datetime.now(timezone.utc)
        
        # Create a transfer to the connected account
        # Note: In production, you need sufficient balance in your platform account
        transfer = stripe.Transfer.create(
            amount=int(total_amount * 100),  # Convert to cents
            currency="eur",
            destination=driver["stripe_account_id"],
            metadata={
                "driver_id": driver_id,
                "driver_email": driver.get("email"),
                "months": ",".join([e["month"] for e in pending_earnings]),
                "platform": "metro-taxi"
            }
        )
        
        # Create payout record
        payout_id = str(uuid.uuid4())
        payout_doc = {
            "id": payout_id,
            "driver_id": driver_id,
            "driver_name": f"{driver.get('first_name', '')} {driver.get('last_name', '')}",
            "driver_email": driver.get("email"),
            "iban": driver.get("iban"),
            "bic": driver.get("bic"),
            "stripe_transfer_id": transfer.id,
            "stripe_account_id": driver["stripe_account_id"],
            "months": [e["month"] for e in pending_earnings],
            "total_km": sum(e.get("total_km", 0) for e in pending_earnings),
            "total_revenue": total_amount,
            "rides_count": sum(e.get("rides_count", 0) for e in pending_earnings),
            "status": "transferred",
            "created_at": now.isoformat(),
            "processed_by": current_user["user_id"]
        }
        
        await db.driver_payouts.insert_one(payout_doc)
        
        # Update all pending earnings to paid
        for earning in pending_earnings:
            await db.driver_earnings.update_one(
                {"driver_id": driver_id, "month": earning["month"]},
                {"$set": {
                    "payout_status": "paid",
                    "payout_id": payout_id,
                    "stripe_transfer_id": transfer.id,
                    "paid_at": now.isoformat()
                }}
            )
        
        # Send email notification to driver
        if driver.get("email"):
            driver_name = f"{driver.get('first_name', '')} {driver.get('last_name', '')}"
            payout_date = now.strftime("%d/%m/%Y")
            asyncio.create_task(send_payout_notification_email(
                email=driver["email"],
                name=driver_name,
                amount=total_amount,
                total_km=sum(e.get("total_km", 0) for e in pending_earnings),
                rides_count=sum(e.get("rides_count", 0) for e in pending_earnings),
                months=[e["month"] for e in pending_earnings],
                payout_date=payout_date,
                lang="fr"
            ))
        
        logging.info(f"Stripe payout processed for driver {driver_id}: €{total_amount} (transfer: {transfer.id})")
        
        return {
            "status": "success",
            "payout_id": payout_id,
            "stripe_transfer_id": transfer.id,
            "amount": total_amount,
            "message": f"Virement de €{total_amount:.2f} effectué avec succès"
        }
        
    except stripe.error.StripeError as e:
        logging.error(f"Stripe error processing payout for driver {driver_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erreur Stripe: {str(e)}")

@api_router.post("/admin/stripe-connect/process-all-payouts")
async def admin_process_all_stripe_payouts(current_user: dict = Depends(get_current_user)):
    """Admin: Process Stripe payouts for all eligible drivers"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe non configuré")
    
    now = datetime.now(timezone.utc)
    
    # Get all pending earnings
    pending_cursor = db.driver_earnings.find({"payout_status": "pending"}, {"_id": 0})
    pending_earnings = await pending_cursor.to_list(length=1000)
    
    # Group by driver
    driver_earnings_map = {}
    for earning in pending_earnings:
        driver_id = earning["driver_id"]
        if driver_id not in driver_earnings_map:
            driver_earnings_map[driver_id] = []
        driver_earnings_map[driver_id].append(earning)
    
    processed = []
    errors = []
    
    for driver_id, earnings in driver_earnings_map.items():
        driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
        
        if not driver:
            errors.append({"driver_id": driver_id, "error": "Chauffeur non trouvé"})
            continue
        
        if not driver.get("stripe_account_id"):
            errors.append({
                "driver_id": driver_id,
                "driver_name": f"{driver.get('first_name', '')} {driver.get('last_name', '')}",
                "error": "Pas de compte Stripe Connect"
            })
            continue
        
        total_amount = sum(e.get("total_revenue", 0) for e in earnings)
        
        if total_amount <= 0:
            continue
        
        try:
            # Create transfer
            transfer = stripe.Transfer.create(
                amount=int(total_amount * 100),
                currency="eur",
                destination=driver["stripe_account_id"],
                metadata={
                    "driver_id": driver_id,
                    "months": ",".join([e["month"] for e in earnings]),
                    "platform": "metro-taxi"
                }
            )
            
            # Create payout record
            payout_id = str(uuid.uuid4())
            payout_doc = {
                "id": payout_id,
                "driver_id": driver_id,
                "driver_name": f"{driver.get('first_name', '')} {driver.get('last_name', '')}",
                "driver_email": driver.get("email"),
                "stripe_transfer_id": transfer.id,
                "stripe_account_id": driver["stripe_account_id"],
                "months": [e["month"] for e in earnings],
                "total_km": sum(e.get("total_km", 0) for e in earnings),
                "total_revenue": total_amount,
                "rides_count": sum(e.get("rides_count", 0) for e in earnings),
                "status": "transferred",
                "created_at": now.isoformat(),
                "processed_by": current_user["user_id"]
            }
            
            await db.driver_payouts.insert_one(payout_doc)
            
            # Update earnings
            for earning in earnings:
                await db.driver_earnings.update_one(
                    {"driver_id": driver_id, "month": earning["month"]},
                    {"$set": {
                        "payout_status": "paid",
                        "payout_id": payout_id,
                        "stripe_transfer_id": transfer.id,
                        "paid_at": now.isoformat()
                    }}
                )
            
            processed.append({
                "driver_id": driver_id,
                "driver_name": f"{driver.get('first_name', '')} {driver.get('last_name', '')}",
                "amount": total_amount,
                "stripe_transfer_id": transfer.id
            })
            
        except stripe.error.StripeError as e:
            errors.append({
                "driver_id": driver_id,
                "driver_name": f"{driver.get('first_name', '')} {driver.get('last_name', '')}",
                "error": str(e)
            })
    
    total_processed = sum(p["amount"] for p in processed)
    
    logging.info(f"Bulk Stripe payouts: {len(processed)} processed, {len(errors)} errors, €{total_processed:.2f} total")
    
    return {
        "processed_count": len(processed),
        "errors_count": len(errors),
        "total_amount": round(total_processed, 2),
        "processed": processed,
        "errors": errors
    }

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
    """Complete a ride and calculate driver earnings
    
    MÉTRO-TAXI KILOMETER RULES:
    - ONLY km traveled WITH Métro-Taxi users on board are counted
    - Counter starts at "in_progress" (user embarked)
    - Counter stops at "completed" (user dropped off)
    - Pickup km (driver to user) are NOT counted - only user-on-board km
    """
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    ride = await db.ride_requests.find_one({"id": ride_id, "driver_id": driver_id}, {"_id": 0})
    
    if not ride:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    # ========================================
    # MÉTRO-TAXI: Only count km WITH user on board
    # ========================================
    
    # Check if km_with_user was already calculated by progress update
    km_with_user = ride.get("km_with_user")
    
    if km_with_user is None:
        # Calculate from km_start_location to destination (user was on board)
        km_start = ride.get("km_start_location")
        if km_start:
            km_with_user = calculate_distance(
                km_start["lat"], km_start["lng"],
                ride["destination_lat"], ride["destination_lng"]
            )
        else:
            # Fallback: use pickup to destination (but this shouldn't happen normally)
            km_with_user = calculate_distance(
                ride["pickup_lat"], ride["pickup_lng"],
                ride["destination_lat"], ride["destination_lng"]
            )
    
    # Round and calculate revenue
    km_with_user = round(km_with_user, 2)
    revenue = round(km_with_user * DRIVER_RATE_PER_KM, 2)
    
    logging.info(f"Ride {ride_id} completed: {km_with_user} km with user on board = €{revenue}")
    
    # Update ride with km and revenue
    completed_at = datetime.now(timezone.utc).isoformat()
    await db.ride_requests.update_one(
        {"id": ride_id},
        {"$set": {
            "status": "completed", 
            "completed_at": completed_at,
            "km_with_user": km_with_user,
            "total_km": km_with_user,  # For compatibility
            "driver_revenue": revenue
        }}
    )
    
    # Record in driver_earnings collection for monthly tracking
    now = datetime.now(timezone.utc)
    month_key = now.strftime("%Y-%m")
    
    await db.driver_earnings.update_one(
        {"driver_id": driver_id, "month": month_key},
        {
            "$inc": {
                "total_km": km_with_user,
                "total_revenue": revenue,
                "rides_count": 1
            },
            "$setOnInsert": {
                "created_at": now.isoformat(),
                "payout_status": "pending"
            },
            "$set": {
                "updated_at": now.isoformat()
            }
        },
        upsert=True
    )
    
    # Restore available seats
    await db.drivers.update_one({"id": driver_id}, {"$inc": {"available_seats": 1}})
    
    # Notify user
    await manager.send_personal_message({
        "type": "ride_completed",
        "ride_id": ride_id,
        "km_with_user": km_with_user,
        "revenue": revenue
    }, ride["user_id"])
    
    return {
        "status": "completed",
        "km_with_user": km_with_user,
        "revenue": revenue,
        "message": f"Trajet complété: {km_with_user} km avec usager = €{revenue:.2f}"
    }

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
    """Update ride progress status with real-time tracking
    
    IMPORTANT: Kilometer tracking rules for Métro-Taxi:
    - Counter starts when status changes to "in_progress" (user embarked)
    - Counter continues with multiple users on board (shared rides)
    - Counter stops when last user is dropped off (completed)
    - Only km with Métro-Taxi users on board are counted
    """
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    ride = await db.ride_requests.find_one({"id": ride_id, "driver_id": driver_id}, {"_id": 0})
    
    if not ride:
        raise HTTPException(status_code=404, detail="Trajet non trouvé")
    
    valid_statuses = ["pickup", "in_progress", "near_destination", "completed"]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Statut invalide")
    
    now = datetime.now(timezone.utc)
    update_data = {
        "status": data.status,
        f"{data.status}_at": now.isoformat()
    }
    
    if data.current_lat and data.current_lng:
        update_data["current_location"] = {"lat": data.current_lat, "lng": data.current_lng}
    
    # ========================================
    # KILOMETER TRACKING LOGIC FOR MÉTRO-TAXI
    # ========================================
    
    # When user embarks (in_progress): Start the km counter
    if data.status == "in_progress":
        update_data["progress_percent"] = 50
        # Record the position where km counting starts (user embarked)
        if data.current_lat and data.current_lng:
            update_data["km_start_location"] = {"lat": data.current_lat, "lng": data.current_lng}
            update_data["km_start_at"] = now.isoformat()
        else:
            # Use pickup location as start if no current location
            update_data["km_start_location"] = {"lat": ride["pickup_lat"], "lng": ride["pickup_lng"]}
            update_data["km_start_at"] = now.isoformat()
        
        logging.info(f"Ride {ride_id}: KM counter started - user embarked at {update_data['km_start_location']}")
    
    elif data.status == "pickup":
        update_data["progress_percent"] = 10
    
    elif data.status == "near_destination":
        update_data["progress_percent"] = 90
    
    elif data.status == "completed":
        update_data["progress_percent"] = 100
        
        # Calculate km traveled WITH user on board (from km_start to current/destination)
        km_start = ride.get("km_start_location")
        if km_start and data.current_lat and data.current_lng:
            # Use current location as end point
            km_with_user = calculate_distance(
                km_start["lat"], km_start["lng"],
                data.current_lat, data.current_lng
            )
        elif km_start:
            # Use destination as end point
            km_with_user = calculate_distance(
                km_start["lat"], km_start["lng"],
                ride["destination_lat"], ride["destination_lng"]
            )
        else:
            # Fallback: calculate from pickup to destination
            km_with_user = calculate_distance(
                ride["pickup_lat"], ride["pickup_lng"],
                ride["destination_lat"], ride["destination_lng"]
            )
        
        update_data["km_with_user"] = round(km_with_user, 2)
        update_data["km_end_at"] = now.isoformat()
        
        logging.info(f"Ride {ride_id}: KM counter stopped - {km_with_user:.2f} km with user on board")
        
        # Restore seat
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
        "message": status_messages.get(data.status, ""),
        "km_with_user": update_data.get("km_with_user")
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

    "en-GB": """Métro-Taxi, the intelligent ridesharing transportation system.
Welcome to Métro-Taxi, the subscription-based urban mobility network.
By choosing intelligent ridesharing, you contribute to environmental protection by reducing your carbon footprint.
Sign up and choose your plan. Locate vehicles heading in your direction.
Request a ride with a single click. The driver picks you up and drops you off wherever you want.
Thanks to our intelligent transfer system, switch vehicles along the way to reach your destination.
Métro-Taxi, your rides without limits, for a greener future.""",

    "de": """Métro-Taxi, das intelligente Fahrgemeinschafts-Transportsystem.
Willkommen bei Métro-Taxi, dem abonnementbasierten urbanen Mobilitätsnetzwerk.
Durch die Wahl intelligenter Fahrgemeinschaften tragen Sie zum Umweltschutz bei, indem Sie Ihren CO2-Fußabdruck reduzieren.
Registrieren Sie sich und wählen Sie Ihren Plan. Finden Sie Fahrzeuge, die in Ihre Richtung fahren.
Fordern Sie eine Fahrt mit einem Klick an. Der Fahrer holt Sie ab und setzt Sie ab, wo Sie möchten.
Dank unseres intelligenten Umstiegssystems können Sie unterwegs das Fahrzeug wechseln, um Ihr Ziel zu erreichen.
Métro-Taxi, Ihre Fahrten ohne Grenzen, für eine grünere Zukunft.""",

    "nl": """Métro-Taxi, het intelligente carpoolsysteem voor vervoer.
Welkom bij Métro-Taxi, het abonnementsgebaseerde stedelijke mobiliteitsnetwerk.
Door te kiezen voor intelligent carpoolen, draagt u bij aan milieubescherming door uw CO2-voetafdruk te verminderen.
Registreer en kies uw plan. Vind voertuigen die uw richting uitgaan.
Vraag een rit aan met één klik. De chauffeur pikt u op en zet u af waar u wilt.
Dankzij ons intelligente overstapsysteem kunt u onderweg van voertuig wisselen om uw bestemming te bereiken.
Métro-Taxi, uw ritten zonder grenzen, voor een groenere toekomst.""",

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

    "hi": """मेट्रो-टैक्सी, स्मार्ट राइड शेयरिंग ट्रांसपोर्ट सिस्टम।
मेट्रो-टैक्सी में आपका स्वागत है, सदस्यता-आधारित शहरी गतिशीलता नेटवर्क।
स्मार्ट राइड शेयरिंग चुनकर, आप अपने कार्बन फुटप्रिंट को कम करके पर्यावरण संरक्षण में योगदान करते हैं।
रजिस्टर करें और अपना प्लान चुनें। अपनी दिशा में जाने वाले वाहन खोजें।
एक क्लिक से यात्रा का अनुरोध करें। ड्राइवर आपको उठाएगा और जहां चाहें वहां छोड़ देगा।
हमारे स्मार्ट ट्रांसफर सिस्टम के कारण, अपने गंतव्य तक पहुंचने के लिए रास्ते में वाहन बदलें।
मेट्रो-टैक्सी, असीमित यात्रा, हरित भविष्य के लिए।""",

    "pa": """ਮੈਟਰੋ-ਟੈਕਸੀ, ਸਮਾਰਟ ਰਾਈਡ ਸ਼ੇਅਰਿੰਗ ਟ੍ਰਾਂਸਪੋਰਟ ਸਿਸਟਮ।
ਮੈਟਰੋ-ਟੈਕਸੀ ਵਿੱਚ ਤੁਹਾਡਾ ਸਵਾਗਤ ਹੈ, ਸਬਸਕ੍ਰਿਪਸ਼ਨ-ਅਧਾਰਤ ਸ਼ਹਿਰੀ ਗਤੀਸ਼ੀਲਤਾ ਨੈੱਟਵਰਕ।
ਸਮਾਰਟ ਰਾਈਡ ਸ਼ੇਅਰਿੰਗ ਚੁਣ ਕੇ, ਤੁਸੀਂ ਆਪਣੇ ਕਾਰਬਨ ਫੁੱਟਪ੍ਰਿੰਟ ਨੂੰ ਘਟਾ ਕੇ ਵਾਤਾਵਰਣ ਦੀ ਸੁਰੱਖਿਆ ਵਿੱਚ ਯੋਗਦਾਨ ਪਾਉਂਦੇ ਹੋ।
ਰਜਿਸਟਰ ਕਰੋ ਅਤੇ ਆਪਣਾ ਪਲਾਨ ਚੁਣੋ। ਆਪਣੀ ਦਿਸ਼ਾ ਵੱਲ ਜਾਣ ਵਾਲੀਆਂ ਗੱਡੀਆਂ ਲੱਭੋ।
ਇੱਕ ਕਲਿੱਕ ਨਾਲ ਸਫ਼ਰ ਦੀ ਬੇਨਤੀ ਕਰੋ। ਡਰਾਈਵਰ ਤੁਹਾਨੂੰ ਲੈ ਜਾਵੇਗਾ ਅਤੇ ਜਿੱਥੇ ਚਾਹੋ ਉੱਥੇ ਛੱਡ ਦੇਵੇਗਾ।
ਸਾਡੇ ਸਮਾਰਟ ਟ੍ਰਾਂਸਫਰ ਸਿਸਟਮ ਕਰਕੇ, ਆਪਣੀ ਮੰਜ਼ਿਲ ਤੱਕ ਪਹੁੰਚਣ ਲਈ ਰਸਤੇ ਵਿੱਚ ਗੱਡੀ ਬਦਲੋ।
ਮੈਟਰੋ-ਟੈਕਸੀ, ਬੇਅੰਤ ਸਫ਼ਰ, ਹਰੇ ਭਰੇ ਭਵਿੱਖ ਲਈ।""",

    "ar": """مترو-تاكسي، نظام التنقل الذكي بالمشاركة.
مرحباً بكم في مترو-تاكسي، شبكة التنقل الحضري بالاشتراك.
باختيار المشاركة الذكية في التنقل، تساهم في حماية البيئة من خلال تقليل بصمتك الكربونية.
سجل واختر خطتك. حدد موقع المركبات المتجهة في اتجاهك.
اطلب رحلة بنقرة واحدة. سيأتي السائق لاصطحابك وإيصالك حيث تريد.
بفضل نظام التحويل الذكي، يمكنك تغيير المركبة أثناء الطريق للوصول إلى وجهتك.
مترو-تاكسي، رحلاتك بلا حدود، من أجل مستقبل أكثر اخضراراً.""",

    "ru": """Метро-Такси, интеллектуальная система совместных поездок.
Добро пожаловать в Метро-Такси, сеть городской мобильности по подписке.
Выбирая умные совместные поездки, вы вносите вклад в защиту окружающей среды, сокращая свой углеродный след.
Зарегистрируйтесь и выберите свой план. Найдите автомобили, едущие в вашем направлении.
Запросите поездку одним кликом. Водитель заберёт вас и довезёт куда захотите.
Благодаря нашей интеллектуальной системе пересадок, вы можете сменить автомобиль по пути к месту назначения.
Метро-Такси, ваши поездки без ограничений, ради более зелёного будущего.""",

    "it": """Métro-Taxi, il sistema di trasporto intelligente in carpooling.
Benvenuti su Métro-Taxi, la rete di mobilità urbana in abbonamento.
Scegliendo il carpooling intelligente, contribuisci alla protezione dell'ambiente riducendo la tua impronta di carbonio.
Registrati e scegli il tuo piano. Trova i veicoli che vanno nella tua direzione.
Richiedi un passaggio con un clic. L'autista ti viene a prendere e ti lascia dove vuoi.
Grazie al nostro sistema di trasbordo intelligente, puoi cambiare veicolo lungo il percorso per raggiungere la tua destinazione.
Métro-Taxi, i tuoi viaggi senza limiti, per un futuro più verde."""
}

class TTSRequest(BaseModel):
    language: str = Field(..., description="Language code (fr, en, en-GB, de, nl, es, pt, no, sv, da, zh, hi, pa, ar, ru)")
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
            {"code": "en", "name": "English (US)", "flag": "🇺🇸"},
            {"code": "en-GB", "name": "English (UK)", "flag": "🇬🇧"},
            {"code": "es", "name": "Español", "flag": "🇪🇸"},
            {"code": "pt", "name": "Português", "flag": "🇵🇹"},
            {"code": "de", "name": "Deutsch", "flag": "🇩🇪"},
            {"code": "nl", "name": "Nederlands", "flag": "🇳🇱"},
            {"code": "no", "name": "Norsk", "flag": "🇳🇴"},
            {"code": "sv", "name": "Svenska", "flag": "🇸🇪"},
            {"code": "da", "name": "Dansk", "flag": "🇩🇰"},
            {"code": "zh", "name": "中文", "flag": "🇨🇳"},
            {"code": "hi", "name": "हिन्दी", "flag": "🇮🇳"},
            {"code": "pa", "name": "ਪੰਜਾਬੀ", "flag": "🇮🇳"},
            {"code": "ar", "name": "العربية", "flag": "🇸🇦"},
            {"code": "ru", "name": "Русский", "flag": "🇷🇺"},
            {"code": "it", "name": "Italiano", "flag": "🇮🇹"}
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

# ============================================
# AUTOMATIC DRIVER PAYOUT PROCESSING
# ============================================
async def process_automatic_payouts():
    """Background task to automatically process driver payouts on the 10th of each month using Stripe Connect"""
    while True:
        try:
            now = datetime.now(timezone.utc)
            
            # Check if today is payout day (10th of month)
            if now.day == PAYOUT_DAY:
                # Check if we already processed payouts today
                today_str = now.strftime("%Y-%m-%d")
                last_auto_payout = await db.system_logs.find_one(
                    {"type": "auto_payout", "date": today_str},
                    {"_id": 0}
                )
                
                if not last_auto_payout:
                    logging.info(f"Starting automatic Stripe Connect payout processing for {today_str}")
                    
                    # Get all pending earnings
                    pending_cursor = db.driver_earnings.find({"payout_status": "pending"}, {"_id": 0})
                    pending_earnings = await pending_cursor.to_list(length=1000)
                    
                    # Group by driver
                    driver_earnings_map = {}
                    for earning in pending_earnings:
                        driver_id = earning["driver_id"]
                        if driver_id not in driver_earnings_map:
                            driver_earnings_map[driver_id] = []
                        driver_earnings_map[driver_id].append(earning)
                    
                    processed_count = 0
                    total_amount = 0
                    errors = []
                    stripe_transfers = []
                    
                    for driver_id, earnings in driver_earnings_map.items():
                        driver = await db.drivers.find_one(
                            {"id": driver_id},
                            {"_id": 0}
                        )
                        
                        if not driver:
                            errors.append({"driver_id": driver_id, "reason": "Driver not found"})
                            continue
                        
                        if not driver.get("stripe_account_id"):
                            errors.append({
                                "driver_id": driver_id,
                                "driver_name": f"{driver.get('first_name', '')} {driver.get('last_name', '')}",
                                "reason": "No Stripe Connect account"
                            })
                            continue
                        
                        amount = sum(e.get("total_revenue", 0) for e in earnings)
                        
                        if amount <= 0:
                            continue
                        
                        # Process Stripe transfer if API key is available
                        if STRIPE_API_KEY:
                            try:
                                transfer = stripe.Transfer.create(
                                    amount=int(amount * 100),
                                    currency="eur",
                                    destination=driver["stripe_account_id"],
                                    metadata={
                                        "driver_id": driver_id,
                                        "months": ",".join([e["month"] for e in earnings]),
                                        "platform": "metro-taxi",
                                        "auto_payout": "true"
                                    }
                                )
                                stripe_transfer_id = transfer.id
                                status = "transferred"
                                stripe_transfers.append(transfer.id)
                            except stripe.error.StripeError as e:
                                logging.error(f"Stripe transfer error for driver {driver_id}: {str(e)}")
                                errors.append({
                                    "driver_id": driver_id,
                                    "reason": f"Stripe error: {str(e)}"
                                })
                                continue
                        else:
                            stripe_transfer_id = None
                            status = "processed"
                        
                        # Create payout record
                        payout_id = str(uuid.uuid4())
                        payout_doc = {
                            "id": payout_id,
                            "driver_id": driver_id,
                            "driver_name": f"{driver.get('first_name', '')} {driver.get('last_name', '')}",
                            "driver_email": driver.get("email"),
                            "iban": driver.get("iban"),
                            "bic": driver.get("bic"),
                            "stripe_account_id": driver.get("stripe_account_id"),
                            "stripe_transfer_id": stripe_transfer_id,
                            "months": [e["month"] for e in earnings],
                            "total_km": sum(e.get("total_km", 0) for e in earnings),
                            "total_revenue": amount,
                            "rides_count": sum(e.get("rides_count", 0) for e in earnings),
                            "status": status,
                            "created_at": now.isoformat(),
                            "processed_by": "system_auto"
                        }
                        
                        await db.driver_payouts.insert_one(payout_doc)
                        
                        # Update all earnings for this driver
                        for earning in earnings:
                            await db.driver_earnings.update_one(
                                {"driver_id": driver_id, "month": earning["month"]},
                                {"$set": {
                                    "payout_status": "paid",
                                    "payout_id": payout_id,
                                    "stripe_transfer_id": stripe_transfer_id,
                                    "paid_at": now.isoformat()
                                }}
                            )
                        
                        # Send email notification to driver
                        if driver.get("email"):
                            driver_name = f"{driver.get('first_name', '')} {driver.get('last_name', '')}"
                            payout_date = now.strftime("%d/%m/%Y")
                            asyncio.create_task(send_payout_notification_email(
                                email=driver["email"],
                                name=driver_name,
                                amount=amount,
                                total_km=sum(e.get("total_km", 0) for e in earnings),
                                rides_count=sum(e.get("rides_count", 0) for e in earnings),
                                months=[e["month"] for e in earnings],
                                payout_date=payout_date,
                                lang="fr"
                            ))
                            logging.info(f"Payout email notification queued for driver {driver_id}")
                        
                        processed_count += 1
                        total_amount += amount
                    
                    # Log the auto payout run
                    await db.system_logs.insert_one({
                        "type": "auto_payout",
                        "date": today_str,
                        "processed_count": processed_count,
                        "total_amount": round(total_amount, 2),
                        "errors_count": len(errors),
                        "stripe_transfers": stripe_transfers,
                        "created_at": now.isoformat()
                    })
                    
                    logging.info(f"Automatic Stripe payout completed: {processed_count} drivers, €{total_amount:.2f} total, {len(stripe_transfers)} transfers")
                    if errors:
                        logging.warning(f"Payout errors: {len(errors)} drivers skipped")
            
        except Exception as e:
            logging.error(f"Error in automatic payout processing: {e}")
        
        # Check every hour
        await asyncio.sleep(3600)

@app.on_event("startup")
async def start_payout_processor():
    """Start the background automatic payout processor"""
    asyncio.create_task(process_automatic_payouts())
    logging.info(f"Automatic payout processor started (processes on the {PAYOUT_DAY}th of each month)")

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
