from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
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
from emergentintegrations.llm.chat import LlmChat, UserMessage
from pywebpush import webpush, WebPushException

# Security middleware imports
from middleware.security import (
    SecurityMiddleware, 
    SecurityHeadersMiddleware, 
    limiter, 
    rate_limit_exceeded_handler,
    record_failed_login,
    clear_failed_login,
    is_login_allowed,
    get_security_stats,
    manual_block_ip,
    manual_unblock_ip,
    get_client_ip
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
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

# Subscription Plans (prices in cents to avoid floating point issues)
# Default plans (France/EUR)
SUBSCRIPTION_PLANS = {
    "24h": {"name": "24 heures", "price": 6.99, "price_cents": 699, "duration_hours": 24, "max_rides_per_period": 5},
    "1week": {"name": "1 semaine", "price": 19.99, "price_cents": 1999, "duration_hours": 168, "max_rides_per_period": 15, "max_rides_per_day": 3},
    "1month": {"name": "1 mois", "price": 53.99, "price_cents": 5399, "duration_hours": 720}
}

# Regional pricing configuration
REGIONAL_PRICING = {
    # France - Île-de-France (default)
    "paris": {
        "currency": "EUR",
        "currency_symbol": "€",
        "plans": {
            "24h": {"name": "24 heures", "price": 6.99, "price_cents": 699},
            "1week": {"name": "1 semaine", "price": 19.99, "price_cents": 1999},
            "1month": {"name": "1 mois", "price": 53.99, "price_cents": 5399}
        },
        "driver_rate_per_km": 1.50
    },
    # France - Lyon
    "lyon": {
        "currency": "EUR",
        "currency_symbol": "€",
        "plans": {
            "24h": {"name": "24 heures", "price": 6.99, "price_cents": 699},
            "1week": {"name": "1 semaine", "price": 19.99, "price_cents": 1999},
            "1month": {"name": "1 mois", "price": 53.99, "price_cents": 5399}
        },
        "driver_rate_per_km": 1.50
    },
    # UK - London Zones 1-2 (Central + Inner)
    "london_central": {
        "currency": "GBP",
        "currency_symbol": "£",
        "plans": {
            "24h": {"name": "24 Hours", "price": 9.99, "price_cents": 999},
            "1week": {"name": "1 Week", "price": 34.99, "price_cents": 3499},
            "1month": {"name": "1 Month", "price": 79.99, "price_cents": 7999}
        },
        "driver_rate_per_km": 2.00
    },
    # UK - London Zones 1-4 (Extended)
    "london_extended": {
        "currency": "GBP",
        "currency_symbol": "£",
        "plans": {
            "24h": {"name": "24 Hours", "price": 14.99, "price_cents": 1499},
            "1week": {"name": "1 Week", "price": 49.99, "price_cents": 4999},
            "1month": {"name": "1 Month", "price": 129.99, "price_cents": 12999}
        },
        "driver_rate_per_km": 2.00
    },
    # UK - London Zones 1-6 (Greater London)
    "london_greater": {
        "currency": "GBP",
        "currency_symbol": "£",
        "plans": {
            "24h": {"name": "24 Hours", "price": 19.99, "price_cents": 1999},
            "1week": {"name": "1 Week", "price": 69.99, "price_cents": 6999},
            "1month": {"name": "1 Month", "price": 149.00, "price_cents": 14900}
        },
        "driver_rate_per_km": 2.00
    },
    # Spain - Madrid Zone A (Centro + Banlieue proche)
    "madrid_zona_a": {
        "currency": "EUR",
        "currency_symbol": "€",
        "plans": {
            "24h": {"name": "24 Horas", "price": 4.99, "price_cents": 499},
            "1week": {"name": "1 Semana", "price": 14.99, "price_cents": 1499},
            "1month": {"name": "1 Mes", "price": 34.99, "price_cents": 3499}
        },
        "driver_rate_per_km": 1.20
    },
    # Spain - Madrid Extended (Zones B1-B2)
    "madrid_extended": {
        "currency": "EUR",
        "currency_symbol": "€",
        "plans": {
            "24h": {"name": "24 Horas", "price": 5.99, "price_cents": 599},
            "1week": {"name": "1 Semana", "price": 17.99, "price_cents": 1799},
            "1month": {"name": "1 Mes", "price": 44.99, "price_cents": 4499}
        },
        "driver_rate_per_km": 1.30
    },
    # Spain - Madrid Grande Couronne (Zones B3/C1/C2)
    "madrid_outer": {
        "currency": "EUR",
        "currency_symbol": "€",
        "plans": {
            "24h": {"name": "24 Horas", "price": 6.99, "price_cents": 699},
            "1week": {"name": "1 Semana", "price": 20.99, "price_cents": 2099},
            "1month": {"name": "1 Mes", "price": 54.99, "price_cents": 5499}
        },
        "driver_rate_per_km": 1.40
    }
}

def get_regional_pricing(region_id: str) -> dict:
    """Get pricing configuration for a specific region"""
    return REGIONAL_PRICING.get(region_id, REGIONAL_PRICING.get("paris"))

# Driver Revenue Configuration
DRIVER_RATE_PER_KM = 1.50  # €1.50 per kilometer (legacy fallback, vehicle-type rates in utils/helpers.py)
# Automatic payout runs every Monday (weekday=0) via Sogecommerce SEPA transfer.
# Drivers are NEVER paid in cash - all revenue is bank-transferred weekly on Mondays.
PAYOUT_WEEKDAY = 0  # 0=Monday, 1=Tuesday, ... 6=Sunday (Python datetime.weekday())
PAYOUT_DAY = "monday"  # Human label kept for legacy admin responses

# Create the main app
app = FastAPI(
    title="Métro-Taxi API",
    description="API sécurisée pour la plateforme Métro-Taxi",
    version="2.0.0"
)

# ============================================
# SECURITY MIDDLEWARES (Order matters!)
# ============================================
# 1. Rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# 2. Security middleware (IP blocking, injection detection)
app.add_middleware(SecurityMiddleware)

# 3. Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize auth service with JWT secret
from services.auth import init_auth
init_auth(JWT_SECRET, JWT_ALGORITHM)

# Import and include modular routers
from routes.regions import router as regions_router
from routes.ratings import router as ratings_router
from routes.chat import router as chat_router
from routes.tts import router as tts_router
from routes.payments import router as payments_router
from routes.sogecommerce import router as sogecommerce_router
from routes.admin import router as admin_router
from routes.admin import public_router as admin_public_router
from routes.ride_history import router as ride_history_router
from routes.support_chat import router as support_chat_router
from routes.promo_codes import router as promo_codes_router
from routes.auto_campaigns import router as auto_campaigns_router
from routes.auto_campaigns import attempt_auto_attribution
from routes.legal import router as legal_router

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

# Constants for algorithm (LEGACY / DEFAULT — used as fallback)
# The real config is now ADAPTIVE per zone (see utils/algorithm_config.py).
# These values match the Paris intra-muros profile.
SEGMENT_MIN_KM = 3.0
SEGMENT_MAX_KM = 4.0
MAX_PICKUP_DISTANCE_KM = 2.0
MAX_TRANSFERS = 2
DIRECTION_THRESHOLD = 60

# Adaptive zone-based algorithm
from utils.zone_detector import detect_zone, is_night_time
from utils.algorithm_config import get_zone_config, MAX_PASSENGERS_PER_VEHICLE

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
                                          dest_lat: float, dest_lng: float,
                                          postal_code: Optional[str] = None) -> dict:
    """
    Calculate optimal route with up to 2 transfers — ADAPTIVE per zone & time.
    Segments dynamiques selon la zone (paris_intra/banlieue/grande_couronne) et la nuit.
    """
    total_distance = calculate_distance(user_lat, user_lng, dest_lat, dest_lng)

    # Detect zone + night based on pickup location
    zone = detect_zone(lat=user_lat, lng=user_lng, postal_code=postal_code)
    night = is_night_time()
    cfg = await get_zone_config(db, zone, is_night=night)

    seg_min = cfg["segment_min_km"]
    seg_max = cfg["segment_max_km"]
    max_pickup = cfg["max_pickup_distance_km"]
    max_transfers = cfg["max_transfers"]
    direction_threshold = cfg["direction_threshold"]

    result = {
        "total_distance_km": round(total_distance, 2),
        "direct_route_possible": False,
        "segments": [],
        "transfer_points": [],
        "total_transfers": 0,
        "estimated_total_time_minutes": 0,
        "route_efficiency": 0,
        "zone": zone,
        "is_night": night,
        "config_used": {
            "segment_min_km": seg_min,
            "segment_max_km": seg_max,
            "max_pickup_distance_km": max_pickup,
            "max_transfers": max_transfers,
            "direction_threshold": direction_threshold,
        },
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

    # Need transfers - calculate optimal segments based on adaptive seg_max
    if total_distance <= seg_max * 2:
        # One transfer should suffice
        num_segments = 2
    else:
        # May need more transfers, bounded by max_transfers+1
        num_segments = min(max_transfers + 1, max(2, int(total_distance / seg_max) + 1))

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
            # Calculate transfer point using adaptive segment_distance
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
        self.chat_rooms: Dict[str, set] = {}  # ride_id -> set of user_ids in chat

    async def connect(self, websocket: WebSocket, user_id: str, user_type: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_types[user_id] = user_type

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_types:
            del self.user_types[user_id]
        # Remove from chat rooms
        for room_id in list(self.chat_rooms.keys()):
            if user_id in self.chat_rooms[room_id]:
                self.chat_rooms[room_id].discard(user_id)

    def join_chat_room(self, ride_id: str, user_id: str):
        if ride_id not in self.chat_rooms:
            self.chat_rooms[ride_id] = set()
        self.chat_rooms[ride_id].add(user_id)

    def leave_chat_room(self, ride_id: str, user_id: str):
        if ride_id in self.chat_rooms:
            self.chat_rooms[ride_id].discard(user_id)

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                logging.error(f"Error sending message to {user_id}: {e}")

    async def send_to_chat_room(self, ride_id: str, message: dict, exclude_user: str = None):
        """Send message to all users in a chat room"""
        if ride_id in self.chat_rooms:
            for user_id in self.chat_rooms[ride_id]:
                if user_id != exclude_user and user_id in self.active_connections:
                    try:
                        await self.active_connections[user_id].send_json(message)
                    except Exception as e:
                        logging.error(f"Error sending chat message to {user_id}: {e}")

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
    # Nouveaux champs obligatoires
    street_address: str  # Rue
    postal_code: str     # Code postal
    city: str            # Ville
    date_of_birth: str   # Date de naissance (format: YYYY-MM-DD)
    # Optionnel: code promo passé à l'inscription (legacy campaign manuelle)
    promo_code: Optional[str] = None
    # Optionnel: ID de campagne auto-attribution (tracking via URL ?campaign=...)
    signup_campaign: Optional[str] = None
    # Patch V10 — Code parrainage d'un partenaire commercial (?ref=GGSM)
    referral_code: Optional[str] = None

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

# ============================================
# CHAT SYSTEM MODELS
# ============================================
class ChatMessage(BaseModel):
    ride_id: str
    content: str
    
class ChatMessageResponse(BaseModel):
    id: str
    ride_id: str
    sender_id: str
    sender_type: str  # "user" or "driver"
    sender_name: str
    content: str
    created_at: str
    read: bool = False

# ============================================
# REGION SYSTEM MODELS
# ============================================
class RegionBounds(BaseModel):
    north: float  # Max latitude
    south: float  # Min latitude
    east: float   # Max longitude
    west: float   # Min longitude

class RegionCreate(BaseModel):
    id: str  # e.g., "paris", "lyon", "london"
    name: str  # Display name e.g., "Île-de-France"
    country: str  # ISO country code e.g., "FR", "GB"
    currency: str  # e.g., "EUR", "GBP"
    language: str  # Default language e.g., "fr", "en"
    timezone: str = "Europe/Paris"
    bounds: RegionBounds
    is_active: bool = False

class RegionResponse(BaseModel):
    id: str
    name: str
    country: str
    currency: str
    language: str
    timezone: str
    bounds: dict
    is_active: bool
    launch_date: Optional[str] = None
    created_at: str
    driver_count: int = 0
    user_count: int = 0

class RegionSubscription(BaseModel):
    region_id: str
    plan_id: str  # "24h", "1week", "1month"
    expires_at: str
    is_active: bool = True

class UserRegisterWithRegion(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str
    region_id: Optional[str] = None  # Optional, can be detected by geolocation

class DriverRegisterWithRegion(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str
    vehicle_plate: str
    vehicle_type: str
    seats: int
    vtc_license: str
    tax_id: Optional[str] = None  # SIRET (FR), NIF (PT/ES), etc.
    region_id: str  # Required for drivers
    iban: Optional[str] = None
    bic: Optional[str] = None
    # Tracking acquisition source (CDG, Gare du Nord, Facebook, TikTok, etc.)
    source_inscription: Optional[str] = None

class CheckoutRequestWithRegion(BaseModel):
    plan_id: str
    region_id: str
    origin_url: str

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

# ============================================
# REGION HELPER FUNCTIONS
# ============================================
def is_point_in_region(lat: float, lng: float, bounds: dict) -> bool:
    """Check if a geographic point is within region bounds"""
    return (bounds['south'] <= lat <= bounds['north'] and
            bounds['west'] <= lng <= bounds['east'])

async def detect_region_by_location(lat: float, lng: float) -> Optional[dict]:
    """Detect which region a point belongs to based on coordinates"""
    regions = await db.regions.find({"is_active": True}, {"_id": 0}).to_list(100)
    for region in regions:
        if is_point_in_region(lat, lng, region['bounds']):
            return region
    return None

async def get_region_or_default(region_id: Optional[str] = None) -> Optional[dict]:
    """Get region by ID or return first active region"""
    if region_id:
        region = await db.regions.find_one({"id": region_id}, {"_id": 0})
        return region
    # Return first active region as default
    return await db.regions.find_one({"is_active": True}, {"_id": 0})

def extract_region_from_host(host: str) -> Optional[str]:
    """Extract region ID from subdomain (e.g., paris.metro-taxi.com -> paris)"""
    if not host:
        return None
    parts = host.split('.')
    if len(parts) >= 3:
        subdomain = parts[0].lower()
        # Ignore www and other common subdomains
        if subdomain not in ['www', 'api', 'admin', 'app']:
            return subdomain
    return None

async def get_user_active_subscription_for_region(user_id: str, region_id: str) -> Optional[dict]:
    """Check if user has active subscription for specific region"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "subscriptions": 1})
    if not user or "subscriptions" not in user:
        return None
    
    now = datetime.now(timezone.utc)
    for sub in user.get("subscriptions", []):
        if sub.get("region_id") == region_id and sub.get("is_active", False):
            expires_at = datetime.fromisoformat(sub["expires_at"].replace('Z', '+00:00'))
            if expires_at > now:
                return sub
    return None

# Email functions extracted to services/emails.py
from services.emails import (
    send_verification_email,
    send_subscription_confirmation_email,
    send_payout_notification_email,
    send_subscription_expiry_reminder_email,
    send_gift_subscription_email
)

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
        "created_at": datetime.now(timezone.utc).isoformat(),
        # Nouveaux champs obligatoires
        "street_address": data.street_address,
        "postal_code": data.postal_code,
        "city": data.city,
        "date_of_birth": data.date_of_birth,
        # Campagne d'origine (auto-attribution à l'activation d'abonnement)
        "signup_campaign": data.signup_campaign,
        # Patch V10 — Parrainage d'un partenaire commercial
        "referral_code": (data.referral_code or "").upper().strip() or None,
    }
    
    # Create response before inserting to avoid ObjectId contamination
    user_response = {k: v for k, v in user_doc.items() if k not in ["password", "verification_token"]}
    
    await db.users.insert_one(user_doc)
    
    # Auto-redeem promo code if provided at signup (Saint-Denis launch campaign)
    promo_attached = None
    if data.promo_code:
        try:
            code = data.promo_code.strip().upper()
            promo = await db.promo_codes.find_one({"code": code}, {"_id": 0})
            now = datetime.now(timezone.utc)
            if promo and not promo.get("used"):
                try:
                    expires_dt = datetime.fromisoformat(promo["expires_at"].replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    expires_dt = None
                if expires_dt and expires_dt >= now:
                    await db.promo_codes.update_one(
                        {"code": code, "used": False},
                        {"$set": {
                            "used": True,
                            "used_by": user_id,
                            "used_at": now.isoformat(),
                            "redeemed_at": now.isoformat(),
                        }},
                    )
                    pending_promo = {
                        "code": code,
                        "type": promo.get("type", "free_first_ride"),
                        "max_distance_km": promo.get("max_distance_km", 10),
                        "expires_at": promo["expires_at"],
                        "region": promo.get("region"),
                        "campaign": promo.get("campaign"),
                        "redeemed_at": now.isoformat(),
                    }
                    await db.users.update_one({"id": user_id}, {"$set": {"pending_promo": pending_promo}})
                    promo_attached = pending_promo
        except Exception as promo_err:
            logging.warning(f"Promo code attach failed at signup: {promo_err}")
    
    # Store verification token separately for easy lookup
    await db.email_verifications.insert_one({
        "token": verification_token,
        "user_id": user_id,
        "user_type": "user",
        "email": data.email,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    })
    
    # Generate verification URL - use FRONTEND_URL env var as the source of truth
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
        "promo_attached": promo_attached,
        "message": "Un email de vérification a été envoyé"
    }

@api_router.post("/auth/register/driver")
async def register_driver(data: DriverRegisterWithRegion, request: Request):
    existing = await db.drivers.find_one({"email": data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    # Validate region exists and is active
    if data.region_id:
        region = await db.regions.find_one({"id": data.region_id, "is_active": True})
        if not region:
            raise HTTPException(status_code=400, detail="Région non disponible ou inactive")
    
    driver_id = str(uuid.uuid4())
    verification_token = generate_verification_token()
    
    # Compute pioneer number = current driver count + 1 (founder pioneer status)
    current_drivers_count = await db.drivers.count_documents({})
    pioneer_number = current_drivers_count + 1
    
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
        "tax_id": data.tax_id,  # SIRET (FR), NIF (PT/ES), etc.
        "iban": data.iban,
        "bic": data.bic,
        "region_id": data.region_id,  # Associate driver with region
        "source_inscription": data.source_inscription,  # CDG, Gare du Nord, Facebook, TikTok, etc.
        "pioneer_number": pioneer_number,  # Founder pioneer status (immutable)
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
    
    # Generate verification URL - use FRONTEND_URL env var as the source of truth
    host_url = os.environ.get("FRONTEND_URL", "https://metro-taxi-demo.emergent.host")
    verification_url = f"{host_url}/verify-email?token={verification_token}"
    
    # Get language from Accept-Language header
    accept_lang = request.headers.get("accept-language", "fr")
    lang = accept_lang.split(",")[0].split("-")[0] if accept_lang else "fr"
    
    # 1) Send verification email (async, non-blocking)
    asyncio.create_task(send_verification_email(
        email=data.email,
        name=data.first_name,
        verification_url=verification_url,
        lang=lang
    ))
    
    # 2) Send "Welcome Pioneer #X" strategic email from Judée (async, non-blocking)
    from services.emails import send_pioneer_welcome_email, send_founder_alert_new_driver
    asyncio.create_task(send_pioneer_welcome_email(
        email=data.email,
        name=data.first_name,
        pioneer_number=pioneer_number,
        source=data.source_inscription
    ))
    
    # 3) Send instant alert to founder (async, non-blocking)
    asyncio.create_task(send_founder_alert_new_driver({
        "first_name": data.first_name,
        "last_name": data.last_name,
        "email": data.email,
        "phone": data.phone,
        "pioneer_number": pioneer_number,
        "region_id": data.region_id,
        "vehicle_type": data.vehicle_type,
        "source_inscription": data.source_inscription
    }))
    
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
        # Check if this might be a re-click on an already-used link
        # by checking if any user/driver with this token pattern is already verified
        # Return a friendly message instead of an error
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
    
    # Generate verification URL - use FRONTEND_URL env var as the source of truth
    host_url = os.environ.get("FRONTEND_URL", "https://metro-taxi-demo.emergent.host")
    verification_url = f"{host_url}/verify-email?token={verification_token}"
    
    # Get user name for email
    if role == "user":
        name = user.get("first_name", "Utilisateur")
    else:
        name = driver.get("first_name", "Chauffeur")
    
    # Send verification email (async, non-blocking)
    asyncio.create_task(send_verification_email(
        email=email,
        name=name,
        verification_url=verification_url,
        lang="fr"
    ))
    
    return {"message": "Email de vérification renvoyé", "verification_url": verification_url}

@api_router.post("/auth/login")
async def login(data: LoginRequest, request: Request):
    # Get client IP for security tracking
    client_ip = get_client_ip(request)
    
    # Check if login is allowed (brute force protection — Patch V9 tracks email+IP)
    allowed, message = is_login_allowed(client_ip, data.email)
    if not allowed:
        raise HTTPException(status_code=429, detail=message)
    
    # PRIORITY ORDER (Patch V8.1 — Edgar bug fix):
    # Drivers FIRST so a driver with a duplicate user account gets driver dashboard
    driver = await db.drivers.find_one({"email": data.email}, {"_id": 0})
    if driver and verify_password(data.password, driver["password"]):
        if not driver.get("is_validated"):
            raise HTTPException(status_code=403, detail="Compte en attente de validation admin")
        clear_failed_login(client_ip, data.email)
        token = create_token(driver["id"], "driver")
        return {"token": token, "driver": {k: v for k, v in driver.items() if k != "password"}}
    
    # Then users
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if user and verify_password(data.password, user["password"]):
        clear_failed_login(client_ip, data.email)
        user_data = {k: v for k, v in user.items() if k != "password"}
        if user.get("role") == "admin":
            await _initiate_admin_otp(user["email"], client_ip)
            return {"otp_required": True, "email": user["email"], "message": "OTP envoyé par email"}
        else:
            token = create_token(user["id"], "user")
            return {"token": token, "user": user_data}
    
    # Check admin collection — require 2FA OTP
    admin = await db.admins.find_one({"email": data.email}, {"_id": 0})
    if admin and verify_password(data.password, admin["password"]):
        clear_failed_login(client_ip, data.email)
        await _initiate_admin_otp(admin["email"], client_ip)
        return {"otp_required": True, "email": admin["email"], "message": "OTP envoyé par email"}
    
    # Check commercial_partners (Patch V10 — 19/06/2026)
    partner = await db.commercial_partners.find_one({"email": data.email}, {"_id": 0})
    if partner and partner.get("password") and verify_password(data.password, partner["password"]):
        if partner.get("status") != "active":
            raise HTTPException(status_code=403, detail="Compte partenaire pas encore activé. Vérifie tes mails ou contacte l'admin.")
        clear_failed_login(client_ip, data.email)
        token = create_token(partner["id"], "partner")
        return {"token": token, "partner": {k: v for k, v in partner.items() if k != "password"}}
    
    # Record failed login attempt
    record_failed_login(client_ip, data.email)
    raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")


# ============================================
# 2FA ADMIN — OTP generation and verification
# ============================================
import secrets as _secrets

# In-memory throttle: max OTP emails per IP per window
_otp_email_throttle: dict[str, list[datetime]] = {}
OTP_MAX_PER_IP_PER_WINDOW = 3
OTP_THROTTLE_WINDOW_MINUTES = 15


def _otp_email_allowed(client_ip: str) -> tuple[bool, int]:
    """Check if this IP can trigger another OTP email. Returns (allowed, retry_after_seconds)."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=OTP_THROTTLE_WINDOW_MINUTES)
    history = [t for t in _otp_email_throttle.get(client_ip, []) if t > window_start]
    _otp_email_throttle[client_ip] = history
    if len(history) >= OTP_MAX_PER_IP_PER_WINDOW:
        retry_after = int((history[0] + timedelta(minutes=OTP_THROTTLE_WINDOW_MINUTES) - now).total_seconds())
        return False, max(retry_after, 1)
    return True, 0


async def _initiate_admin_otp(admin_email: str, client_ip: str):
    """Generate a 6-digit OTP, store it in DB with 5 min expiry, send it by email.

    Anti-bombing: max 3 OTPs per IP per 15 min. Raises HTTPException 429 if exceeded.
    """
    allowed, retry_after = _otp_email_allowed(client_ip)
    if not allowed:
        logging.warning(f"🛡️ OTP email throttled for IP {client_ip} (retry in {retry_after}s)")
        raise HTTPException(
            status_code=429,
            detail=f"Trop de demandes de code. Réessayez dans {retry_after // 60 + 1} min.",
        )

    from services.emails import send_admin_otp_email
    otp_code = f"{_secrets.randbelow(1000000):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    # Invalidate previous OTPs for this admin
    await db.admin_otps.delete_many({"email": admin_email})
    await db.admin_otps.insert_one({
        "email": admin_email,
        "code": otp_code,
        "expires_at": expires_at.isoformat(),
        "client_ip": client_ip,
        "attempts": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    # Record OTP email sent for throttling
    _otp_email_throttle.setdefault(client_ip, []).append(datetime.now(timezone.utc))
    await send_admin_otp_email(admin_email, otp_code, client_ip)
    logging.info(f"Admin OTP generated for {admin_email} from {client_ip}")


class AdminOTPVerifyRequest(BaseModel):
    email: EmailStr
    code: str


@api_router.post("/auth/admin/verify-otp")
async def verify_admin_otp(data: AdminOTPVerifyRequest, request: Request):
    """Verify a 6-digit OTP and return a JWT admin token if valid."""
    client_ip = get_client_ip(request)

    allowed, message = is_login_allowed(client_ip)
    if not allowed:
        raise HTTPException(status_code=429, detail=message)

    otp_doc = await db.admin_otps.find_one({"email": data.email}, {"_id": 0})
    if not otp_doc:
        record_failed_login(client_ip, data.email)
        raise HTTPException(status_code=401, detail="Code invalide ou expiré")

    # Expiry check
    expires_at = datetime.fromisoformat(otp_doc["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        await db.admin_otps.delete_one({"email": data.email})
        raise HTTPException(status_code=401, detail="Code expiré — reconnectez-vous")

    # Max 5 attempts
    if otp_doc.get("attempts", 0) >= 5:
        await db.admin_otps.delete_one({"email": data.email})
        record_failed_login(client_ip, data.email)
        raise HTTPException(status_code=429, detail="Trop de tentatives — reconnectez-vous")

    if otp_doc["code"] != data.code.strip():
        await db.admin_otps.update_one({"email": data.email}, {"$inc": {"attempts": 1}})
        record_failed_login(client_ip, data.email)
        raise HTTPException(status_code=401, detail="Code invalide")

    # Success: delete OTP, issue admin token
    await db.admin_otps.delete_one({"email": data.email})
    clear_failed_login(client_ip)

    admin = await db.admins.find_one({"email": data.email}, {"_id": 0, "password": 0})
    if not admin:
        admin = await db.users.find_one({"email": data.email, "role": "admin"}, {"_id": 0, "password": 0})
    if not admin:
        raise HTTPException(status_code=404, detail="Compte admin introuvable")

    token = create_token(admin["id"], "admin")
    logging.info(f"Admin 2FA success for {data.email} from {client_ip}")
    return {"token": token, "admin": admin}

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
        # Check users collection first (admin accounts stored there)
        admin = await db.users.find_one({"id": user_id, "role": "admin"}, {"_id": 0, "password": 0})
        if admin:
            return {"admin": admin}
        # Fallback to admins collection (legacy)
        admin = await db.admins.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if admin:
            return {"admin": admin}
    elif role == "partner":
        # Patch V10 — Partenaires commerciaux
        partner = await db.commercial_partners.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if partner:
            return {"partner": partner}
    
    raise HTTPException(status_code=404, detail="Utilisateur non trouvé")


# ============================================
# PASSWORD MANAGEMENT — Patch V9 (06/2026)
# ============================================
# 3 endpoints: forgot-password, reset-password, change-password
# Anti-bombing : max 3 demandes / 15 min / IP
from services.emails import send_password_reset_email

_pwd_reset_throttle: dict[str, list[datetime]] = {}
PWD_RESET_MAX_PER_IP = 3
PWD_RESET_WINDOW_MINUTES = 15


def _pwd_reset_email_allowed(client_ip: str) -> tuple[bool, int]:
    """Limit le nombre d'emails de reset par IP pour éviter le spam."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=PWD_RESET_WINDOW_MINUTES)
    history = [t for t in _pwd_reset_throttle.get(client_ip, []) if t > window_start]
    _pwd_reset_throttle[client_ip] = history
    if len(history) >= PWD_RESET_MAX_PER_IP:
        retry_after = int((history[0] + timedelta(minutes=PWD_RESET_WINDOW_MINUTES) - now).total_seconds())
        return False, max(retry_after, 1)
    return True, 0


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


async def _find_account_by_email(email: str):
    """Cherche dans drivers puis users (ordre cohérent avec login priority).
    Retourne (collection_name, doc) ou (None, None)."""
    driver = await db.drivers.find_one({"email": email}, {"_id": 0})
    if driver:
        return "drivers", driver
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if user:
        return "users", user
    return None, None


@api_router.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, request: Request):
    """Génère un code à 6 chiffres valide 15 min et l'envoie par email.
    Réponse identique que l'email existe ou non (anti-enumeration)."""
    client_ip = get_client_ip(request)
    allowed, retry_after = _pwd_reset_email_allowed(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Trop de demandes. Réessayez dans {retry_after // 60 + 1} min."
        )

    email = data.email.lower().strip()
    collection_name, account = await _find_account_by_email(email)

    if account:
        code = f"{secrets.randbelow(1000000):06d}"
        await db.password_resets.delete_many({"email": email})
        await db.password_resets.insert_one({
            "email": email,
            "code": code,
            "collection": collection_name,
            "user_id": account["id"],
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
            "attempts": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "client_ip": client_ip,
        })
        _pwd_reset_throttle.setdefault(client_ip, []).append(datetime.now(timezone.utc))
        name = account.get("first_name", "")
        asyncio.create_task(send_password_reset_email(email, name, code))
        logging.info(f"Password reset code generated for {email} from {client_ip}")

    # Réponse identique dans tous les cas pour éviter l'énumération d'emails
    return {"message": "Si un compte existe avec cet email, un code a été envoyé."}


@api_router.post("/auth/reset-password")
async def reset_password(data: ResetPasswordRequest, request: Request):
    """Vérifie le code et met à jour le mot de passe."""
    email = data.email.lower().strip()
    reset = await db.password_resets.find_one({"email": email}, {"_id": 0})

    if not reset:
        raise HTTPException(status_code=400, detail="Code invalide ou expiré")

    # Vérifier expiration
    expires_at = datetime.fromisoformat(reset["expires_at"])
    if expires_at < datetime.now(timezone.utc):
        await db.password_resets.delete_many({"email": email})
        raise HTTPException(status_code=400, detail="Code expiré. Demandez un nouveau code.")

    # Anti-brute-force sur le code lui-même
    if reset.get("attempts", 0) >= 5:
        await db.password_resets.delete_many({"email": email})
        raise HTTPException(status_code=429, detail="Trop de tentatives. Demandez un nouveau code.")

    if reset["code"] != data.code.strip():
        await db.password_resets.update_one(
            {"email": email},
            {"$inc": {"attempts": 1}}
        )
        raise HTTPException(status_code=400, detail="Code invalide")

    # Validation longueur mot de passe
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Le mot de passe doit faire au moins 8 caractères.")

    # Mise à jour du mot de passe
    new_hash = hash_password(data.new_password)
    collection_name = reset["collection"]
    user_id = reset["user_id"]
    await db[collection_name].update_one(
        {"id": user_id},
        {"$set": {"password": new_hash}}
    )
    await db.password_resets.delete_many({"email": email})
    # Reset également l'anti-brute-force login pour cet IP
    client_ip = get_client_ip(request)
    clear_failed_login(client_ip)
    logging.info(f"Password reset successful for {email}")

    return {"message": "Mot de passe mis à jour avec succès. Vous pouvez vous connecter."}


@api_router.post("/auth/change-password")
async def change_password(data: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """Changement de mot de passe pour utilisateur connecté."""
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Le nouveau mot de passe doit faire au moins 8 caractères.")

    role = current_user["role"]
    user_id = current_user["user_id"]

    if role == "driver":
        account = await db.drivers.find_one({"id": user_id}, {"_id": 0})
        collection_name = "drivers"
    elif role == "user":
        account = await db.users.find_one({"id": user_id}, {"_id": 0})
        collection_name = "users"
    elif role == "admin":
        account = await db.users.find_one({"id": user_id, "role": "admin"}, {"_id": 0})
        collection_name = "users"
        if not account:
            account = await db.admins.find_one({"id": user_id}, {"_id": 0})
            collection_name = "admins"
    else:
        raise HTTPException(status_code=403, detail="Type de compte non supporté")

    if not account:
        raise HTTPException(status_code=404, detail="Compte introuvable")

    if not verify_password(data.current_password, account["password"]):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")

    new_hash = hash_password(data.new_password)
    await db[collection_name].update_one(
        {"id": user_id},
        {"$set": {"password": new_hash}}
    )
    logging.info(f"Password changed for {role} {account.get('email')}")
    return {"message": "Mot de passe modifié avec succès"}


# Payment routes extracted to routes/payments.py
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
async def get_available_drivers(region_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get available drivers, optionally filtered by region.
    
    A driver is shown only if their GPS position was updated in the last 10 minutes.
    This prevents 'ghost' drivers from appearing when they closed the app without going OFFLINE.
    """
    stale_threshold = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    query = {
        "is_active": True,
        "is_validated": True,
        "location": {"$ne": None},
        "location_updated_at": {"$gte": stale_threshold}
    }
    
    # Filter by region if specified
    if region_id:
        query["region_id"] = region_id
    
    drivers = await db.drivers.find(query, {"_id": 0, "password": 0}).to_list(100)
    return {"drivers": drivers}

# ============================================
# MATCHING ALGORITHM ENDPOINTS
# ============================================

@api_router.post("/matching/find-drivers")
async def find_matching_drivers(data: MatchingRequest, region_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Find best matching drivers based on distance, direction, and availability.
    
    Excludes drivers with stale GPS (>10 min) to avoid 'ghost' matches.
    """
    stale_threshold = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    query = {
        "is_active": True,
        "is_validated": True,
        "location": {"$ne": None},
        "location_updated_at": {"$gte": stale_threshold},
        "available_seats": {"$gt": 0}
    }
    
    # Filter by region if specified
    if region_id:
        query["region_id"] = region_id
    
    drivers = await db.drivers.find(query, {"_id": 0, "password": 0}).to_list(100)
    
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
    
    # Tarif différencié selon le type de véhicule du chauffeur
    from utils.helpers import DRIVER_RATE_PER_KM_BY_VEHICLE, get_driver_rate_per_km
    driver_doc = await db.drivers.find_one(
        {"id": driver_id},
        {"_id": 0, "vehicle_type": 1}
    )
    vehicle_type = (driver_doc or {}).get("vehicle_type") or "berline"
    rate_per_km = get_driver_rate_per_km(vehicle_type)
    
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
        "rate_per_km": rate_per_km,
        "vehicle_type": vehicle_type,
        "rate_per_km_by_vehicle": DRIVER_RATE_PER_KM_BY_VEHICLE,
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

# Admin routes extracted to routes/admin.py
# TTS routes extracted to routes/tts.py
# ============================================
# PUSH NOTIFICATIONS ENDPOINTS
# ============================================

@api_router.get("/notifications/vapid-public-key")
async def get_vapid_public_key():
    """Get VAPID public key for push notification subscription"""
    vapid_public_key = os.environ.get("VAPID_PUBLIC_KEY", "")
    if not vapid_public_key:
        raise HTTPException(status_code=500, detail="VAPID keys not configured")
    return {"publicKey": vapid_public_key}

@api_router.post("/notifications/subscribe")
async def subscribe_push_notifications(subscription: PushSubscription, current_user: dict = Depends(get_current_user)):
    """Subscribe to push notifications"""
    user_id = current_user.get("user_id") or current_user.get("id")
    user_type = current_user.get("role", "user")
    
    # Store subscription
    sub_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_type": user_type,
        "endpoint": subscription.endpoint,
        "keys": subscription.keys,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Upsert by endpoint to avoid duplicates
    await db.push_subscriptions.update_one(
        {"endpoint": subscription.endpoint},
        {"$set": sub_doc},
        upsert=True
    )
    
    return {"success": True, "message": "Subscription registered"}

@api_router.delete("/notifications/unsubscribe")
async def unsubscribe_push_notifications(endpoint: str, current_user: dict = Depends(get_current_user)):
    """Unsubscribe from push notifications"""
    await db.push_subscriptions.delete_one({"endpoint": endpoint})
    return {"success": True, "message": "Subscription removed"}

async def send_push_notification(user_id: str, notification: NotificationPayload, user_type: str = "user"):
    """Send push notification to a specific user"""
    subscriptions = await db.push_subscriptions.find(
        {"user_id": user_id, "user_type": user_type}
    ).to_list(10)
    
    # Store notification for later retrieval (in-app notifications)
    notif_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_type": user_type,
        "title": notification.title,
        "body": notification.body,
        "data": notification.data,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notif_doc)
    
    # Send real push notifications via WebPush
    vapid_private_key = os.environ.get("VAPID_PRIVATE_KEY")
    vapid_contact = os.environ.get("VAPID_CONTACT", "mailto:contact@metro-taxi.com")
    
    sent_count = 0
    for sub in subscriptions:
        try:
            # Build subscription info for webpush
            subscription_info = {
                "endpoint": sub.get("endpoint"),
                "keys": sub.get("keys", {})
            }
            
            # Only send if we have valid VAPID keys and subscription
            if vapid_private_key and subscription_info.get("endpoint") and subscription_info.get("keys", {}).get("p256dh"):
                payload = json.dumps({
                    "title": notification.title,
                    "body": notification.body,
                    "icon": "/icons/icon-192x192.png",
                    "badge": "/icons/icon-72x72.png",
                    "data": notification.data or {}
                })
                
                webpush(
                    subscription_info=subscription_info,
                    data=payload,
                    vapid_private_key=vapid_private_key,
                    vapid_claims={"sub": vapid_contact}
                )
                sent_count += 1
                logging.info(f"Push notification sent to user {user_id}")
        except WebPushException as e:
            logging.error(f"WebPush failed for user {user_id}: {e}")
            # If subscription is gone (410 Gone), remove it
            if e.response and e.response.status_code == 410:
                await db.push_subscriptions.delete_one({"endpoint": sub.get("endpoint")})
        except Exception as e:
            logging.error(f"Failed to send push notification: {e}")
    
    return sent_count

@api_router.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user), limit: int = 20):
    """Get user's notifications"""
    user_id = current_user.get("user_id") or current_user.get("id")
    user_type = current_user.get("role", "user")
    
    notifications = await db.notifications.find(
        {"user_id": user_id, "user_type": user_type},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    unread_count = await db.notifications.count_documents(
        {"user_id": user_id, "user_type": user_type, "read": False}
    )
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a notification as read"""
    await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"read": True}}
    )
    return {"success": True}

@api_router.put("/notifications/read-all")
async def mark_all_notifications_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    user_id = current_user.get("user_id") or current_user.get("id")
    user_type = current_user.get("role", "user")
    
    await db.notifications.update_many(
        {"user_id": user_id, "user_type": user_type},
        {"$set": {"read": True}}
    )
    return {"success": True}

@api_router.get("/subscription/status")
async def get_subscription_status(current_user: dict = Depends(get_current_user)):
    """Get current user's subscription status with expiration details"""
    user_id = current_user.get("user_id") or current_user.get("id")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    now = datetime.now(timezone.utc)
    subscription_active = user.get("subscription_active", False)
    expires_str = user.get("subscription_expires")
    
    hours_remaining = None
    days_remaining = None
    is_expiring_soon = False
    
    if expires_str and subscription_active:
        try:
            expires = datetime.fromisoformat(expires_str)
            delta = expires - now
            hours_remaining = max(0, round(delta.total_seconds() / 3600))
            days_remaining = max(0, round(delta.total_seconds() / 86400, 1))
            is_expiring_soon = hours_remaining <= 48
        except (ValueError, TypeError):
            pass
    
    return {
        "active": subscription_active,
        "plan": user.get("subscription_plan"),
        "expires_at": expires_str,
        "hours_remaining": hours_remaining,
        "days_remaining": days_remaining,
        "is_expiring_soon": is_expiring_soon
    }

# ============================================
# MULTI-REGION SUBSCRIPTION ENDPOINTS
# ============================================

@api_router.get("/config/public")
async def get_public_config():
    """Public config endpoint — exposes subscription pause status and launch date.
    
    Used by frontend to know if it should display the subscription button or
    the 'waitlist' message instead.
    """
    paused = os.environ.get("SUBSCRIPTIONS_PAUSED", "false").lower() == "true"
    launch_date = os.environ.get("LAUNCH_DATE", "2026-07-26")
    return {
        "subscriptions_paused": paused,
        "launch_date": launch_date,
        "message_fr": (
            f"Métro-Taxi est en phase de finalisation technique. "
            f"Pour garantir la qualité du service à nos premiers abonnés, "
            f"nous suspendons temporairement les nouvelles souscriptions jusqu'au "
            f"lancement officiel le {launch_date}. Inscris-toi sur la liste prioritaire."
        ) if paused else "Souscriptions ouvertes"
    }


class WaitlistJoinRequest(BaseModel):
    email: str
    first_name: Optional[str] = None
    region_id: Optional[str] = "paris"


@api_router.post("/waitlist/join")
async def waitlist_join(data: WaitlistJoinRequest):
    """Anyone can join the launch waitlist (no auth required).
    
    Stores email + region; will be used for a mass-email on launch day.
    """
    email = data.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Email invalide")
    
    # Upsert by email (no duplicates)
    await db.launch_waitlist.update_one(
        {"email": email},
        {
            "$setOnInsert": {
                "email": email,
                "first_name": data.first_name,
                "region_id": data.region_id or "paris",
                "joined_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    total = await db.launch_waitlist.count_documents({})
    return {
        "success": True,
        "message": "Tu es bien inscrit·e sur la liste prioritaire. On te préviendra en premier au lancement.",
        "waitlist_position": total
    }


@api_router.get("/subscription/regions")
async def get_user_region_subscriptions(current_user: dict = Depends(get_current_user)):
    """Get all region subscriptions for the current user"""
    user_id = current_user.get("user_id") or current_user.get("id")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    now = datetime.now(timezone.utc)
    subscriptions = user.get("subscriptions", [])
    
    result = []
    for sub in subscriptions:
        region_id = sub.get("region_id")
        region = await db.regions.find_one({"id": region_id}, {"_id": 0})
        
        expires_str = sub.get("expires_at")
        is_active = False
        hours_remaining = 0
        
        if expires_str:
            try:
                expires = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                delta = expires - now
                hours_remaining = max(0, round(delta.total_seconds() / 3600))
                is_active = hours_remaining > 0
            except (ValueError, TypeError):
                pass
        
        result.append({
            "region_id": region_id,
            "region": region,
            "plan_id": sub.get("plan_id"),
            "expires_at": expires_str,
            "is_active": is_active,
            "hours_remaining": hours_remaining,
            "created_at": sub.get("created_at")
        })
    
    return {"subscriptions": result}

@api_router.get("/subscription/region/{region_id}")
async def get_subscription_for_region(region_id: str, current_user: dict = Depends(get_current_user)):
    """Check if user has active subscription for a specific region"""
    user_id = current_user.get("user_id") or current_user.get("id")
    
    subscription = await get_user_active_subscription_for_region(user_id, region_id)
    
    if subscription:
        now = datetime.now(timezone.utc)
        expires = datetime.fromisoformat(subscription["expires_at"].replace('Z', '+00:00'))
        hours_remaining = max(0, round((expires - now).total_seconds() / 3600))
        
        return {
            "has_subscription": True,
            "subscription": {
                **subscription,
                "hours_remaining": hours_remaining,
                "is_expiring_soon": hours_remaining <= 48
            }
        }
    
    return {"has_subscription": False, "subscription": None}

@api_router.post("/notifications/test-expiry")
async def create_test_expiry_notification(current_user: dict = Depends(get_current_user)):
    """Create a test subscription expiry notification for the current user (for testing purposes)"""
    user_id = current_user.get("user_id") or current_user.get("id")
    role = current_user.get("role", "user")
    
    # Get user email for sending test email
    user_email = None
    user_name = "Utilisateur"
    if role == "user":
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "email": 1, "first_name": 1})
        if user:
            user_email = user.get("email")
            user_name = user.get("first_name", "Utilisateur")
    
    notif_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_type": "user",
        "title": "Abonnement expire bientôt",
        "body": "Votre abonnement Métro-Taxi expire bientôt. Renouvelez-le dès maintenant pour continuer à utiliser le service sans interruption.",
        "data": {
            "type": "subscription_expiry",
            "notification_key": "test_expiry",
            "expiry_date": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "hours_remaining": 24,
            "action": "renew",
            "action_url": "/subscription"
        },
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notif_doc)
    
    # Also send test email if email is available
    email_sent = False
    if user_email:
        email_sent = await send_subscription_expiry_reminder_email(
            email=user_email,
            name=user_name,
            hours_remaining=24,
            expires_at=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            lang="fr"
        )
    
    return {
        "success": True, 
        "notification_id": notif_doc["id"], 
        "message": "Test expiry notification created",
        "email_sent": email_sent,
        "email_to": user_email
    }

# ============================================
# Ride history routes extracted to routes/ride_history.py
# Create / update default admin from environment variables
@app.on_event("startup")
async def create_default_admin():
    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        logging.warning("ADMIN_EMAIL / ADMIN_PASSWORD non configurés dans .env — admin non créé")
        return

    existing = await db.admins.find_one({"email": admin_email})
    if not existing:
        admin_doc = {
            "id": str(uuid.uuid4()),
            "email": admin_email,
            "password": hash_password(admin_password),
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.admins.insert_one(admin_doc)
        logging.info(f"Default admin created: {admin_email}")
    else:
        # Always sync the password to match .env (allows rotation)
        await db.admins.update_one(
            {"email": admin_email},
            {"$set": {"password": hash_password(admin_password)}}
        )
        logging.info(f"Admin password synced from .env for {admin_email}")

    # Remove any legacy insecure admin account if a different admin_email is used
    if admin_email != "admin@metrotaxi.fr":
        await db.admins.delete_many({"email": "admin@metrotaxi.fr"})
        logging.info("Legacy admin account admin@metrotaxi.fr removed")

    # 🛡️ SECURITY HARDENING (2026-05-20) :
    # Auto-purge of all admin accounts (in db.admins and db.users) whose email
    # is NOT the canonical ADMIN_EMAIL from .env. Closes the "zombie admin" backdoor
    # where a test/legacy admin account keeps an old bcrypt hash unsynced.
    purged_admins = await db.admins.delete_many({"email": {"$ne": admin_email}})
    if purged_admins.deleted_count > 0:
        logging.warning(
            f"🛡️ Purged {purged_admins.deleted_count} non-canonical admin account(s) "
            f"from db.admins (kept only {admin_email})"
        )
    purged_users_admin = await db.users.delete_many({
        "role": "admin",
        "email": {"$ne": admin_email}
    })
    if purged_users_admin.deleted_count > 0:
        logging.warning(
            f"🛡️ Purged {purged_users_admin.deleted_count} non-canonical admin account(s) "
            f"from db.users"
        )

    # Always invalidate any pending OTP at startup (force re-auth after restart)
    await db.admin_otps.delete_many({})
    logging.info("All pending admin OTPs invalidated at startup")

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
# AUTOMATIC SUBSCRIPTION EXPIRATION NOTIFICATIONS
# ============================================
async def check_and_notify_expiring_subscriptions():
    """Background task to send notifications for expiring subscriptions at 48h, 24h, and day of expiration"""
    while True:
        try:
            now = datetime.now(timezone.utc)
            
            # Find all users with active subscriptions
            active_users = await db.users.find({
                "subscription_active": True,
                "subscription_expires": {"$ne": None}
            }, {"_id": 0, "id": 1, "subscription_expires": 1, "email": 1, "first_name": 1}).to_list(1000)
            
            for user in active_users:
                expires_str = user.get("subscription_expires")
                if not expires_str:
                    continue
                    
                try:
                    expires = datetime.fromisoformat(expires_str)
                    hours_until_expiry = (expires - now).total_seconds() / 3600
                    
                    # Define notification thresholds and their keys
                    thresholds = [
                        (48, 47, "subscription_expiry_48h"),  # 48h notification (between 47-48 hours)
                        (24, 23, "subscription_expiry_24h"),  # 24h notification (between 23-24 hours)
                        (1, 0, "subscription_expiry_today"),   # Day of expiration (0-1 hours)
                    ]
                    
                    for max_hours, min_hours, notif_key in thresholds:
                        if min_hours < hours_until_expiry <= max_hours:
                            # Check if we already sent this notification
                            existing_notif = await db.notifications.find_one({
                                "user_id": user["id"],
                                "data.notification_key": notif_key,
                                "data.expiry_date": expires_str
                            })
                            
                            if not existing_notif:
                                # Create the notification
                                notif_doc = {
                                    "id": str(uuid.uuid4()),
                                    "user_id": user["id"],
                                    "user_type": "user",
                                    "title": "Abonnement expire bientôt" if hours_until_expiry > 1 else "Abonnement expire aujourd'hui",
                                    "body": "Votre abonnement Métro-Taxi expire bientôt. Renouvelez-le dès maintenant pour continuer à utiliser le service sans interruption.",
                                    "data": {
                                        "type": "subscription_expiry",
                                        "notification_key": notif_key,
                                        "expiry_date": expires_str,
                                        "hours_remaining": round(hours_until_expiry),
                                        "action": "renew",
                                        "action_url": "/subscription"
                                    },
                                    "read": False,
                                    "created_at": datetime.now(timezone.utc).isoformat()
                                }
                                await db.notifications.insert_one(notif_doc)
                                logging.info(f"Subscription expiry notification ({notif_key}) sent to user: {user.get('email', user['id'])}")
                                
                                # Also send email reminder
                                user_email = user.get("email")
                                user_name = user.get("first_name", "Utilisateur")
                                if user_email:
                                    asyncio.create_task(send_subscription_expiry_reminder_email(
                                        email=user_email,
                                        name=user_name,
                                        hours_remaining=round(hours_until_expiry),
                                        expires_at=expires_str,
                                        lang="fr"
                                    ))
                                    logging.info(f"Subscription expiry email reminder scheduled for: {user_email}")
                            break  # Only send one notification per check
                            
                except (ValueError, TypeError) as e:
                    logging.error(f"Error parsing expiration date for user {user['id']}: {e}")
            
        except Exception as e:
            logging.error(f"Error checking expiring subscriptions for notifications: {e}")
        
        # Check every hour
        await asyncio.sleep(3600)

@app.on_event("startup")
async def start_subscription_notification_checker():
    """Start the background subscription expiration notification checker"""
    asyncio.create_task(check_and_notify_expiring_subscriptions())
    logging.info("Subscription expiration notification checker started (runs every hour)")

# ============================================
# AUTOMATIC DRIVER PAYOUT PROCESSING
# ============================================
async def process_automatic_payouts():
    """Background task to automatically process driver payouts EVERY MONDAY via SEPA/Stripe.
    
    Métro-Taxi rule: drivers are NEVER paid in cash. All earnings are bank-transferred
    weekly on Mondays for the previous week. The deduplication key is the ISO week
    (YYYY-Www) so that a Monday run only triggers once per week.
    """
    while True:
        try:
            now = datetime.now(timezone.utc)
            
            # Trigger only on Mondays (Python: Monday=0)
            if now.weekday() == PAYOUT_WEEKDAY:
                # Deduplication by ISO week (e.g. "2026-W24"). Guarantees one run per week.
                iso_year, iso_week, _ = now.isocalendar()
                week_key = f"{iso_year}-W{iso_week:02d}"
                today_str = now.strftime("%Y-%m-%d")
                last_auto_payout = await db.system_logs.find_one(
                    {"type": "auto_payout", "week": week_key},
                    {"_id": 0}
                )
                
                if not last_auto_payout:
                    logging.info(f"Starting automatic weekly payout processing for {week_key} ({today_str})")
                    
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
                    
                    # Log the auto payout run (keyed by ISO week)
                    await db.system_logs.insert_one({
                        "type": "auto_payout",
                        "date": today_str,
                        "week": week_key,
                        "processed_count": processed_count,
                        "total_amount": round(total_amount, 2),
                        "errors_count": len(errors),
                        "stripe_transfers": stripe_transfers,
                        "created_at": now.isoformat()
                    })
                    
                    logging.info(f"Automatic weekly payout completed for {week_key}: {processed_count} drivers, €{total_amount:.2f} total, {len(stripe_transfers)} transfers")
                    if errors:
                        logging.warning(f"Payout errors: {len(errors)} drivers skipped")
                    
                    # Patch V10 — Process partner commissions on the same Monday cycle
                    try:
                        from routes.commercial_partners import process_weekly_partner_payouts
                        partner_summary = await process_weekly_partner_payouts()
                        logging.info(
                            f"Partner payouts for {week_key}: "
                            f"{partner_summary['payouts_created']} partenaires, "
                            f"€{partner_summary['total_eur']:.2f} total"
                        )
                    except Exception as exc:
                        logging.error(f"Partner payout processing failed: {exc}")
            
        except Exception as e:
            logging.error(f"Error in automatic payout processing: {e}")
        
        # Check every hour
        await asyncio.sleep(3600)

@app.on_event("startup")
async def start_payout_processor():
    """Start the background automatic payout processor"""
    asyncio.create_task(process_automatic_payouts())
    logging.info("Automatic payout processor started (runs every Monday — weekly SEPA transfers)")


# ============================================
# STALE DRIVER CLEANER (auto-OFFLINE after inactivity)
# ============================================
async def cleanup_stale_drivers():
    """Auto-deactivate drivers whose GPS has not been updated in the last 10 minutes.
    
    This prevents 'ghost drivers' from staying online for hours (e.g. Abderrahim case 14/06).
    Runs every minute, sets is_active=false on stale drivers.
    """
    while True:
        try:
            stale_cutoff = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
            result = await db.drivers.update_many(
                {
                    "is_active": True,
                    "location_updated_at": {"$lt": stale_cutoff}
                },
                {"$set": {"is_active": False, "auto_offline_at": datetime.now(timezone.utc).isoformat()}}
            )
            if result.modified_count > 0:
                logging.info(f"Auto-OFFLINE: {result.modified_count} stale driver(s) deactivated (>10 min no GPS)")
        except Exception as e:
            logging.error(f"Stale driver cleanup error: {e}")
        await asyncio.sleep(60)  # Check every minute


@app.on_event("startup")
async def start_stale_driver_cleaner():
    """Start the background stale driver cleaner"""
    asyncio.create_task(cleanup_stale_drivers())
    logging.info("Stale driver cleaner started (auto-OFFLINE after 10 min no GPS)")

@app.on_event("startup")
async def verify_database_connection():
    """Verify MongoDB connection at startup with retry logic"""
    max_retries = 5
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # Ping the database to verify connection
            await client.admin.command('ping')
            logging.info("✅ MongoDB connection verified successfully")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"MongoDB connection attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            else:
                logging.error(f"❌ Failed to connect to MongoDB after {max_retries} attempts: {e}")
                # Don't raise - let the app start and handle errors per-request
                # This allows the app to recover if DB becomes available later

@app.on_event("startup")
async def initialize_default_regions():
    """Create default regions if they don't exist"""
    default_regions = [
        # FRANCE
        {
            "id": "paris",
            "name": "Île-de-France",
            "country": "FR",
            "currency": "EUR",
            "language": "fr",
            "timezone": "Europe/Paris",
            "bounds": {
                "north": 49.2415,
                "south": 48.1200,
                "east": 3.5590,
                "west": 1.4465
            },
            "is_active": True,
            "launch_date": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "lyon",
            "name": "Rhône-Alpes",
            "country": "FR",
            "currency": "EUR",
            "language": "fr",
            "timezone": "Europe/Paris",
            "bounds": {
                "north": 46.3000,
                "south": 45.5000,
                "east": 5.2000,
                "west": 4.5000
            },
            "is_active": False,
            "launch_date": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        # UK - LONDON
        {
            "id": "london_central",
            "name": "London Zones 1-2",
            "description": "Central London + Inner (Camden, Greenwich, Brixton)",
            "country": "GB",
            "currency": "GBP",
            "language": "en",
            "timezone": "Europe/London",
            "bounds": {
                "north": 51.5500,
                "south": 51.4500,
                "east": 0.0500,
                "west": -0.2500
            },
            "is_active": False,
            "launch_date": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "london_extended",
            "name": "London Zones 1-4",
            "description": "Central + Stratford, Wimbledon, Wembley, Ealing",
            "country": "GB",
            "currency": "GBP",
            "language": "en",
            "timezone": "Europe/London",
            "bounds": {
                "north": 51.6200,
                "south": 51.3500,
                "east": 0.1500,
                "west": -0.4000
            },
            "is_active": False,
            "launch_date": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "london_greater",
            "name": "Greater London (Zones 1-6)",
            "description": "All Greater London including Heathrow, Croydon, Barnet",
            "country": "GB",
            "currency": "GBP",
            "language": "en",
            "timezone": "Europe/London",
            "bounds": {
                "north": 51.6919,
                "south": 51.2868,
                "east": 0.3340,
                "west": -0.5103
            },
            "is_active": False,
            "launch_date": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        # SPAIN - MADRID
        {
            "id": "madrid_zona_a",
            "name": "Madrid Zone A",
            "description": "Madrid Centro + Alcorcón, Getafe, Leganés, Alcobendas, Coslada",
            "country": "ES",
            "currency": "EUR",
            "language": "es",
            "timezone": "Europe/Madrid",
            "bounds": {
                "north": 40.5500,
                "south": 40.3000,
                "east": -3.5500,
                "west": -3.8500
            },
            "is_active": False,
            "launch_date": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "madrid_extended",
            "name": "Madrid Zones B1-B2",
            "description": "Grande couronne: Móstoles, Fuenlabrada, Parla, Arganda del Rey",
            "country": "ES",
            "currency": "EUR",
            "language": "es",
            "timezone": "Europe/Madrid",
            "bounds": {
                "north": 40.6500,
                "south": 40.1500,
                "east": -3.3000,
                "west": -4.0500
            },
            "is_active": False,
            "launch_date": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "madrid_outer",
            "name": "Madrid Zones B3/C1/C2",
            "description": "Grande couronne éloignée: Alcalá de Henares, Torrejón de Ardoz, San Fernando de Henares",
            "country": "ES",
            "currency": "EUR",
            "language": "es",
            "timezone": "Europe/Madrid",
            "bounds": {
                "north": 40.7500,
                "south": 40.0500,
                "east": -3.1000,
                "west": -4.2000
            },
            "is_active": False,
            "launch_date": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    for region in default_regions:
        existing = await db.regions.find_one({"id": region["id"]})
        if not existing:
            await db.regions.insert_one(region)
            logging.info(f"✅ Created default region: {region['name']} ({region['id']})")
        else:
            # Update existing region with new fields if missing
            update_fields = {}
            if "description" in region and not existing.get("description"):
                update_fields["description"] = region["description"]
            if update_fields:
                await db.regions.update_one({"id": region["id"]}, {"$set": update_fields})
            logging.info(f"ℹ️ Region already exists: {region['name']} ({region['id']})")

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
            
            elif message.get("type") == "join_chat":
                # Join a chat room for a specific ride
                ride_id = message.get("ride_id")
                if ride_id:
                    manager.join_chat_room(ride_id, user_id)
                    await websocket.send_json({"type": "chat_joined", "ride_id": ride_id})
            
            elif message.get("type") == "leave_chat":
                # Leave a chat room
                ride_id = message.get("ride_id")
                if ride_id:
                    manager.leave_chat_room(ride_id, user_id)
                    await websocket.send_json({"type": "chat_left", "ride_id": ride_id})
            
            elif message.get("type") == "typing":
                # Broadcast typing indicator to chat room
                ride_id = message.get("ride_id")
                if ride_id:
                    await manager.send_to_chat_room(ride_id, {
                        "type": "typing",
                        "user_id": user_id,
                        "user_type": user_type
                    }, exclude_user=user_id)
                    
    except WebSocketDisconnect:
        manager.disconnect(user_id)

# ============================================
# STATIC AUDIO FILES WITH CACHE HEADERS
# ============================================
# Serve pre-generated voiceover MP3 files with long cache headers
# This avoids the no-cache issue from the React dev server

AUDIO_DIR = Path(__file__).parent.parent / "frontend" / "public" / "audio" / "voiceover"

@app.get("/api/audio/voiceover/{filename}")
async def serve_voiceover_audio(filename: str):
    """
    Serve pre-generated voiceover MP3 files with proper caching headers.
    Files are immutable (pre-generated), so we can cache them for a long time.
    """
    # Sanitize filename to prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Only allow .mp3 files
    if not filename.endswith(".mp3"):
        raise HTTPException(status_code=400, detail="Only MP3 files are allowed")
    
    file_path = AUDIO_DIR / filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Return file with aggressive caching headers (1 year)
    return FileResponse(
        path=str(file_path),
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "Accept-Ranges": "bytes"
        }
    )


# ============================================
# CARTE DE VISITE PDF — Téléchargement direct
# ============================================
@app.get("/api/assets/business-card.pdf")
async def download_business_card():
    """Force le téléchargement du PDF Vistaprint-ready (contourne le routing React)."""
    pdf_path = ROOT_DIR.parent / "frontend" / "public" / "cards" / "Carte-Visite-Metro-Taxi-Vistaprint.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Carte de visite introuvable")
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename="Carte-Visite-Metro-Taxi-Vistaprint.pdf",
        headers={"Content-Disposition": 'attachment; filename="Carte-Visite-Metro-Taxi-Vistaprint.pdf"'}
    )


@app.get("/api/assets/business-card-preview-{face}.png")
async def preview_business_card(face: str):
    """Previews PNG (recto / verso) pour visualisation rapide avant téléchargement PDF."""
    if face not in ("recto", "verso"):
        raise HTTPException(status_code=404, detail="face must be 'recto' or 'verso'")
    png_path = ROOT_DIR.parent / "frontend" / "public" / "cards" / f"preview-{face}.png"
    if not png_path.exists():
        raise HTTPException(status_code=404, detail="Preview introuvable")
    return FileResponse(path=str(png_path), media_type="image/png")


@app.get("/api/assets/note-synthese-parallel.pdf")
async def download_note_synthese_pdf():
    """PDF de la note de synthèse Parallel (1 page A4, prêt à envoyer aux avocats)."""
    pdf_path = ROOT_DIR.parent / "frontend" / "public" / "cards" / "Metro-Taxi-Note-Synthese-Parallel.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Note de synthèse PDF introuvable")
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename="Metro-Taxi-Note-Synthese-Parallel.pdf",
        headers={"Content-Disposition": 'attachment; filename="Metro-Taxi-Note-Synthese-Parallel.pdf"'}
    )


@app.get("/api/assets/note-synthese-parallel.docx")
async def download_note_synthese_docx():
    """DOCX éditable de la note de synthèse Parallel (modifiable avant envoi)."""
    docx_path = ROOT_DIR.parent / "frontend" / "public" / "cards" / "Metro-Taxi-Note-Synthese-Parallel.docx"
    if not docx_path.exists():
        raise HTTPException(status_code=404, detail="Note de synthèse DOCX introuvable")
    return FileResponse(
        path=str(docx_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="Metro-Taxi-Note-Synthese-Parallel.docx",
        headers={"Content-Disposition": 'attachment; filename="Metro-Taxi-Note-Synthese-Parallel.docx"'}
    )


# ============================================
# AI HELP CHATBOT
# ============================================
# Multilingual AI chatbot for customer support

class ChatMessage(BaseModel):
    message: str
    language: str = "fr"
    session_id: Optional[str] = None
    user_type: str = "user"  # "user" or "driver"

class ChatResponse(BaseModel):
    response: str
    session_id: str

# System prompts for the chatbot
CHATBOT_SYSTEM_PROMPT = """Tu es l'assistant virtuel de Métro-Taxi, une plateforme de mise en relation entre usagers et chauffeurs VTC.

RÈGLES IMPORTANTES:
1. Réponds TOUJOURS dans la langue de l'utilisateur (détectée automatiquement)
2. Sois concis, professionnel et amical
3. Si tu ne connais pas la réponse, suggère de contacter le support
4. Ne donne JAMAIS d'informations fausses sur les tarifs ou les politiques

INFORMATIONS SUR MÉTRO-TAXI:
- Abonnements: Différents plans selon les régions (mensuel, trimestriel, annuel)
- Les abonnements s'enchaînent automatiquement (la nouvelle période s'ajoute à l'ancienne)
- Les chauffeurs reçoivent leurs virements le 15 de chaque mois
- L'application est disponible en 16 langues
- Support disponible par email

POUR LES USAGERS:
- Comment s'abonner: Aller sur "Abonnements" et choisir un plan
- Comment commander un trajet: Depuis le tableau de bord, entrer destination et cliquer "Commander"
- Annulation: Possible avant l'arrivée du chauffeur
- Paiement: Carte bancaire via Stripe (sécurisé)

POUR LES CHAUFFEURS:
- Inscription: Formulaire avec pièces d'identité, permis, numéro fiscal (SIRET/NIF)
- Validation: Un admin doit valider le profil avant de pouvoir accepter des courses
- Revenus: Visibles dans le tableau de bord, virements le 15 du mois
- IBAN: À renseigner dans les paramètres pour recevoir les virements

Si l'utilisateur pose une question hors sujet, ramène poliment la conversation vers Métro-Taxi."""

@app.post("/api/help/chat", response_model=ChatResponse)
async def help_chatbot(chat_message: ChatMessage):
    """
    AI-powered multilingual chatbot for customer support.
    Responds in the user's language automatically.
    """
    try:
        emergent_key = os.environ.get('EMERGENT_LLM_KEY')
        if not emergent_key:
            raise HTTPException(status_code=500, detail="Chatbot not configured")
        
        # Generate session ID if not provided
        session_id = chat_message.session_id or str(uuid.uuid4())
        
        # Customize system prompt based on user type
        user_context = "Tu parles à un USAGER (client qui commande des trajets)." if chat_message.user_type == "user" else "Tu parles à un CHAUFFEUR VTC partenaire."
        
        # Language instruction
        language_names = {
            "fr": "français", "en": "English", "es": "español", "de": "Deutsch",
            "it": "italiano", "pt": "português", "nl": "Nederlands", "sv": "svenska",
            "no": "norsk", "da": "dansk", "zh": "中文", "hi": "हिन्दी",
            "pa": "ਪੰਜਾਬੀ", "ar": "العربية", "ru": "русский"
        }
        lang_name = language_names.get(chat_message.language.split('-')[0], "français")
        
        full_system = f"{CHATBOT_SYSTEM_PROMPT}\n\n{user_context}\n\nIMPORTANT: Réponds en {lang_name}."
        
        # Initialize chat
        chat = LlmChat(
            api_key=emergent_key,
            session_id=session_id,
            system_message=full_system
        ).with_model("openai", "gpt-4o-mini")
        
        # Send message and get response
        user_msg = UserMessage(text=chat_message.message)
        response = await chat.send_message(user_msg)
        
        # Store conversation in database for analytics (optional)
        await db.help_conversations.insert_one({
            "session_id": session_id,
            "user_type": chat_message.user_type,
            "language": chat_message.language,
            "user_message": chat_message.message,
            "bot_response": response,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return ChatResponse(response=response, session_id=session_id)
        
    except Exception as e:
        logging.error(f"Chatbot error: {e}")
        # Fallback message in user's language
        fallback_messages = {
            "fr": "Désolé, je rencontre un problème technique. Veuillez réessayer ou contacter le support.",
            "en": "Sorry, I'm experiencing a technical issue. Please try again or contact support.",
            "es": "Lo siento, estoy experimentando un problema técnico. Por favor, inténtelo de nuevo.",
            "de": "Entschuldigung, ich habe ein technisches Problem. Bitte versuchen Sie es erneut.",
            "it": "Mi dispiace, sto riscontrando un problema tecnico. Per favore riprova.",
            "pt": "Desculpe, estou com um problema técnico. Por favor, tente novamente.",
            "ar": "عذراً، أواجه مشكلة تقنية. يرجى المحاولة مرة أخرى.",
            "zh": "抱歉，我遇到了技术问题。请重试。",
            "ru": "Извините, у меня техническая проблема. Пожалуйста, попробуйте снова."
        }
        lang = chat_message.language.split('-')[0]
        fallback = fallback_messages.get(lang, fallback_messages["en"])
        return ChatResponse(response=fallback, session_id=chat_message.session_id or str(uuid.uuid4()))

# Include the router in the main app
app.include_router(api_router)

# Include modular routers (regions routes moved to routes/regions.py)
app.include_router(regions_router)
app.include_router(ratings_router)
app.include_router(chat_router)
app.include_router(tts_router)
app.include_router(payments_router)
app.include_router(sogecommerce_router)
app.include_router(admin_router)
app.include_router(admin_public_router)
app.include_router(ride_history_router)
app.include_router(support_chat_router)
app.include_router(promo_codes_router)
app.include_router(auto_campaigns_router)
app.include_router(legal_router)

# Marketing assets download endpoint (forces download, bypasses PWA scope)
from routes.marketing import router as marketing_router
app.include_router(marketing_router)

# Founding members VIP waitlist (tarif fondateur 53,99€/mois verrouillé à vie)
from routes.founding_members import router as founding_members_router
app.include_router(founding_members_router)

from routes.fleet_partnerships import router as fleet_partnerships_router
app.include_router(fleet_partnerships_router)
from routes.commercial_partners import router as commercial_partners_router
app.include_router(commercial_partners_router)

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
