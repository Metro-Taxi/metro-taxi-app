"""
Routes Partenariat Patron VTC (B2B) — Métro-Taxi

Permet à un patron de flotte VTC de soumettre une demande
de partenariat B2B depuis la page publique /patron-vtc.

- POST /api/fleet-partnerships/apply : Soumet une demande (public, sans auth)
- GET  /api/admin/fleet-partnerships : Liste admin
- POST /api/admin/fleet-partnerships/{id}/status : Marque comme contacté / accepté / rejeté
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from database import db
from services.emails import (
    send_fleet_partnership_alert,
    send_fleet_partnership_confirmation,
)
from server import get_current_user

router = APIRouter(prefix="/api", tags=["fleet-partnerships"])


class FleetPartnershipApplication(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    company_name: Optional[str] = Field(None, max_length=200)
    email: EmailStr
    phone: str = Field(..., min_length=5, max_length=30)
    fleet_size: int = Field(..., ge=1, le=10000)
    city: str = Field(..., min_length=2, max_length=120)
    message: Optional[str] = Field(None, max_length=2000)


class FleetPartnershipStatusUpdate(BaseModel):
    status: str  # 'new', 'contacted', 'accepted', 'rejected'
    notes: Optional[str] = Field(None, max_length=2000)


ALLOWED_STATUSES = {"new", "contacted", "accepted", "rejected"}


@router.post("/fleet-partnerships/apply")
async def submit_fleet_partnership(data: FleetPartnershipApplication, request: Request):
    """Public endpoint — un patron VTC soumet sa demande de partenariat."""
    # Anti-doublon : si une demande pending existe déjà pour le même email dans les 24h, on rejette
    now = datetime.now(timezone.utc)
    recent = await db.fleet_partnerships.find_one({
        "email": data.email.lower(),
        "status": {"$in": ["new", "contacted"]},
    }, {"_id": 0})
    if recent:
        raise HTTPException(
            status_code=409,
            detail="Une demande est déjà en cours pour cet email. Nous vous recontactons sous peu."
        )

    application_id = str(uuid.uuid4())
    # Capture IP client pour traçabilité (best-effort)
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    if "," in (client_ip or ""):
        client_ip = client_ip.split(",")[0].strip()

    doc = {
        "id": application_id,
        "full_name": data.full_name.strip(),
        "company_name": (data.company_name or "").strip() or None,
        "email": data.email.lower(),
        "phone": data.phone.strip(),
        "fleet_size": data.fleet_size,
        "city": data.city.strip(),
        "message": (data.message or "").strip() or None,
        "status": "new",
        "client_ip": client_ip,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "notes": None,
    }
    await db.fleet_partnerships.insert_one(doc)

    # Email fondateur (alerte) — best-effort
    try:
        await send_fleet_partnership_alert(doc)
    except Exception as e:
        logging.error(f"Fleet alert email failed: {e}")

    # Email confirmation au patron VTC — best-effort
    try:
        await send_fleet_partnership_confirmation(doc["email"], doc["full_name"], doc["fleet_size"])
    except Exception as e:
        logging.error(f"Fleet confirmation email failed: {e}")

    return {
        "status": "submitted",
        "application_id": application_id,
        "message": "Demande reçue. Nous vous recontactons sous 48h.",
    }


@router.get("/admin/fleet-partnerships")
async def admin_list_fleet_partnerships(current_user: dict = Depends(get_current_user)):
    """Admin : liste de toutes les demandes de partenariat flotte."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    applications = await db.fleet_partnerships.find({}, {"_id": 0}).sort("created_at", -1).to_list(length=500)

    # Stats rapides
    total = len(applications)
    by_status = {}
    total_fleet_size = 0
    for app in applications:
        by_status[app["status"]] = by_status.get(app["status"], 0) + 1
        total_fleet_size += int(app.get("fleet_size", 0))

    return {
        "applications": applications,
        "total": total,
        "by_status": by_status,
        "total_fleet_size": total_fleet_size,
    }


@router.post("/admin/fleet-partnerships/{application_id}/status")
async def admin_update_fleet_partnership_status(
    application_id: str,
    data: FleetPartnershipStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Admin : met à jour le statut d'une demande (contacté, accepté, rejeté)."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    if data.status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Statut invalide. Valides : {sorted(ALLOWED_STATUSES)}",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    update = {"status": data.status, "updated_at": now_iso}
    if data.notes is not None:
        update["notes"] = data.notes.strip()
    if data.status == "contacted":
        update["contacted_at"] = now_iso

    result = await db.fleet_partnerships.update_one(
        {"id": application_id},
        {"$set": update},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    return {"status": "updated", "application_id": application_id, "new_status": data.status}
