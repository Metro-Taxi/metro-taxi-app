"""
Promo codes routes — Métro-Taxi.

Mécanique : "1ère course offerte ≤ N km" (campagne Saint-Denis 13 juin 2026).
- Admin génère N codes uniques au format `{PREFIX}-2026-XXXX`.
- Usager redeem son code → flag `pending_promo` sur son profil.
- Au /rides/request : si pending_promo et distance ≤ max_distance_km → bypass abonnement, course offerte par la plateforme.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
import secrets
import string
import uuid
import logging
import io
import os

import qrcode

from database import db
from services.auth import get_current_user

router = APIRouter(prefix="/api", tags=["promo_codes"])

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class GeneratePromoCodesRequest(BaseModel):
    campaign: str = Field(..., min_length=2, max_length=40, description="Identifiant campagne (ex: saint-denis-2026-06-13)")
    prefix: str = Field("STDENIS", min_length=2, max_length=20, description="Prefix code (ex: STDENIS)")
    count: int = Field(30, ge=1, le=500)
    max_distance_km: float = Field(10.0, gt=0, le=50)
    expires_at: str = Field(..., description="ISO date d'expiration des codes")
    region: Optional[str] = Field("saint-denis", description="Zone géographique cible")


class RedeemPromoCodeRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=40)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _generate_code(prefix: str) -> str:
    """Génère un code unique au format PREFIX-2026-XXXX (4 caractères alphanumériques sécurisés)."""
    alphabet = string.ascii_uppercase + string.digits
    # Éviter les caractères ambigus (0, O, I, 1)
    alphabet = alphabet.replace("0", "").replace("O", "").replace("I", "").replace("1", "")
    suffix = "".join(secrets.choice(alphabet) for _ in range(4))
    return f"{prefix.upper()}-2026-{suffix}"


def _serialize_promo(p: dict) -> dict:
    return {k: v for k, v in p.items() if k != "_id"}


# -----------------------------------------------------------------------------
# ADMIN ROUTES
# -----------------------------------------------------------------------------
@router.post("/admin/promo-codes/generate")
async def generate_promo_codes(
    data: GeneratePromoCodesRequest,
    current_user: dict = Depends(get_current_user)
):
    """Admin: génère N codes promo uniques pour une campagne."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    # Validation date expiration
    try:
        expires_dt = datetime.fromisoformat(data.expires_at.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Format expires_at invalide (ISO 8601)")
    if expires_dt < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="La date d'expiration doit être dans le futur")

    now = datetime.now(timezone.utc)
    generated = []
    attempts = 0
    max_attempts = data.count * 10  # safety net pour les collisions

    while len(generated) < data.count and attempts < max_attempts:
        attempts += 1
        code = _generate_code(data.prefix)
        # Vérifie l'unicité
        existing = await db.promo_codes.find_one({"code": code})
        if existing:
            continue
        doc = {
            "id": str(uuid.uuid4()),
            "code": code,
            "type": "free_first_ride",
            "campaign": data.campaign,
            "region": data.region,
            "max_distance_km": data.max_distance_km,
            "expires_at": expires_dt.isoformat(),
            "used": False,
            "used_by": None,
            "used_at": None,
            "redeemed_at": None,
            "consumed_at": None,
            "ride_id": None,
            "platform_cost_eur": None,
            "created_at": now.isoformat(),
            "created_by": current_user.get("user_id"),
        }
        await db.promo_codes.insert_one(doc)
        generated.append(_serialize_promo(doc))

    if len(generated) < data.count:
        logging.warning(f"Promo code generation: only {len(generated)}/{data.count} created (collisions)")

    return {
        "status": "ok",
        "generated_count": len(generated),
        "requested_count": data.count,
        "codes": generated,
    }


@router.get("/admin/promo-codes")
async def list_promo_codes(
    campaign: Optional[str] = None,
    used: Optional[bool] = None,
    limit: int = 200,
    current_user: dict = Depends(get_current_user),
):
    """Admin: liste les codes promo avec filtres optionnels."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    q: dict = {}
    if campaign:
        q["campaign"] = campaign
    if used is not None:
        q["used"] = used

    cursor = db.promo_codes.find(q, {"_id": 0}).sort("created_at", -1).limit(limit)
    codes = await cursor.to_list(length=limit)

    total = await db.promo_codes.count_documents(q)
    used_count = await db.promo_codes.count_documents({**q, "used": True})

    return {
        "total": total,
        "used_count": used_count,
        "available_count": total - used_count,
        "codes": codes,
    }


@router.get("/admin/promo-codes/stats")
async def promo_codes_stats(current_user: dict = Depends(get_current_user)):
    """Admin: stats globales codes promo + courses offertes consommées."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    pipeline = [
        {
            "$group": {
                "_id": "$campaign",
                "total": {"$sum": 1},
                "used": {"$sum": {"$cond": ["$used", 1, 0]}},
                "consumed": {"$sum": {"$cond": [{"$ne": ["$consumed_at", None]}, 1, 0]}},
                "platform_cost_eur": {"$sum": {"$ifNull": ["$platform_cost_eur", 0]}},
            }
        }
    ]
    by_campaign = await db.promo_codes.aggregate(pipeline).to_list(length=100)
    return {
        "by_campaign": [
            {
                "campaign": row["_id"],
                "total": row["total"],
                "used": row["used"],
                "consumed": row["consumed"],
                "platform_cost_eur": round(row.get("platform_cost_eur", 0) or 0, 2),
            }
            for row in by_campaign
        ]
    }


