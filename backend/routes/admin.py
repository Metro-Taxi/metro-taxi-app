"""
Routes API pour l'administration, Stripe Connect, et gestion des trajets - Métro-Taxi
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel
import os
import logging
import uuid
import math
import stripe

from database import db
from models.schemas import RideRequestCreate, RideProgressUpdate, LocationUpdate, NotificationPayload
from services.auth import get_current_user
from services.emails import send_subscription_confirmation_email, send_gift_subscription_email, send_payout_notification_email

# Security middleware
from middleware.security import get_security_stats, manual_block_ip, manual_unblock_ip, get_client_ip

# Stripe config
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY

# Import config from server
from server import SUBSCRIPTION_PLANS, REGIONAL_PRICING, DRIVER_RATE_PER_KM, PAYOUT_DAY

def _get_manager():
    from server import manager
    return manager

router = APIRouter(prefix="/api", tags=["admin"])

# Admin Routes for Driver Payouts
@router.get("/admin/driver-earnings")
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

@router.post("/admin/process-payouts")
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

@router.get("/admin/payouts-history")
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

@router.get("/stripe-connect/config")
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

@router.post("/drivers/stripe-connect/create-account")
async def create_stripe_connect_account(request: Request, current_user: dict = Depends(get_current_user)):
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
                # Generate new onboarding link with dynamic origin
                origin = request.headers.get('origin', 'https://metro-taxi.com')
                account_link = stripe.AccountLink.create(
                    account=driver["stripe_account_id"],
                    refresh_url=f"{origin}/driver/stripe-refresh",
                    return_url=f"{origin}/driver/stripe-complete",
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
        
        # Create account onboarding link with dynamic origin
        origin = request.headers.get('origin', 'https://metro-taxi.com')
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url=f"{origin}/driver/stripe-refresh",
            return_url=f"{origin}/driver/stripe-complete",
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

@router.get("/drivers/stripe-connect/status")
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

@router.post("/admin/stripe-connect/process-payout/{driver_id}")
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

@router.post("/admin/stripe-connect/process-all-payouts")
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
@router.post("/rides/request")
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
    await _get_manager().send_personal_message({
        "type": "ride_request",
        "ride": {k: v for k, v in ride_doc.items()}
    }, data.driver_id)
    
    return {"ride": {k: v for k, v in ride_doc.items()}}

@router.get("/rides/pending")
async def get_pending_rides(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    rides = await db.ride_requests.find(
        {"driver_id": driver_id, "status": "pending"},
        {"_id": 0}
    ).to_list(100)
    
    return {"rides": rides}

@router.post("/rides/{ride_id}/accept")
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
    await _get_manager().send_personal_message({
        "type": "ride_accepted",
        "ride_id": ride_id
    }, ride["user_id"])
    
    return {"status": "accepted"}

@router.post("/rides/{ride_id}/reject")
async def reject_ride(ride_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Accès réservé aux chauffeurs")
    
    driver_id = current_user["user_id"]
    ride = await db.ride_requests.find_one({"id": ride_id, "driver_id": driver_id}, {"_id": 0})
    
    if not ride:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    await db.ride_requests.update_one({"id": ride_id}, {"$set": {"status": "rejected"}})
    
    # Notify user
    await _get_manager().send_personal_message({
        "type": "ride_rejected",
        "ride_id": ride_id
    }, ride["user_id"])
    
    return {"status": "rejected"}

@router.post("/rides/{ride_id}/complete")
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
    await _get_manager().send_personal_message({
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

@router.get("/rides/active")
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

@router.post("/rides/{ride_id}/progress")
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
    
    await _get_manager().send_personal_message({
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

@router.get("/rides/{ride_id}/tracking")
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
@router.post("/users/location")
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

# ============================================
# REGION MANAGEMENT ENDPOINTS
# ============================================
# NOTE: Region routes have been moved to routes/regions.py
# Imported via: from routes.regions import router as regions_router

# Admin Routes
@router.get("/admin/stats")
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

# ============================================
# SECURITY ADMIN ENDPOINTS
# ============================================

@router.get("/admin/security/stats")
async def get_admin_security_stats(current_user: dict = Depends(get_current_user)):
    """Get security statistics for admin dashboard"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    return get_security_stats()

@router.post("/admin/security/block-ip")
async def admin_block_ip(data: dict, current_user: dict = Depends(get_current_user)):
    """Manually block an IP address"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    ip = data.get("ip")
    duration = data.get("duration_minutes", 60)
    
    if not ip:
        raise HTTPException(status_code=400, detail="IP address required")
    
    manual_block_ip(ip, duration)
    return {"message": f"IP {ip} blocked for {duration} minutes", "success": True}

@router.post("/admin/security/unblock-ip")
async def admin_unblock_ip(data: dict, current_user: dict = Depends(get_current_user)):
    """Manually unblock an IP address"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    ip = data.get("ip")
    if not ip:
        raise HTTPException(status_code=400, detail="IP address required")
    
    success = manual_unblock_ip(ip)
    if success:
        return {"message": f"IP {ip} unblocked", "success": True}
    return {"message": f"IP {ip} was not blocked", "success": False}

