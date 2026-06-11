"""
Auto-attribution campaigns — Métro-Taxi.

Mécanique "1ère course offerte aux N premiers ABONNÉS d'une zone pilote" :
- Plus de codes promo papier à gérer
- Compteur atomique des places restantes (race-condition-safe via $inc)
- Trigger automatique : à l'activation d'un abonnement, si l'usager est éligible
  (campagne active + places restantes + valid_from atteint) → crédit auto-attribué

Différence avec promo_codes.py :
- promo_codes = système classique 1 code = 1 personne (utilisable pour campagnes futures)
- auto_campaigns = système "premier abonné, premier servi" sans code à distribuer
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from database import db
from services.auth import get_current_user

router = APIRouter(prefix="/api", tags=["auto_campaigns"])

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class CreateAutoCampaignRequest(BaseModel):
    campaign_id: str = Field(..., min_length=4, max_length=60, description="ID lisible (ex: saint-denis-2026-06-13)")
    name: str = Field(..., min_length=2, max_length=100, description="Nom affiché (ex: Saint-Denis Pionniers)")
    region: str = Field("saint-denis", description="Zone géographique")
    max_slots: int = Field(30, ge=1, le=10000, description="Nombre de bénéficiaires max")
    benefit_type: str = Field("free_first_ride", description="Type d'avantage")
    max_distance_km: float = Field(10.0, gt=0, le=50)
    valid_from: str = Field(..., description="ISO datetime — crédit consommable à partir de cette date")
    expires_at: str = Field(..., description="ISO datetime — campagne et crédits expirent à cette date")


# -----------------------------------------------------------------------------
# Public endpoints (no auth)
# -----------------------------------------------------------------------------
@router.get("/campaigns/{campaign_id}/status")
async def get_campaign_status(campaign_id: str):
    """Public: retourne l'état de la campagne (places restantes, etc.).

    Utilisé par la landing /saint-denis pour afficher le compteur live.
    """
    camp = await db.auto_campaigns.find_one({"campaign_id": campaign_id}, {"_id": 0})
    if not camp:
        raise HTTPException(status_code=404, detail="Campagne introuvable")

    now = datetime.now(timezone.utc)
    expires_dt = datetime.fromisoformat(camp["expires_at"].replace("Z", "+00:00"))

    slots_used = camp.get("slots_used", 0)
    slots_total = camp["max_slots"]
    slots_remaining = max(0, slots_total - slots_used)

    return {
        "campaign_id": camp["campaign_id"],
        "name": camp["name"],
        "region": camp.get("region"),
        "slots_total": slots_total,
        "slots_used": slots_used,
        "slots_remaining": slots_remaining,
        "max_distance_km": camp["max_distance_km"],
        "benefit_type": camp.get("benefit_type", "free_first_ride"),
        "valid_from": camp["valid_from"],
        "expires_at": camp["expires_at"],
        "active": (
            slots_remaining > 0
            and now <= expires_dt
            and camp.get("active", True)
        ),
        "consumable_from_iso": camp["valid_from"],
        "expired": now > expires_dt,
    }


# -----------------------------------------------------------------------------
# Admin endpoints
# -----------------------------------------------------------------------------
@router.post("/admin/campaigns/auto/create")
async def create_auto_campaign(
    data: CreateAutoCampaignRequest,
    current_user: dict = Depends(get_current_user),
):
    """Admin: crée une nouvelle campagne d'auto-attribution.

    Compteur de places initialisé à 0. Sera incrémenté atomiquement à chaque
    attribution lors de souscription d'abonnement (cf. attempt_auto_attribution).
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    # Validation dates
    try:
        valid_from_dt = datetime.fromisoformat(data.valid_from.replace("Z", "+00:00"))
        expires_dt = datetime.fromisoformat(data.expires_at.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Format de date invalide (ISO 8601 requis)")
    if expires_dt <= valid_from_dt:
        raise HTTPException(status_code=400, detail="expires_at doit être postérieur à valid_from")

    # Unicité campaign_id
    existing = await db.auto_campaigns.find_one({"campaign_id": data.campaign_id})
    if existing:
        raise HTTPException(status_code=409, detail="Une campagne avec cet ID existe déjà")

    now = datetime.now(timezone.utc)
    doc = {
        "id": str(uuid.uuid4()),
        "campaign_id": data.campaign_id,
        "name": data.name,
        "region": data.region,
        "max_slots": data.max_slots,
        "slots_used": 0,
        "benefit_type": data.benefit_type,
        "max_distance_km": data.max_distance_km,
        "valid_from": valid_from_dt.isoformat(),
        "expires_at": expires_dt.isoformat(),
        "active": True,
        "created_at": now.isoformat(),
        "created_by": current_user.get("user_id"),
    }
    await db.auto_campaigns.insert_one(doc)
    doc.pop("_id", None)
    return {"status": "ok", "campaign": doc}


@router.get("/admin/campaigns/auto")
async def list_auto_campaigns(current_user: dict = Depends(get_current_user)):
    """Admin: liste toutes les campagnes auto-attribution avec stats."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    campaigns = await db.auto_campaigns.find({}, {"_id": 0}).sort("created_at", -1).to_list(length=200)
    # Pour chaque campagne, compte les bénéficiaires effectifs (sécurité contre désync)
    for c in campaigns:
        actual = await db.users.count_documents(
            {"pending_promo.campaign": c["campaign_id"]}
        )
        consumed = await db.users.count_documents(
            {"used_promo_campaigns": c["campaign_id"]}
        )
        c["actual_pending"] = actual
        c["consumed"] = consumed
    return {"campaigns": campaigns}


@router.post("/admin/campaigns/auto/{campaign_id}/close")
async def close_auto_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Admin: clôture manuellement une campagne (active = false)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    result = await db.auto_campaigns.update_one(
        {"campaign_id": campaign_id},
        {"$set": {"active": False, "closed_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    return {"status": "ok"}


async def attempt_auto_attribution(user_id: str, campaign_id: str) -> Optional[dict]:
    """Tente d'attribuer un crédit "1ère course offerte" à un usager qui vient
    d'activer un abonnement, s'il fait partie d'une campagne auto-attribution active.

    Race-condition-safe : utilise `find_one_and_update` avec condition `slots_used < max_slots`
    pour garantir qu'on ne dépasse jamais le quota.

    Args:
        user_id: ID de l'usager qui vient de s'abonner
        campaign_id: ID de la campagne signup (provenant de l'URL ?campaign=)

    Returns:
        dict avec les infos du crédit attribué, ou None si pas éligible.
    """
    if not campaign_id:
        return None

    now = datetime.now(timezone.utc)

    # Vérifie que l'usager existe et n'a pas déjà bénéficié
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        return None
    if user.get("pending_promo"):
        # Crédit déjà actif → on ne réattribue pas (idempotent)
        return None
    if campaign_id in (user.get("used_promo_campaigns") or []):
        # L'usager a déjà consommé sa course offerte pour cette campagne
        return None

    # Incrémente atomiquement slots_used SI < max_slots ET campagne active ET non expirée
    updated = await db.auto_campaigns.find_one_and_update(
        {
            "campaign_id": campaign_id,
            "active": True,
            "$expr": {"$lt": ["$slots_used", "$max_slots"]},
            "expires_at": {"$gt": now.isoformat()},
        },
        {"$inc": {"slots_used": 1}},
        return_document=True,
    )
    if not updated:
        # Soit campagne inexistante, soit complète, soit expirée
        return None

    # Attribue le crédit "pending_promo" à l'usager
    pending_promo = {
        "code": f"AUTO-{campaign_id.upper()}-{updated['slots_used']:03d}",
        "type": updated.get("benefit_type", "free_first_ride"),
        "max_distance_km": updated["max_distance_km"],
        "valid_from": updated["valid_from"],
        "expires_at": updated["expires_at"],
        "region": updated.get("region"),
        "campaign": updated["campaign_id"],
        "slot_number": updated["slots_used"],
        "redeemed_at": now.isoformat(),
        "source": "auto_campaign",
    }
    await db.users.update_one({"id": user_id}, {"$set": {"pending_promo": pending_promo}})

    logging.info(
        f"🎁 Auto-attribution campaign={campaign_id} slot={updated['slots_used']}/{updated['max_slots']} user={user_id}"
    )
    return pending_promo


# -----------------------------------------------------------------------------
# HELPER — Auto-attribution par RÉGION (fallback si pas de signup_campaign)
# -----------------------------------------------------------------------------
async def auto_attribute_for_region(user_id: str, region_id: str) -> Optional[dict]:
    """Cherche une campagne auto-attribution active pour cette région et tente
    l'attribution. Permet aux flyers/posts sans lien magique de fonctionner :
    n'importe qui s'abonnant sur cette région reçoit le cadeau si places dispo.

    Args:
        user_id: usager qui vient d'activer un abo
        region_id: id de la région de l'abo (ex: "paris", "saint-denis")

    Returns:
        dict du pending_promo si attribué, sinon None.
    """
    if not region_id:
        return None

    # Cherche la campagne active matching cette région
    # Une zone "saint-denis" est conceptuellement dans la région "paris" (Île-de-France).
    # On accepte donc :
    #  - match exact (region == region_id)
    #  - match parent : campagnes "saint-denis-*" pour les usagers Paris/Île-de-France
    now = datetime.now(timezone.utc)
    candidate_regions = {region_id}
    if region_id in ("paris", "ile-de-france", "idf"):
        candidate_regions.add("saint-denis")

    camp = await db.auto_campaigns.find_one(
        {
            "region": {"$in": list(candidate_regions)},
            "active": True,
            "$expr": {"$lt": ["$slots_used", "$max_slots"]},
            "expires_at": {"$gt": now.isoformat()},
        },
        {"_id": 0, "campaign_id": 1},
        sort=[("created_at", -1)],  # la plus récente d'abord
    )
    if not camp:
        return None

    return await attempt_auto_attribution(user_id, camp["campaign_id"])
