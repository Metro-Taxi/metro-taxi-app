"""
Routes API pour le système de notation - Métro-Taxi
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid

from database import db
from models.schemas import RatingCreate, NotificationPayload
from services.auth import get_current_user

router = APIRouter(prefix="/api", tags=["ratings"])


@router.post("/ratings")
async def create_rating(rating: RatingCreate, current_user: dict = Depends(get_current_user)):
    """Create a rating for a completed ride"""
    user_id = current_user.get("user_id") or current_user.get("id")

    ride = await db.rides.find_one({"id": rating.ride_id})
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    if ride.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Can only rate completed rides")
    if ride.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="You can only rate your own rides")

    existing = await db.ratings.find_one({"ride_id": rating.ride_id})
    if existing:
        raise HTTPException(status_code=400, detail="Ride already rated")

    rating_doc = {
        "id": str(uuid.uuid4()),
        "ride_id": rating.ride_id,
        "user_id": user_id,
        "driver_id": rating.driver_id,
        "rating": rating.rating,
        "comment": rating.comment,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.ratings.insert_one(rating_doc)

    await _update_driver_average_rating(rating.driver_id)

    # Send notification to driver
    try:
        from routes.notifications import send_push_notification
        await send_push_notification(
            rating.driver_id,
            NotificationPayload(
                title="Nouvelle note reçue",
                body=f"Vous avez reçu une note de {rating.rating} étoiles",
                data={"type": "rating", "ride_id": rating.ride_id}
            ),
            "driver"
        )
    except ImportError:
        pass

    return {"success": True, "rating_id": rating_doc["id"]}


async def _update_driver_average_rating(driver_id: str):
    """Update driver's average rating"""
    pipeline = [
        {"$match": {"driver_id": driver_id}},
        {"$group": {"_id": "$driver_id", "average_rating": {"$avg": "$rating"}, "total_ratings": {"$sum": 1}}}
    ]
    result = await db.ratings.aggregate(pipeline).to_list(1)
    if result:
        await db.drivers.update_one(
            {"id": driver_id},
            {"$set": {"average_rating": round(result[0]["average_rating"], 2), "total_ratings": result[0]["total_ratings"]}}
        )


@router.get("/ratings/driver/{driver_id}")
async def get_driver_ratings(driver_id: str, page: int = 1, limit: int = 10):
    """Get ratings for a specific driver"""
    skip = (page - 1) * limit
    ratings = await db.ratings.find({"driver_id": driver_id}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    for r in ratings:
        user = await db.users.find_one({"id": r["user_id"]}, {"_id": 0, "first_name": 1, "last_name": 1})
        r["user_name"] = f"{user.get('first_name', '')} {user.get('last_name', '')[0]}." if user else "Anonymous"

    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0, "average_rating": 1, "total_ratings": 1})
    return {
        "ratings": ratings,
        "average_rating": driver.get("average_rating", 0) if driver else 0,
        "total_ratings": driver.get("total_ratings", 0) if driver else 0
    }


@router.get("/ratings/pending")
async def get_pending_ratings(current_user: dict = Depends(get_current_user)):
    """Get rides that haven't been rated yet by the user"""
    user_id = current_user.get("user_id") or current_user.get("id")

    completed_rides = await db.rides.find({"user_id": user_id, "status": "completed"}, {"_id": 0, "id": 1}).to_list(100)
    ride_ids = [r["id"] for r in completed_rides]

    rated_rides = await db.ratings.find({"ride_id": {"$in": ride_ids}}, {"_id": 0, "ride_id": 1}).to_list(100)
    rated_ids = {r["ride_id"] for r in rated_rides}
    unrated_ids = [rid for rid in ride_ids if rid not in rated_ids]

    if not unrated_ids:
        return {"pending_ratings": []}

    pending = await db.rides.find({"id": {"$in": unrated_ids}}, {"_id": 0}).sort("completed_at", -1).limit(5).to_list(5)

    for ride in pending:
        if ride.get("driver_id"):
            driver = await db.drivers.find_one({"id": ride["driver_id"]}, {"_id": 0, "first_name": 1, "last_name": 1, "vehicle_plate": 1})
            ride["driver_name"] = f"{driver.get('first_name', '')} {driver.get('last_name', '')}" if driver else "Unknown"
            ride["vehicle_plate"] = driver.get("vehicle_plate") if driver else None

    return {"pending_ratings": pending}