@router.get("/admin/drivers")
async def get_all_drivers(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    drivers = await db.drivers.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return {"drivers": drivers}

@router.post("/admin/drivers/{driver_id}/validate")
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

@router.post("/admin/drivers/{driver_id}/deactivate")
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

@router.get("/admin/users")
async def get_all_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return {"users": users}

# Admin - Get user ride history
@router.get("/admin/user/{user_id}/rides")
async def get_user_ride_history(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get ride history for a specific user (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    # Get all rides for this user
    rides = await db.rides.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Enrich with driver names
    for ride in rides:
        if ride.get("driver_id"):
            driver = await db.drivers.find_one({"id": ride["driver_id"]}, {"_id": 0, "first_name": 1, "last_name": 1})
            if driver:
                ride["driver_name"] = f"{driver['first_name']} {driver['last_name']}"
    
    return {"rides": rides}

# Admin - Get subscription statistics
@router.get("/admin/subscriptions")
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
@router.post("/admin/subscriptions/cleanup")
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

# Admin - Gift a free subscription to a user
class GiftSubscriptionRequest(BaseModel):
    user_id: str
    plan_id: str  # "24h", "1week", "1month"
    reason: Optional[str] = None  # "promo_lancement", "geste_commercial", "parrainage", etc.

@router.post("/admin/subscriptions/gift")
async def gift_subscription(data: GiftSubscriptionRequest, current_user: dict = Depends(get_current_user)):
    """Gift a free subscription to a user (promotional or commercial gesture)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    # Validate plan
    if data.plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail=f"Plan invalide. Choisir parmi: {list(SUBSCRIPTION_PLANS.keys())}")
    
    plan = SUBSCRIPTION_PLANS[data.plan_id]
    
    # Find user
    user = await db.users.find_one({"id": data.user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Calculate expiration
    now = datetime.now(timezone.utc)
    
    # If user already has active subscription, extend it
    current_expires = None
    if user.get("subscription_active") and user.get("subscription_expires"):
        try:
            current_expires = datetime.fromisoformat(user["subscription_expires"])
            if current_expires > now:
                # Extend from current expiration
                new_expires = current_expires + timedelta(hours=plan["duration_hours"])
            else:
                new_expires = now + timedelta(hours=plan["duration_hours"])
        except (ValueError, TypeError):
            new_expires = now + timedelta(hours=plan["duration_hours"])
    else:
        new_expires = now + timedelta(hours=plan["duration_hours"])
    
    # Update user subscription
    await db.users.update_one(
        {"id": data.user_id},
        {"$set": {
            "subscription_active": True,
            "subscription_expires": new_expires.isoformat(),
            "subscription_plan": data.plan_id
        }}
    )
    
    # Log the gift in a collection for tracking
    gift_record = {
        "id": str(uuid.uuid4()),
        "user_id": data.user_id,
        "user_email": user.get("email"),
        "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
        "plan_id": data.plan_id,
        "plan_name": plan["name"],
        "plan_value": plan["price"],
        "reason": data.reason or "non_spécifié",
        "gifted_by": current_user["user_id"],
        "gifted_at": now.isoformat(),
        "expires_at": new_expires.isoformat()
    }
    await db.gift_subscriptions.insert_one(gift_record)
    
    # Send email notification to user
    if RESEND_API_KEY and user.get("email"):
        try:
            params = {
                "from": SENDER_EMAIL,
                "to": [user["email"]],
                "subject": "🎁 Abonnement offert - Métro-Taxi",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #09090B; color: white; padding: 30px; border-radius: 10px;">
                    <h1 style="color: #FFD60A; text-align: center;">🎁 ABONNEMENT OFFERT</h1>
                    <p>Bonjour {user.get('first_name', 'Cher client')},</p>
                    <p>Nous avons le plaisir de vous offrir un abonnement <strong style="color: #FFD60A;">{plan['name']}</strong> !</p>
                    <div style="background: #18181B; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                        <p style="margin: 0; font-size: 24px; color: #FFD60A; font-weight: bold;">{plan['name']}</p>
                        <p style="margin: 10px 0 0 0; color: #888;">Valeur: {plan['price']}€</p>
                        <p style="margin: 10px 0 0 0; color: #888;">Expire le: {new_expires.strftime('%d/%m/%Y à %H:%M')}</p>
                    </div>
                    <p>Profitez de trajets illimités dès maintenant !</p>
                    <p style="color: #888; font-size: 12px; margin-top: 30px;">L'équipe Métro-Taxi</p>
                </div>
                """
            }
            await asyncio.to_thread(resend.Emails.send, params)
            logging.info(f"Gift notification email sent to {user['email']}")
        except Exception as e:
            logging.warning(f"Failed to send gift notification email: {e}")
    
    return {
        "success": True,
        "message": f"Abonnement {plan['name']} offert à {user.get('email')}",
        "user_email": user.get("email"),
        "plan": plan["name"],
        "expires_at": new_expires.isoformat(),
        "extended": current_expires is not None and current_expires > now
    }

@router.get("/admin/subscriptions/gifts")
async def get_gift_history(current_user: dict = Depends(get_current_user)):
    """Get history of gifted subscriptions"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    gifts = await db.gift_subscriptions.find({}, {"_id": 0}).sort("gifted_at", -1).to_list(100)
    
    total_value = sum(g.get("plan_value", 0) for g in gifts)
    
    return {
        "gifts": gifts,
        "total_gifts": len(gifts),
        "total_value": total_value
    }

# Admin - Get all virtual cards
@router.get("/admin/cards")
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
@router.get("/admin/cards/{user_id}")
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
@router.get("/users/{user_id}/card")
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

