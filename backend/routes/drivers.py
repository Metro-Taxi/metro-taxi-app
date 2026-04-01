"""
Routes API pour les chauffeurs - Métro-Taxi
Gère : localisation, disponibilité, revenus, virements, Stripe Connect
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
import logging

# Imports locaux
from database import db
from models.schemas import LocationUpdate, BankInfoUpdate
from services.auth import get_current_user

router = APIRouter(prefix="/api", tags=["drivers"])

# Configuration - importée depuis server.py ou .env
DRIVER_RATE_PER_KM = 1.50
PAYOUT_DAY = 15


# ============================================
# LOCALISATION
# ============================================

@router.post("/drivers/location")
async def update_driver_location(data: LocationUpdate, current_user: dict = Depends(get_current_user)):
    """Mettre à jour la position du chauffeur"""
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
    
    # Broadcast via WebSocket (importé depuis server.py)
    try:
        from server import manager
        driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0, "password": 0})
        if driver and driver.get("is_active") and driver.get("is_validated"):
            await manager.broadcast_to_users({
                "type": "driver_location_update",
                "driver": driver
            })
    except ImportError:
        pass
    
    return {"status": "ok"}


@router.get("/drivers/available")
async def get_available_drivers(region_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Obtenir les chauffeurs disponibles, filtrable par région"""
    query = {"is_active": True, "is_validated": True, "location": {"$ne": None}}
    
    if region_id:
        query["region_id"] = region_id
    
    drivers = await db.drivers.find(query, {"_id": 0, "password": 0}).to_list(100)
    return {"drivers": drivers}


# ============================================
# STATUT ET PROFIL
# ============================================

@router.post("/drivers/toggle-active")
async def toggle_driver_active(current_user: dict = Depends(get_current_user)):
    """Activer/désactiver le statut du chauffeur"""
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
    
    if not driver:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    new_status = not driver.get("is_active", False)
    await db.drivers.update_one({"id": driver_id}, {"$set": {"is_active": new_status}})
    
    return {"is_active": new_status}


# ============================================
# INFORMATIONS BANCAIRES
# ============================================

@router.put("/drivers/bank-info")
async def update_driver_bank_info(data: BankInfoUpdate, current_user: dict = Depends(get_current_user)):
    """Mettre à jour les informations bancaires (IBAN + BIC)"""
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


@router.get("/drivers/bank-info")
async def get_driver_bank_info(current_user: dict = Depends(get_current_user)):
    """Obtenir les informations bancaires"""
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0, "iban": 1, "bic": 1})
    
    if not driver:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    return {"iban": driver.get("iban"), "bic": driver.get("bic")}


# ============================================
# REVENUS ET HISTORIQUE
# ============================================

@router.get("/drivers/earnings")
async def get_driver_earnings(current_user: dict = Depends(get_current_user)):
    """Obtenir le résumé des revenus du chauffeur"""
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    now = datetime.now(timezone.utc)
    current_month = now.strftime("%Y-%m")
    
    # Revenus du mois en cours
    current_earnings = await db.driver_earnings.find_one(
        {"driver_id": driver_id, "month": current_month},
        {"_id": 0}
    )
    
    # Historique des revenus
    earnings_cursor = db.driver_earnings.find(
        {"driver_id": driver_id},
        {"_id": 0}
    ).sort("month", -1).limit(12)
    
    earnings_history = await earnings_cursor.to_list(length=12)
    
    # Calcul des totaux
    total_km = sum(e.get("total_km", 0) for e in earnings_history)
    total_revenue = sum(e.get("total_revenue", 0) for e in earnings_history)
    total_rides = sum(e.get("rides_count", 0) for e in earnings_history)
    
    # Virements en attente
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


@router.get("/drivers/earnings/history")
async def get_driver_earnings_history(current_user: dict = Depends(get_current_user)):
    """Obtenir l'historique détaillé des revenus"""
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    
    rides_cursor = db.ride_requests.find(
        {"driver_id": driver_id, "status": "completed", "driver_revenue": {"$exists": True}},
        {"_id": 0, "id": 1, "user_name": 1, "completed_at": 1, "total_km": 1, "driver_revenue": 1, "pickup_km": 1, "ride_km": 1}
    ).sort("completed_at", -1).limit(50)
    
    rides = await rides_cursor.to_list(length=50)
    
    return {"rides": rides}


@router.get("/drivers/payouts")
async def get_driver_payouts(current_user: dict = Depends(get_current_user)):
    """Obtenir l'historique des virements"""
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    
    payouts_cursor = db.driver_payouts.find(
        {"driver_id": driver_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(24)
    
    payouts = await payouts_cursor.to_list(length=24)
    
    return {"payouts": payouts}