# -----------------------------------------------------------------------------
# USER ROUTES
# -----------------------------------------------------------------------------
@router.post("/promo-codes/redeem")
async def redeem_promo_code(
    data: RedeemPromoCodeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Usager: valide un code promo et active le crédit `pending_promo` sur son profil.

    1 code = 1 usager = 1 course offerte (plafonnée à max_distance_km).
    """
    if current_user.get("role") != "user":
        raise HTTPException(status_code=403, detail="Accès réservé aux usagers")

    user_id = current_user["user_id"]
    code = data.code.strip().upper()

    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usager non trouvé")

    # Empêche d'écraser un crédit déjà actif
    if user.get("pending_promo"):
        raise HTTPException(
            status_code=409,
            detail="Vous avez déjà un code promo actif. Utilisez-le ou attendez son expiration avant d'en activer un nouveau."
        )

    promo = await db.promo_codes.find_one({"code": code}, {"_id": 0})
    if not promo:
        raise HTTPException(status_code=404, detail="Code promo introuvable")

    if promo.get("used"):
        raise HTTPException(status_code=409, detail="Code promo déjà utilisé")

    now = datetime.now(timezone.utc)
    try:
        expires_dt = datetime.fromisoformat(promo["expires_at"].replace("Z", "+00:00"))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Code promo : date d'expiration invalide")
    if expires_dt < now:
        raise HTTPException(status_code=410, detail="Code promo expiré")

    # Marquer le code comme utilisé (réservation à cet usager)
    await db.promo_codes.update_one(
        {"code": code, "used": False},
        {
            "$set": {
                "used": True,
                "used_by": user_id,
                "used_at": now.isoformat(),
                "redeemed_at": now.isoformat(),
            }
        },
    )

    # Activer le crédit course offerte sur le profil usager
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

    return {
        "status": "ok",
        "message": f"Code activé ! Ta 1ère course est offerte (jusqu'à {pending_promo['max_distance_km']} km).",
        "pending_promo": pending_promo,
    }


@router.get("/promo-codes/my-promo")
async def get_my_promo(current_user: dict = Depends(get_current_user)):
    """Usager: récupère le crédit promo actif sur son profil (s'il y en a un)."""
    if current_user.get("role") != "user":
        raise HTTPException(status_code=403, detail="Accès réservé aux usagers")

    user = await db.users.find_one(
        {"id": current_user["user_id"]},
        {"_id": 0, "pending_promo": 1},
    )
    return {"pending_promo": (user or {}).get("pending_promo")}



# -----------------------------------------------------------------------------
# QR CODE GENERATION (one code = one flyer, per the Capitaine's strategy)
# -----------------------------------------------------------------------------
@router.get("/admin/promo-codes/qr")
async def generate_promo_qr(
    code: str,
    base_url: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Admin: génère un QR code PNG pointant vers `/saint-denis?promo=<code>`.

    Idéal pour flyers physiques : 1 flyer = 1 code = 1 QR code unique → zéro friction
    pour l'usager (scan → landing prérempli → inscription).
    Le paramètre `base_url` permet d'override l'URL frontend (défaut: FRONTEND_URL).
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    code_norm = code.strip().upper()
    promo = await db.promo_codes.find_one({"code": code_norm}, {"_id": 0})
    if not promo:
        raise HTTPException(status_code=404, detail="Code promo introuvable")

    frontend_url = (base_url or os.environ.get("FRONTEND_URL") or "https://metro-taxi.com").rstrip("/")
    target_url = f"{frontend_url}/saint-denis?promo={code_norm}&src=flyer"

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # 30% recovery — bon pour impression
        box_size=12,
        border=2,
    )
    qr.add_data(target_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="image/png",
        headers={
            "Content-Disposition": f'inline; filename="qr_{code_norm}.png"',
            "Cache-Control": "public, max-age=3600",
            "X-Target-Url": target_url,
        },
    )


@router.post("/admin/promo-codes/qr-batch")
async def generate_promo_qr_batch(
    current_user: dict = Depends(get_current_user),
    campaign: Optional[str] = None,
    base_url: Optional[str] = None,
):
    """Admin: génère un ZIP contenant TOUS les QR codes PNG d'une campagne.

    Permet d'imprimer 30 flyers d'un coup. Retourne `application/zip`.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    import zipfile

    q: dict = {}
    if campaign:
        q["campaign"] = campaign

    codes = await db.promo_codes.find(q, {"_id": 0}).to_list(length=1000)
    if not codes:
        raise HTTPException(status_code=404, detail="Aucun code trouvé pour cette campagne")

    frontend_url = (base_url or os.environ.get("FRONTEND_URL") or "https://metro-taxi.com").rstrip("/")

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in codes:
            code_norm = p["code"]
            target_url = f"{frontend_url}/saint-denis?promo={code_norm}&src=flyer"
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=12,
                border=2,
            )
            qr.add_data(target_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            png_buf = io.BytesIO()
            img.save(png_buf, format="PNG")
            zf.writestr(f"qr_{code_norm}.png", png_buf.getvalue())

    zip_buf.seek(0)
    filename = f"qrcodes_{campaign or 'all'}.zip"
    return Response(
        content=zip_buf.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
