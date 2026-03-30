"""
Routes API pour la gestion des régions
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional

# Imports locaux
from database import db
from models.schemas import RegionCreate
from services.auth import get_current_user

router = APIRouter(prefix="/api", tags=["regions"])


# ============================================
# HELPER FUNCTIONS
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


# ============================================
# PUBLIC ROUTES
# ============================================

@router.get("/regions")
async def get_all_regions():
    """Get all regions (public endpoint for region selection)"""
    regions = await db.regions.find({}, {"_id": 0}).to_list(100)
    
    # Add driver and user counts
    for region in regions:
        region['driver_count'] = await db.drivers.count_documents({"region_id": region['id']})
        region['user_count'] = await db.users.count_documents({"subscriptions.region_id": region['id']})
    
    return regions


@router.get("/regions/active")
async def get_active_regions():
    """Get only active regions (for public use)"""
    regions = await db.regions.find({"is_active": True}, {"_id": 0}).to_list(100)
    return regions


@router.get("/regions/detect")
async def detect_region(lat: float, lng: float):
    """Detect region based on coordinates"""
    region = await detect_region_by_location(lat, lng)
    if region:
        return {"detected": True, "region": region}
    return {"detected": False, "region": None, "message": "No active region found for this location"}


@router.get("/regions/{region_id}")
async def get_region(region_id: str):
    """Get a specific region by ID"""
    region = await db.regions.find_one({"id": region_id}, {"_id": 0})
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    region['driver_count'] = await db.drivers.count_documents({"region_id": region_id})
    region['user_count'] = await db.users.count_documents({"subscriptions.region_id": region_id})
    return region


# ============================================
# ADMIN ROUTES
# ============================================

@router.post("/admin/regions")
async def create_region(region: RegionCreate, current_user: dict = Depends(get_current_user)):
    """Create a new region (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if region already exists
    existing = await db.regions.find_one({"id": region.id})
    if existing:
        raise HTTPException(status_code=400, detail="Region with this ID already exists")
    
    region_data = {
        "id": region.id.lower(),
        "name": region.name,
        "country": region.country.upper(),
        "currency": region.currency.upper(),
        "language": region.language.lower(),
        "timezone": region.timezone,
        "bounds": region.bounds.model_dump(),
        "is_active": region.is_active,
        "launch_date": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.regions.insert_one(region_data)
    return {"status": "created", "region": {k: v for k, v in region_data.items() if k != "_id"}}


@router.put("/admin/regions/{region_id}")
async def update_region(region_id: str, region: RegionCreate, current_user: dict = Depends(get_current_user)):
    """Update a region (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    existing = await db.regions.find_one({"id": region_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Region not found")
    
    update_data = {
        "name": region.name,
        "country": region.country.upper(),
        "currency": region.currency.upper(),
        "language": region.language.lower(),
        "timezone": region.timezone,
        "bounds": region.bounds.model_dump(),
        "is_active": region.is_active
    }
    
    await db.regions.update_one({"id": region_id}, {"$set": update_data})
    return {"status": "updated"}


@router.post("/admin/regions/{region_id}/activate")
async def activate_region(region_id: str, current_user: dict = Depends(get_current_user)):
    """Activate a region (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.regions.update_one(
        {"id": region_id},
        {"$set": {"is_active": True, "launch_date": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Region not found")
    
    return {"status": "activated", "launch_date": datetime.now(timezone.utc).isoformat()}


@router.post("/admin/regions/{region_id}/deactivate")
async def deactivate_region(region_id: str, current_user: dict = Depends(get_current_user)):
    """Deactivate a region (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.regions.update_one(
        {"id": region_id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Region not found")
    
    return {"status": "deactivated"}


@router.delete("/admin/regions/{region_id}")
async def delete_region(region_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a region (admin only) - only if no drivers/users"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if region has drivers
    driver_count = await db.drivers.count_documents({"region_id": region_id})
    if driver_count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete region with {driver_count} drivers")
    
    result = await db.regions.delete_one({"id": region_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Region not found")
    
    return {"status": "deleted"}


@router.get("/admin/regions/stats")
async def get_regions_stats(current_user: dict = Depends(get_current_user)):
    """Get statistics for all regions (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    regions = await db.regions.find({}, {"_id": 0}).to_list(100)
    stats = []
    
    for region in regions:
        region_id = region['id']
        driver_count = await db.drivers.count_documents({"region_id": region_id})
        validated_drivers = await db.drivers.count_documents({"region_id": region_id, "is_validated": True})
        active_drivers = await db.drivers.count_documents({"region_id": region_id, "is_active": True})
        
        # Count users with active subscription in this region
        pipeline = [
            {"$match": {"subscriptions": {"$elemMatch": {"region_id": region_id, "is_active": True}}}},
            {"$count": "count"}
        ]
        result = await db.users.aggregate(pipeline).to_list(1)
        active_subscribers = result[0]['count'] if result else 0
        
        # Count active rides in this region
        active_rides = await db.ride_requests.count_documents({
            "status": "accepted",
            "region_id": region_id
        })
        
        stats.append({
            "region": region,
            "stats": {
                "total_drivers": driver_count,
                "validated_drivers": validated_drivers,
                "active_drivers": active_drivers,
                "active_subscribers": active_subscribers,
                "active_rides": active_rides
            }
        })
    
    return stats
