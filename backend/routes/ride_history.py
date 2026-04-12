"""
Routes API pour l'historique des trajets - Métro-Taxi
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import math

from database import db
from services.auth import get_current_user

router = APIRouter(prefix="/api", tags=["ride_history"])

# RIDE HISTORY ENDPOINTS
# ============================================

@router.get("/rides/history")
async def get_ride_history(
    current_user: dict = Depends(get_current_user),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    """Get ride history for current user or driver"""
    user_id = current_user.get("user_id") or current_user.get("id")
    user_type = current_user.get("role", "user")
    
    # Build query
    query = {}
    if user_type == "driver":
        query["driver_id"] = user_id
    else:
        query["user_id"] = user_id
    
    if status:
        query["status"] = status
    
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}
    
    # Get total count
    total = await db.rides.count_documents(query)
    
    # Get paginated rides
    skip = (page - 1) * limit
    rides = await db.rides.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich rides with user/driver info and ratings
    for ride in rides:
        if user_type == "driver" and ride.get("user_id"):
            user = await db.users.find_one({"id": ride["user_id"]}, {"_id": 0, "first_name": 1, "last_name": 1})
            ride["user_name"] = f"{user.get('first_name', '')} {user.get('last_name', '')}" if user else "Unknown"
        elif ride.get("driver_id"):
            driver = await db.drivers.find_one({"id": ride["driver_id"]}, {"_id": 0, "first_name": 1, "last_name": 1, "vehicle_plate": 1})
            ride["driver_name"] = f"{driver.get('first_name', '')} {driver.get('last_name', '')}" if driver else "Unknown"
            ride["vehicle_plate"] = driver.get("vehicle_plate") if driver else None
        
        # Get rating for this ride
        rating = await db.ratings.find_one({"ride_id": ride["id"]}, {"_id": 0})
        ride["rating"] = rating
    
    return {
        "rides": rides,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit) if limit > 0 else 0
    }

@router.get("/rides/{ride_id}")
async def get_ride_details(ride_id: str, current_user: dict = Depends(get_current_user)):
    """Get detailed ride information"""
    ride = await db.rides.find_one({"id": ride_id}, {"_id": 0})
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    # Get user info
    if ride.get("user_id"):
        user = await db.users.find_one({"id": ride["user_id"]}, {"_id": 0, "first_name": 1, "last_name": 1, "phone": 1})
        ride["user"] = user
    
    # Get driver info
    if ride.get("driver_id"):
        driver = await db.drivers.find_one({"id": ride["driver_id"]}, {"_id": 0, "first_name": 1, "last_name": 1, "phone": 1, "vehicle_plate": 1, "vehicle_type": 1})
        ride["driver"] = driver
    
    # Get rating
    rating = await db.ratings.find_one({"ride_id": ride_id}, {"_id": 0})
    ride["rating"] = rating
    
    return ride

# Ratings routes extracted to routes/ratings.py
# Chat routes extracted to routes/chat.py
