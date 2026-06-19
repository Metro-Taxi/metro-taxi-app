"""
Routes Partenaires Commerciaux — Métro-Taxi V10 (19/06/2026)

Système d'affiliation pour :
- commerce_fixe : boutiques (Golden GSM, Kelly's, Taxiphones...)
- ambulant     : ambassadeurs mobiles (démarchage rue/marché)
- entreprise   : hôtels, écoles, mairies...

Chaque partenaire a :
- Code parrainage unique (4 lettres dérivées du nom + suffixe si collision)
- QR code à afficher / porter
- Lien public : metro-taxi.com/inscription?ref=GGSM
- Commission 15% (configurable) sur chaque abonnement signé via son code
- Dashboard temps réel pour voir signups + commission

Endpoints :
- POST   /api/partners/apply              : Inscription publique (status=pending)
- GET    /api/partners/by-code/{code}     : Récupère infos publiques d'un partenaire (pour signup)
- GET    /api/partners/me                 : Dashboard du partenaire connecté
- GET    /api/admin/partners              : Liste admin
- POST   /api/admin/partners/{id}/validate : Admin valide / refuse
"""
import logging
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from database import db
from server import get_current_user, hash_password
from services.emails import send_partner_welcome_email, send_partner_application_alert

router = APIRouter(prefix="/api", tags=["commercial-partners"])
logger = logging.getLogger(__name__)


# ============================================
# MODELS
# ============================================
PartnerType = Literal["commerce_fixe", "ambulant", "entreprise"]
PartnerStatus = Literal["pending", "active", "suspended", "rejected"]


class PartnerApplication(BaseModel):
    """Soumission publique d'une demande de partenariat."""
    partner_type: PartnerType
    business_name: str = Field(..., min_length=2, max_length=120)
    contact_first_name: str = Field(..., min_length=1, max_length=80)
    contact_last_name: str = Field(..., min_length=1, max_length=80)
    email: EmailStr
    phone: str = Field(..., min_length=5, max_length=30)
    # Commerce fixe : adresse + horaires
    street_address: Optional[str] = Field(None, max_length=200)
    postal_code: Optional[str] = Field(None, max_length=10)
    city: Optional[str] = Field(None, max_length=120)
    siret: Optional[str] = Field(None, max_length=20)
    # Ambulant : zone d'activité
    activity_zone: Optional[str] = Field(None, max_length=200)
    # Message libre
    motivation: Optional[str] = Field(None, max_length=1500)
    # Préférences contact
    preferred_contact: Optional[Literal["email", "phone", "whatsapp"]] = "email"


class PartnerValidation(BaseModel):
    """Admin valide ou rejette une demande."""
    action: Literal["approve", "reject", "suspend"]
    commission_rate: Optional[float] = Field(0.15, ge=0, le=0.5)
    notes: Optional[str] = Field(None, max_length=1500)


# ============================================
# HELPERS
# ============================================
def generate_referral_code(business_name: str) -> str:
    """Génère un code parrainage 4 lettres extraites du nom du commerce.
    
    Règle (modèle Capitaine) :
    - 1 lettre par mot
    - Si < 4 lettres au total, on complète avec les lettres suivantes du DERNIER mot
    
    Ex :
    - 'Golden GSM'       → G + GSM   → GGSM
    - 'Kellys Mode'      → K + MOD   → KMOD  
    - 'Souleymane Tall'  → S + TAL   → STAL
    - 'Taxiphones'       → TAXI (mono-mot, 4 premières lettres)
    - 'Le Chat Noir'     → L + C + NOIR → LCNO (truncated à 4)
    """
    import unicodedata
    # Nettoie : enlève accents, ponctuation, ne garde que lettres
    name = unicodedata.normalize('NFKD', business_name).encode('ASCII', 'ignore').decode()
    name = ''.join(c.upper() if c.isalpha() else ' ' for c in name)
    words = [w for w in name.split() if w]
    if not words:
        return ''.join(secrets.choice('ABCDEFGHIJKLMNPQRSTUVWXYZ') for _ in range(4))
    
    if len(words) == 1:
        # Mono-mot : 4 premières lettres
        return (words[0] + 'XXXX')[:4]
    
    # Multi-mots : 1 lettre par mot, puis on complète avec le DERNIER mot
    code = ''.join(w[0] for w in words)
    if len(code) < 4:
        # Complète avec les lettres suivantes du dernier mot
        last_word_extra = words[-1][1:]  # tout sauf la 1ère lettre déjà incluse
        code += last_word_extra
    return (code + 'XXXX')[:4]


