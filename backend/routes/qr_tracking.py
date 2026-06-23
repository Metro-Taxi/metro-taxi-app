"""
Tracking QR codes / campagnes marketing.
Permet de mesurer les conversions des flyers (Orly, CDG, Gare de Lyon, banderole, etc.).

Usage côté frontend :
  - Quand un visiteur arrive sur metro-taxi.com avec ?ref=xxx, on POST /api/qr/scan
  - On stocke aussi le ref en localStorage pour le binder au signup ensuite
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel
import logging
from database import db
from services.auth import get_current_user

router = APIRouter(prefix="/api")


class QRScanIn(BaseModel):
    campaign: str
    referrer: Optional[str] = None


@router.post("/qr/scan")
async def record_qr_scan(payload: QRScanIn, request: Request):
    """Endpoint public — enregistre un scan QR / clic sur lien tracké."""
    campaign = (payload.campaign or "").strip().lower()[:80]
    if not campaign:
        raise HTTPException(status_code=400, detail="campaign manquant")
    try:
        await db.qr_scans.insert_one({
            "campaign": campaign,
            "referrer": (payload.referrer or "")[:200],
            "ip": request.client.host if request.client else "",
            "user_agent": request.headers.get("user-agent", "")[:300],
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logging.warning(f"qr_scan insert failed: {e}")
        return {"status": "ignored"}
    return {"status": "recorded", "campaign": campaign}


@router.get("/admin/qr/stats")
async def qr_stats(current_user: dict = Depends(get_current_user)):
    """Stats agrégées : scans par campagne + inscriptions issues (users + drivers)."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")

    # 1) Aggrégation des scans par campagne
    scans_pipeline = [
        {"$group": {
            "_id": "$campaign",
            "total_scans": {"$sum": 1},
            "last_scan": {"$max": "$scanned_at"},
            "first_scan": {"$min": "$scanned_at"},
        }},
        {"$sort": {"total_scans": -1}},
    ]
    scans_by_campaign = []
    async for doc in db.qr_scans.aggregate(scans_pipeline):
        scans_by_campaign.append({
            "campaign": doc["_id"],
            "total_scans": doc["total_scans"],
            "last_scan": doc.get("last_scan"),
            "first_scan": doc.get("first_scan"),
        })

    # 2) Inscriptions usagers par campagne (via signup_campaign)
    users_pipeline = [
        {"$match": {"signup_campaign": {"$exists": True, "$nin": [None, ""]}}},
        {"$group": {"_id": "$signup_campaign", "users": {"$sum": 1}}},
    ]
    users_by_campaign: dict = {}
    async for doc in db.users.aggregate(users_pipeline):
        users_by_campaign[(doc["_id"] or "").strip().lower()] = doc["users"]

    # 3) Inscriptions chauffeurs par source (via source_inscription)
    drivers_pipeline = [
        {"$match": {"source_inscription": {"$exists": True, "$nin": [None, ""]}}},
        {"$group": {"_id": "$source_inscription", "drivers": {"$sum": 1}}},
    ]
    drivers_by_source: dict = {}
    async for doc in db.drivers.aggregate(drivers_pipeline):
        drivers_by_source[(doc["_id"] or "").strip().lower()] = doc["drivers"]

    # 4) Merge — on enrichit chaque campagne avec ses inscriptions et calcule la conversion
    rows = []
    seen_campaigns = set()
    for s in scans_by_campaign:
        c = s["campaign"]
        seen_campaigns.add(c)
        users_count = users_by_campaign.get(c, 0)
        drivers_count = drivers_by_source.get(c, 0)
        total_signups = users_count + drivers_count
        conv_pct = round((total_signups / s["total_scans"]) * 100, 1) if s["total_scans"] else 0
        rows.append({
            "campaign": c,
            "scans": s["total_scans"],
            "users_signed_up": users_count,
            "drivers_signed_up": drivers_count,
            "total_signups": total_signups,
            "conversion_pct": conv_pct,
            "first_scan": s["first_scan"],
            "last_scan": s["last_scan"],
        })

    # Campagnes qui ont des inscriptions mais pas de scans trackés (ex : drivers historiques)
    untracked_users = {k: v for k, v in users_by_campaign.items() if k not in seen_campaigns}
    untracked_drivers = {k: v for k, v in drivers_by_source.items() if k not in seen_campaigns}
    untracked_keys = set(list(untracked_users.keys()) + list(untracked_drivers.keys()))
    for c in untracked_keys:
        rows.append({
            "campaign": c,
            "scans": 0,
            "users_signed_up": untracked_users.get(c, 0),
            "drivers_signed_up": untracked_drivers.get(c, 0),
            "total_signups": untracked_users.get(c, 0) + untracked_drivers.get(c, 0),
            "conversion_pct": None,  # NA car pas de scan tracké
            "first_scan": None,
            "last_scan": None,
        })

    # Totaux globaux
    total_scans = sum(r["scans"] for r in rows)
    total_signups_all = sum(r["total_signups"] for r in rows)
    global_conv = round((total_signups_all / total_scans) * 100, 1) if total_scans else None

    # Derniers 7 jours
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    last7_scans = await db.qr_scans.count_documents({"scanned_at": {"$gte": since}})

    return {
        "rows": rows,
        "totals": {
            "total_scans": total_scans,
            "total_signups": total_signups_all,
            "global_conversion_pct": global_conv,
            "scans_last_7_days": last7_scans,
        },
    }
