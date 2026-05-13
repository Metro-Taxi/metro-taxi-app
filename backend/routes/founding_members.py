"""
Routes Membre Fondateur — Métro-Taxi
- POST /api/founding-members/join : Un usager existant rejoint la liste VIP (tarif 53,99€/mois verrouillé à vie)
- GET  /api/founding-members/stats : Compteur public (progression chauffeurs vers 150)
- GET  /api/founding-members/me : Statut de l'usager connecté
- GET  /api/admin/founding-members : Liste admin
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import db
from services.emails import send_founding_member_welcome

# We reuse the auth dependency from server.py
from server import get_current_user

router = APIRouter(prefix="/api", tags=["founding-members"])

# Target number of drivers before subscriptions open publicly
TARGET_DRIVERS_FOR_LAUNCH = 150
# Locked-in price for founding members (in cents)
FOUNDING_MEMBER_PRICE_CENTS = 5399  # 53.99€


# ============================================
# PUBLIC — GET /api/founding-members/stats
# ============================================
@router.get("/founding-members/stats")
async def founding_members_stats():
    """Public stats — used by the landing page progress bar."""
    drivers_count = await db.drivers.count_documents({})
    members_count = await db.users.count_documents({"is_founding_member": True})
    progress_pct = round((drivers_count / TARGET_DRIVERS_FOR_LAUNCH) * 100, 1)
    return {
        "drivers_count": drivers_count,
        "target_drivers": TARGET_DRIVERS_FOR_LAUNCH,
        "progress_pct": min(progress_pct, 100),
        "founding_members_count": members_count,
        "launch_unlocked": drivers_count >= TARGET_DRIVERS_FOR_LAUNCH,
        "locked_price_eur": FOUNDING_MEMBER_PRICE_CENTS / 100,
    }


# ============================================
# POST /api/founding-members/join
# Authenticated user → joins the VIP list
# ============================================
@router.post("/founding-members/join")
async def join_founding_members(current_user: dict = Depends(get_current_user)):
    """An existing authenticated user joins the Membre Fondateur VIP waitlist."""
    if current_user["role"] != "user":
        raise HTTPException(status_code=403, detail="Réservé aux abonnés Métro-Taxi")

    user_id = current_user["user_id"]
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if user.get("is_founding_member"):
        return {
            "status": "already_member",
            "founding_member_number": user.get("founding_member_number"),
            "message": "Tu es déjà Membre Fondateur",
        }

    # Assign next founding member number
    last = await db.users.find_one(
        {"founding_member_number": {"$exists": True}},
        sort=[("founding_member_number", -1)],
        projection={"_id": 0, "founding_member_number": 1},
    )
    next_number = (last.get("founding_member_number", 0) + 1) if last else 1

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.users.update_one(
        {"id": user_id},
        {
            "$set": {
                "is_founding_member": True,
                "founding_member_number": next_number,
                "founding_member_joined_at": now_iso,
                "founding_member_locked_price_cents": FOUNDING_MEMBER_PRICE_CENTS,
            }
        },
    )

    # Send welcome email (best-effort, non-blocking on failure)
    try:
        drivers_count = await db.drivers.count_documents({})
        await send_founding_member_welcome(
            email=user["email"],
            name=f"{user.get('first_name','')} {user.get('last_name','')}".strip(),
            founding_number=next_number,
            total_drivers=drivers_count,
            target_drivers=TARGET_DRIVERS_FOR_LAUNCH,
        )
    except Exception as e:
        logging.error(f"Welcome email failed for member #{next_number}: {e}")

    return {
        "status": "joined",
        "founding_member_number": next_number,
        "locked_price_cents": FOUNDING_MEMBER_PRICE_CENTS,
        "joined_at": now_iso,
        "message": f"🏆 Bienvenue Membre Fondateur #{next_number} ! Tarif 53,99€/mois verrouillé à vie.",
    }


# ============================================
# GET /api/founding-members/me
# ============================================
@router.get("/founding-members/me")
async def my_founding_status(current_user: dict = Depends(get_current_user)):
    """Get the current user's founding member status."""
    if current_user["role"] != "user":
        return {"is_founding_member": False}

    user = await db.users.find_one(
        {"id": current_user["user_id"]},
        {"_id": 0, "is_founding_member": 1, "founding_member_number": 1,
         "founding_member_joined_at": 1, "founding_member_locked_price_cents": 1},
    )
    if not user:
        return {"is_founding_member": False}

    return {
        "is_founding_member": user.get("is_founding_member", False),
        "founding_member_number": user.get("founding_member_number"),
        "joined_at": user.get("founding_member_joined_at"),
        "locked_price_cents": user.get("founding_member_locked_price_cents", FOUNDING_MEMBER_PRICE_CENTS),
    }


# ============================================
# ADMIN — GET /api/admin/founding-members
# ============================================
@router.get("/admin/founding-members")
async def admin_list_founding_members(current_user: dict = Depends(get_current_user)):
    """Admin list of all founding members, sorted by founding_member_number."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    members = await db.users.find(
        {"is_founding_member": True},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1, "phone": 1,
         "founding_member_number": 1, "founding_member_joined_at": 1,
         "founding_member_locked_price_cents": 1, "created_at": 1, "subscription_active": 1},
    ).sort("founding_member_number", 1).to_list(length=1000)

    return {
        "members": members,
        "total": len(members),
        "target_drivers": TARGET_DRIVERS_FOR_LAUNCH,
    }