async def get_unique_referral_code(business_name: str) -> str:
    """Génère un code unique en ajoutant un suffixe numérique si collision."""
    base_code = generate_referral_code(business_name)
    candidate = base_code
    suffix = 1
    while await db.commercial_partners.find_one({"referral_code": candidate}):
        # Collision : ajoute un suffixe numérique (max 99 = 6 caractères)
        if suffix < 10:
            candidate = base_code[:3] + str(suffix)
        else:
            candidate = base_code[:2] + str(suffix)
        suffix += 1
        if suffix > 99:
            # Fallback random
            candidate = base_code[:2] + secrets.token_hex(1).upper()
            break
    return candidate


def _public_partner_view(partner: dict) -> dict:
    """Filtre les champs sensibles pour exposition publique (page signup)."""
    return {
        "referral_code": partner["referral_code"],
        "business_name": partner["business_name"],
        "partner_type": partner["partner_type"],
        "status": partner["status"],
    }


# ============================================
# PUBLIC ENDPOINTS
# ============================================
@router.post("/partners/apply")
async def partner_apply(data: PartnerApplication, request: Request):
    """Inscription publique d'un partenaire commercial — status=pending."""
    # Anti-doublon : même email + status=pending dans les 24h
    existing = await db.commercial_partners.find_one({
        "email": data.email.lower().strip(),
        "status": {"$in": ["pending", "active"]}
    })
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Une demande existe déjà pour cet email. Vérifie tes mails ou contacte le support."
        )
    
    referral_code = await get_unique_referral_code(data.business_name)
    partner_id = str(uuid.uuid4())
    
    partner_doc = {
        "id": partner_id,
        "partner_type": data.partner_type,
        "business_name": data.business_name.strip(),
        "contact_first_name": data.contact_first_name.strip(),
        "contact_last_name": data.contact_last_name.strip(),
        "email": data.email.lower().strip(),
        "phone": data.phone.strip(),
        "street_address": (data.street_address or "").strip() or None,
        "postal_code": (data.postal_code or "").strip() or None,
        "city": (data.city or "").strip() or None,
        "siret": (data.siret or "").strip() or None,
        "activity_zone": (data.activity_zone or "").strip() or None,
        "motivation": (data.motivation or "").strip() or None,
        "preferred_contact": data.preferred_contact,
        "referral_code": referral_code,
        "commission_rate": 0.15,  # 15% par défaut, ajustable par admin
        "status": "pending",
        "password": None,  # Sera défini lors de la validation admin
        "created_at": datetime.now(timezone.utc).isoformat(),
        "validated_at": None,
        "stats": {
            "total_signups": 0,
            "total_subscribers": 0,
            "total_commission_earned": 0.0,
            "total_commission_paid": 0.0,
        }
    }
    await db.commercial_partners.insert_one(partner_doc)
    logger.info(f"📋 Nouveau partenaire pending : {data.business_name} ({referral_code})")
    
    # Notification email à l'admin
    try:
        await send_partner_application_alert(partner_doc)
    except Exception as e:
        logger.error(f"Failed to send partner application alert: {e}")
    
    return {
        "message": "Ta demande a été reçue. On te recontacte sous 24-48h.",
        "referral_code": referral_code,
    }


@router.get("/partners/by-code/{code}")
async def get_partner_by_code(code: str):
    """Récupère les infos publiques d'un partenaire via son code de parrainage.
    Utilisé sur la page d'inscription quand un usager arrive avec ?ref=XXX."""
    code = code.upper().strip()
    partner = await db.commercial_partners.find_one(
        {"referral_code": code, "status": "active"},
        {"_id": 0}
    )
    if not partner:
        raise HTTPException(status_code=404, detail="Code parrainage invalide ou partenaire inactif")
    return _public_partner_view(partner)


