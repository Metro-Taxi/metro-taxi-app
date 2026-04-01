"""
Routes API pour l'algorithme de matching - Métro-Taxi
Gère : recherche de chauffeurs, optimisation de trajets, transbordements
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import math

# Imports locaux
from database import db
from models.schemas import MatchingRequest
from services.auth import get_current_user

router = APIRouter(prefix="/api/matching", tags=["matching"])

# ============================================
# CONSTANTS - Algorithme de matching
# ============================================
SEGMENT_MIN_KM = 1.5
SEGMENT_MAX_KM = 3.0
MAX_PICKUP_DISTANCE_KM = 2.0
MAX_TRANSFERS = 2
DIRECTION_THRESHOLD = 60


# ============================================
# HELPER FUNCTIONS
# ============================================

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculer la distance entre deux points en km (formule Haversine)"""
    R = 6371
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def calculate_bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculer le cap (bearing) entre deux points en degrés"""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    lng_diff = math.radians(lng2 - lng1)
    
    x = math.sin(lng_diff) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lng_diff)
    
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def calculate_direction_score(user_bearing: float, driver_bearing: float) -> int:
    """Calculer le score de compatibilité de direction (0-100)"""
    diff = abs(user_bearing - driver_bearing)
    if diff > 180:
        diff = 360 - diff
    
    if diff <= 30:
        return 100
    elif diff <= 60:
        return 80
    elif diff <= 90:
        return 50
    else:
        return max(0, 100 - diff)


def calculate_eta_minutes(distance_km: float, avg_speed_kmh: float = 30) -> int:
    """Calculer l'ETA en minutes"""
    return max(1, round((distance_km / avg_speed_kmh) * 60))


def calculate_matching_score(driver: dict, user_lat: float, user_lng: float, 
                            dest_lat: float, dest_lng: float) -> dict:
    """Calculer le score de matching complet pour un chauffeur"""
    driver_loc = driver.get("location", {})
    driver_dest = driver.get("destination", {})
    
    if not driver_loc:
        return {"score": 0, "pickup_distance": float('inf'), "direction_score": 0}
    
    # Distance de prise en charge
    pickup_distance = calculate_distance(
        user_lat, user_lng, 
        driver_loc.get("lat", 0), driver_loc.get("lng", 0)
    )
    
    # Score de direction
    user_bearing = calculate_bearing(user_lat, user_lng, dest_lat, dest_lng)
    
    if driver_dest:
        driver_bearing = calculate_bearing(
            driver_loc.get("lat", 0), driver_loc.get("lng", 0),
            driver_dest.get("lat", 0), driver_dest.get("lng", 0)
        )
        direction_score = calculate_direction_score(user_bearing, driver_bearing)
    else:
        direction_score = 50
    
    # Score de proximité
    if pickup_distance <= 0.5:
        proximity_score = 100
    elif pickup_distance <= 1:
        proximity_score = 80
    elif pickup_distance <= 2:
        proximity_score = 60
    else:
        proximity_score = max(0, 40 - (pickup_distance - 2) * 10)
    
    # Score combiné
    total_score = (direction_score * 0.5) + (proximity_score * 0.5)
    
    return {
        "score": round(total_score, 1),
        "pickup_distance": round(pickup_distance, 2),
        "direction_score": direction_score,
        "proximity_score": proximity_score,
        "eta_minutes": calculate_eta_minutes(pickup_distance)
    }


# ============================================
# ROUTES
# ============================================

@router.post("/find-drivers")
async def find_matching_drivers(data: MatchingRequest, region_id: Optional[str] = None, 
                                current_user: dict = Depends(get_current_user)):
    """Trouver les chauffeurs correspondants selon distance, direction et disponibilité"""
    query = {"is_active": True, "is_validated": True, "location": {"$ne": None}, "available_seats": {"$gt": 0}}
    
    if region_id:
        query["region_id"] = region_id
    
    drivers = await db.drivers.find(query, {"_id": 0, "password": 0}).to_list(100)
    
    matched_drivers = []
    for driver in drivers:
        match_info = calculate_matching_score(
            driver, data.user_lat, data.user_lng, data.dest_lat, data.dest_lng
        )
        if match_info["score"] > 10:
            matched_drivers.append({
                **driver,
                "matching": match_info
            })
    
    matched_drivers.sort(key=lambda x: x["matching"]["score"], reverse=True)
    
    return {"drivers": matched_drivers[:10]}


@router.post("/transfers")
async def find_transfer_routes(data: MatchingRequest, current_user: dict = Depends(get_current_user)):
    """Trouver les options de transbordement pour un trajet optimisé"""
    # Import depuis server.py pour éviter la duplication de code
    try:
        from server import find_transfer_options
        transfers = await find_transfer_options(
            data.user_lat, data.user_lng, data.dest_lat, data.dest_lng
        )
    except ImportError:
        transfers = []
    
    return {"transfers": transfers, "count": len(transfers)}


@router.post("/optimal-route")
async def get_optimal_route(data: MatchingRequest, current_user: dict = Depends(get_current_user)):
    """
    Calculer le trajet optimal avec optimisation automatique des transbordements
    Retourne un plan complet avec segments (1.5-3km) et jusqu'à 2 transbordements
    """
    try:
        from server import calculate_multi_transfer_route
        route = await calculate_multi_transfer_route(
            data.user_lat, data.user_lng, data.dest_lat, data.dest_lng
        )
    except ImportError:
        route = {"error": "Route calculation not available"}
    
    return {
        "route": route,
        "algorithm_config": {
            "segment_min_km": SEGMENT_MIN_KM,
            "segment_max_km": SEGMENT_MAX_KM,
            "max_transfers": MAX_TRANSFERS,
            "direction_threshold": DIRECTION_THRESHOLD
        }
    }


@router.get("/driver-passengers/{driver_id}")
async def get_driver_compatible_passengers(driver_id: str, current_user: dict = Depends(get_current_user)):
    """Obtenir les passagers compatibles avec la direction du chauffeur"""
    if current_user["role"] != "driver" and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    try:
        from server import find_compatible_passengers_for_driver
        passengers = await find_compatible_passengers_for_driver(driver_id)
    except ImportError:
        passengers = []
    
    return {
        "passengers": passengers,
        "count": len(passengers),
        "auto_match_enabled": True
    }


@router.get("/network-status")
async def get_network_status(current_user: dict = Depends(get_current_user)):
    """Obtenir le statut en temps réel du réseau - véhicules disponibles, couverture, etc."""
    active_drivers = await db.drivers.find(
        {"is_active": True, "is_validated": True, "location": {"$ne": None}},
        {"_id": 0, "password": 0}
    ).to_list(1000)
    
    total_seats = sum(d.get('available_seats', 0) for d in active_drivers)
    
    # Zone de couverture
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
    
    # Trajets actifs
    active_rides = await db.ride_requests.count_documents(
        {"status": {"$in": ["accepted", "pickup", "in_progress"]}}
    )
    
    # Demandes en attente
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


@router.get("/suggestions/{user_id}")
async def get_ride_suggestions(user_id: str, current_user: dict = Depends(get_current_user)):
    """Obtenir des suggestions de trajets personnalisées"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    user_location = user.get("location")
    if not user_location:
        return {"suggestions": [], "message": "Position utilisateur non disponible"}
    
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