# ============================================
# PARTNER ENDPOINTS (authenticated as partner)
# ============================================
@router.get("/partners/me")
async def get_my_partner_dashboard(current_user: dict = Depends(get_current_user)):
    """Dashboard du partenaire connecté."""
    if current_user.get("role") != "partner":
        raise HTTPException(status_code=403, detail="Accès réservé aux partenaires")
    
    partner = await db.commercial_partners.find_one(
        {"id": current_user["user_id"]},
        {"_id": 0, "password": 0}
    )
    if not partner:
        raise HTTPException(status_code=404, detail="Compte partenaire introuvable")
    
    # Récupérer les usagers récents qu'il a parrainés (anonymisés)
    referred_users = await db.users.find(
        {"referral_code": partner["referral_code"]},
        {"_id": 0, "id": 1, "first_name": 1, "created_at": 1, "subscription_active": 1}
    ).sort("created_at", -1).limit(20).to_list(20)
    
    # Anonymise le prénom (garde l'initiale)
    for u in referred_users:
        if u.get("first_name"):
            u["first_name"] = u["first_name"][0] + "."
    
    partner["recent_referrals"] = referred_users
    return partner


# ============================================
# ADMIN ENDPOINTS
# ============================================
async def _require_admin(current_user: dict):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès admin requis")


@router.get("/admin/partners")
async def admin_list_partners(
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Liste tous les partenaires pour l'admin, triés par date desc."""
    await _require_admin(current_user)
    
    query = {}
    if status_filter and status_filter != "all":
        query["status"] = status_filter
    
    partners = await db.commercial_partners.find(
        query, {"_id": 0, "password": 0}
    ).sort("created_at", -1).to_list(500)
    
    # Compte total par status pour les badges admin
    counts = {
        "pending": await db.commercial_partners.count_documents({"status": "pending"}),
        "active": await db.commercial_partners.count_documents({"status": "active"}),
        "suspended": await db.commercial_partners.count_documents({"status": "suspended"}),
        "rejected": await db.commercial_partners.count_documents({"status": "rejected"}),
    }
    return {"partners": partners, "counts": counts}


@router.post("/admin/partners/{partner_id}/validate")
async def admin_validate_partner(
    partner_id: str,
    data: PartnerValidation,
    current_user: dict = Depends(get_current_user)
):
    """Admin valide / rejette / suspend une demande de partenariat."""
    await _require_admin(current_user)
    
    partner = await db.commercial_partners.find_one({"id": partner_id}, {"_id": 0})
    if not partner:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    
    update = {
        "admin_notes": data.notes,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "validated_by": current_user.get("user_id"),
    }
    
    if data.action == "approve":
        # Génère un mot de passe temporaire et envoie par email
        temp_password = secrets.token_urlsafe(9)  # 12 caractères
        update["status"] = "active"
        update["password"] = hash_password(temp_password)
        update["commission_rate"] = data.commission_rate or partner.get("commission_rate", 0.15)
        await db.commercial_partners.update_one({"id": partner_id}, {"$set": update})
        
        # Envoie l'email de bienvenue avec login + mot de passe
        try:
            await send_partner_welcome_email(
                email=partner["email"],
                first_name=partner["contact_first_name"],
                business_name=partner["business_name"],
                referral_code=partner["referral_code"],
                temp_password=temp_password,
            )
        except Exception as e:
            logger.error(f"Failed to send partner welcome email: {e}")
        
        logger.info(f"✅ Partenaire validé : {partner['business_name']} ({partner['referral_code']})")
        return {"message": "Partenaire validé. Email de bienvenue envoyé.", "status": "active"}
    
    elif data.action == "reject":
        update["status"] = "rejected"
        await db.commercial_partners.update_one({"id": partner_id}, {"$set": update})
        logger.info(f"❌ Partenaire rejeté : {partner['business_name']}")
        return {"message": "Partenaire rejeté.", "status": "rejected"}
    
    elif data.action == "suspend":
        update["status"] = "suspended"
        await db.commercial_partners.update_one({"id": partner_id}, {"$set": update})
        logger.info(f"⏸️ Partenaire suspendu : {partner['business_name']}")
        return {"message": "Partenaire suspendu.", "status": "suspended"}
    
    raise HTTPException(status_code=400, detail="Action invalide")


@router.get("/admin/partners/{partner_id}")
async def admin_get_partner_details(
    partner_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Détail complet d'un partenaire avec stats à jour."""
    await _require_admin(current_user)
    
    partner = await db.commercial_partners.find_one({"id": partner_id}, {"_id": 0, "password": 0})
    if not partner:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    
    # Recalcule les stats live depuis la collection users
    referred = await db.users.find(
        {"referral_code": partner["referral_code"]},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1,
         "created_at": 1, "subscription_active": 1, "subscription_plan": 1}
    ).sort("created_at", -1).to_list(500)
    
    subscribers = [u for u in referred if u.get("subscription_active")]
    
    # Calcul commission basé sur abonnements actifs
    plan_amounts = {"solo": 6.99, "famille": 19.99, "pro": 53.99}
    total_commission = 0.0
    for sub in subscribers:
        plan_price = plan_amounts.get(sub.get("subscription_plan", "solo"), 6.99)
        total_commission += plan_price * partner.get("commission_rate", 0.15)
    
    partner["referred_users"] = referred
    partner["stats_live"] = {
        "total_signups": len(referred),
        "active_subscribers": len(subscribers),
        "commission_this_month": round(total_commission, 2),
    }
    return partner


# ============================================
# COMMISSION HELPERS (utilisés par Sogecommerce IPN + payout lundi)
# Patch V10 - 19/06/2026
# ============================================
async def credit_partner_commission(
    referral_code: str,
    user_id: str,
    order_id: str,
    plan_id: str,
    amount_cents: int,
) -> bool:
    """Crée une commission partenaire à l'issue d'un paiement Sogecommerce.

    Appelée depuis l'IPN Sogecommerce sur paiement réussi (initial + renouvellement).
    Le partenaire ne touche RIEN tant qu'un paiement n'est pas effectivement reçu.

    Returns True si une commission a bien été créditée.
    """
    if not referral_code or not amount_cents:
        return False
    code = referral_code.upper().strip()
    partner = await db.commercial_partners.find_one(
        {"referral_code": code, "status": "active"}, {"_id": 0}
    )
    if not partner:
        logger.info(f"Pas de partenaire actif pour code {code} — skip commission")
        return False

    # Anti-doublon : si on a déjà crédité pour cet order_id, on saute
    existing = await db.partner_commissions.find_one({"order_id": order_id})
    if existing:
        logger.info(f"Commission déjà créditée pour order {order_id}")
        return False

    rate = float(partner.get("commission_rate", 0.15))
    commission_eur = round((amount_cents / 100.0) * rate, 2)

    await db.partner_commissions.insert_one({
        "id": str(uuid.uuid4()),
        "partner_id": partner["id"],
        "referral_code": code,
        "user_id": user_id,
        "order_id": order_id,
        "plan_id": plan_id,
        "amount_paid_eur": round(amount_cents / 100.0, 2),
        "commission_rate": rate,
        "commission_eur": commission_eur,
        "status": "pending_payout",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    # Met à jour les stats agrégées du partenaire (pour affichage rapide)
    await db.commercial_partners.update_one(
        {"id": partner["id"]},
        {"$inc": {
            "stats.total_commission_earned": commission_eur,
        }}
    )
    logger.info(
        f"💰 Commission {commission_eur}€ créditée à {partner['business_name']} "
        f"({code}) — paiement {amount_cents}c order={order_id}"
    )
    return True


async def process_weekly_partner_payouts() -> dict:
    """Agrège toutes les commissions 'pending_payout' par partenaire et les marque
    comme 'ready_for_payout' (en attente de virement bancaire manuel/SEPA).

    Appelé chaque LUNDI par le scheduler existant (process_automatic_payouts).
    Retourne un résumé pour les logs.
    """
    pending = await db.partner_commissions.find(
        {"status": "pending_payout"}, {"_id": 0}
    ).to_list(length=10000)

    by_partner: dict[str, list] = {}
    for c in pending:
        by_partner.setdefault(c["partner_id"], []).append(c)

    total_paid_out = 0.0
    payouts_created = 0
    for partner_id, commissions in by_partner.items():
        total = round(sum(c["commission_eur"] for c in commissions), 2)
        if total <= 0:
            continue
        payout_id = str(uuid.uuid4())
        await db.partner_payouts.insert_one({
            "id": payout_id,
            "partner_id": partner_id,
            "amount_eur": total,
            "commission_count": len(commissions),
            "commission_ids": [c["id"] for c in commissions],
            "status": "ready_for_transfer",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        await db.partner_commissions.update_many(
            {"id": {"$in": [c["id"] for c in commissions]}},
            {"$set": {"status": "paid", "payout_id": payout_id}}
        )
        await db.commercial_partners.update_one(
            {"id": partner_id},
            {"$inc": {"stats.total_commission_paid": total}}
        )
        total_paid_out += total
        payouts_created += 1

    return {
        "payouts_created": payouts_created,
        "total_eur": round(total_paid_out, 2),
        "commissions_processed": len(pending),
    }
