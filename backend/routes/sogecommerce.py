"""
Routes paiement Sogecommerce (Société Générale).

- POST /api/payments/sogecommerce/checkout : génère un formulaire signé (auth user)
- POST /api/payments/sogecommerce/ipn       : notification serveur-à-serveur (public)
- GET  /api/payments/sogecommerce/return    : retour usager après paiement (public)
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import unquote_plus
import logging
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from database import db
from services.auth import get_current_user
from services.emails import send_subscription_confirmation_email
from services.sogecommerce import (
    compute_vads_signature,
    verify_vads_signature,
    get_active_key,
    get_ctx_mode,
    get_shop_id,
    get_payment_url,
)
from routes.auto_campaigns import attempt_auto_attribution

router = APIRouter(prefix="/api/payments/sogecommerce", tags=["sogecommerce"])

logger = logging.getLogger(__name__)

# Devises ISO 4217 numériques
CURRENCY_NUM = {
    "EUR": "978",
    "GBP": "826",
    "USD": "840",
}


class SogeCheckoutRequest(BaseModel):
    plan_id: str
    region_id: str
    origin_url: str


def _short_trans_id() -> str:
    """vads_trans_id doit être 6 caractères alphanumériques, unique sur la journée."""
    # Utilise les 6 derniers chiffres du timestamp ms pour rester court & unique journalier.
    ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    return str(ms)[-6:]


@router.post("/checkout")
async def create_sogecommerce_checkout(
    data: SogeCheckoutRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Crée un payload de formulaire signé pour redirection vers Sogecommerce.

    Le frontend recevra :
    - `action_url` : l'URL POST cible (vads-payment)
    - `fields`     : tous les champs à inclure dans le `<form>` (signature incluse)

    Charge à lui de faire un auto-submit POST.
    """
    # 🚫 PAUSE COMMERCIALE : tant que l'env SUBSCRIPTIONS_PAUSED=true, on refuse tout nouveau paiement
    # Mis en place le 16/06/2026 suite à l'impossibilité d'effectuer les courses payées.
    if os.environ.get("SUBSCRIPTIONS_PAUSED", "false").lower() == "true":
        launch_date = os.environ.get("LAUNCH_DATE", "2026-07-26")
        raise HTTPException(
            status_code=503,
            detail=f"Les nouvelles souscriptions sont temporairement suspendues. Lancement officiel le {launch_date}. Inscris-toi sur la liste prioritaire pour être prévenu en premier."
        )
    
    # Lazy import pour éviter import circulaire
    from server import SUBSCRIPTION_PLANS, REGIONAL_PRICING

    if data.plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Plan invalide")

    region = await db.regions.find_one({"id": data.region_id, "is_active": True})
    if not region:
        raise HTTPException(status_code=400, detail="Région non disponible")

    # Prix régional si défini, sinon prix par défaut
    plan_default = SUBSCRIPTION_PLANS[data.plan_id]
    regional = REGIONAL_PRICING.get(data.region_id, {})
    regional_plan = (regional.get("plans") or {}).get(data.plan_id, {})
    price_cents = regional_plan.get("price_cents", plan_default["price_cents"])
    currency_code = regional.get("currency", "EUR").upper()
    currency_num = CURRENCY_NUM.get(currency_code, "978")

    user_id = current_user["user_id"]
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0, "email": 1}) or {}
    user_email = user_doc.get("email", "")
    trans_id = _short_trans_id()
    order_id = str(uuid.uuid4())

    # Date format vads : yyyyMMddHHmmss UTC
    now_utc = datetime.now(timezone.utc)
    trans_date = now_utc.strftime("%Y%m%d%H%M%S")

    # URL retour usager (front) — côté serveur on traite via IPN
    return_url = f"{data.origin_url}/subscription/success?provider=sogecommerce&order_id={order_id}"

    fields = {
        "vads_action_mode": "INTERACTIVE",
        "vads_amount": str(price_cents),
        "vads_ctx_mode": get_ctx_mode(),
        "vads_currency": currency_num,
        "vads_cust_email": user_email,
        "vads_cust_id": user_id,
        "vads_order_id": order_id,
        "vads_page_action": "PAYMENT",
        "vads_payment_config": "SINGLE",
        "vads_return_mode": "GET",
        "vads_site_id": get_shop_id(),
        "vads_trans_date": trans_date,
        "vads_trans_id": trans_id,
        "vads_url_return": return_url,
        "vads_version": "V2",
        # Métadonnées récupérables dans l'IPN via vads_ext_info_*
        "vads_ext_info_plan_id": data.plan_id,
        "vads_ext_info_region_id": data.region_id,
        "vads_ext_info_user_id": user_id,
    }

    signature = compute_vads_signature(fields, get_active_key())

    # Trace en DB
    await db.payment_transactions.insert_one({
        "id": str(uuid.uuid4()),
        "provider": "sogecommerce",
        "order_id": order_id,
        "trans_id": trans_id,
        "trans_date": trans_date,
        "user_id": user_id,
        "plan_id": data.plan_id,
        "region_id": data.region_id,
        "amount_cents": price_cents,
        "currency": currency_code,
        "ctx_mode": fields["vads_ctx_mode"],
        "status": "pending",
        "payment_status": "initiated",
        "created_at": now_utc.isoformat(),
    })

    return {
        "action_url": get_payment_url(),
        "fields": {**fields, "signature": signature},
        "order_id": order_id,
    }


@router.post("/ipn")
async def sogecommerce_ipn(request: Request):
    """Notification serveur-à-serveur (Instant Payment Notification).

    - Signature : champ `signature` à recalculer sur tous les `vads_*`.
    - vads_trans_status == "AUTHORISED" / "CAPTURED" => succès.
    - vads_ext_info_plan_id / vads_ext_info_region_id / vads_ext_info_user_id
      portent le contexte applicatif.
    """
    form = await request.form()
    payload = {k: str(v) for k, v in form.items()}
    received_signature = payload.get("signature", "")

    try:
        key = get_active_key()
    except Exception as exc:
        logger.error(f"Sogecommerce IPN: clé indisponible: {exc}")
        raise HTTPException(status_code=500, detail="Configuration manquante")

    if not verify_vads_signature(payload, received_signature, key):
        logger.warning(f"Sogecommerce IPN: signature invalide (order_id={payload.get('vads_order_id')})")
        raise HTTPException(status_code=400, detail="Signature invalide")

    order_id = payload.get("vads_order_id", "")
    trans_status = payload.get("vads_trans_status", "")
    trans_uuid = payload.get("vads_trans_uuid", "")
    user_id = payload.get("vads_ext_info_user_id", "")
    plan_id = payload.get("vads_ext_info_plan_id", "")
    region_id = payload.get("vads_ext_info_region_id", "")
    amount_cents = int(payload.get("vads_amount", "0") or 0)

    transaction = await db.payment_transactions.find_one(
        {"order_id": order_id, "provider": "sogecommerce"}, {"_id": 0}
    )
    if not transaction:
        logger.error(f"Sogecommerce IPN: transaction inconnue order_id={order_id}")
        # On répond 200 quand même pour stopper les retries (sinon SG retente 9x)
        return "OK"

    # Mise à jour transaction (idempotent)
    await db.payment_transactions.update_one(
        {"order_id": order_id, "provider": "sogecommerce"},
        {"$set": {
            "trans_uuid": trans_uuid,
            "trans_status": trans_status,
            "ipn_received_at": datetime.now(timezone.utc).isoformat(),
            "payment_status": trans_status,
        }},
    )

    success_statuses = {"AUTHORISED", "CAPTURED", "ACCEPTED"}
    if trans_status not in success_statuses:
        logger.info(f"Sogecommerce IPN: paiement non finalisé order_id={order_id} status={trans_status}")
        return "OK"

    # Déjà activé ?
    if transaction.get("status") == "completed":
        return "OK"

    # Lazy import
    from server import SUBSCRIPTION_PLANS

    plan = SUBSCRIPTION_PLANS.get(plan_id)
    if not plan:
        logger.error(f"Sogecommerce IPN: plan inconnu {plan_id}")
        return "OK"

    now = datetime.now(timezone.utc)
    user = await db.users.find_one({"id": user_id})

    if not user:
        logger.error(f"Sogecommerce IPN: user inconnu {user_id}")
        return "OK"

    existing_subs = user.get("subscriptions", []) or []
    base_date = now
    for sub in existing_subs:
        if sub.get("region_id") == region_id:
            try:
                existing_expires = datetime.fromisoformat(
                    str(sub.get("expires_at", "")).replace("Z", "+00:00")
                )
                if existing_expires > now:
                    base_date = existing_expires
            except (ValueError, TypeError):
                pass
            break

    expires_at = base_date + timedelta(hours=plan["duration_hours"])
    new_subscription = {
        "region_id": region_id,
        "plan_id": plan_id,
        "expires_at": expires_at.isoformat(),
        "is_active": True,
        "payment_method": "sogecommerce",
        "created_at": now.isoformat(),
    }

    updated = False
    for i, sub in enumerate(existing_subs):
        if sub.get("region_id") == region_id:
            existing_subs[i] = new_subscription
            updated = True
            break
    if not updated:
        existing_subs.append(new_subscription)

    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "subscriptions": existing_subs,
            "subscription_active": True,
            "subscription_expires": expires_at.isoformat(),
            "subscription_plan": plan_id,
            "email_verified": True,  # 30/06/2026 — activation auto au paiement réussi
        }},
    )
    await db.payment_transactions.update_one(
        {"order_id": order_id, "provider": "sogecommerce"},
        {"$set": {"status": "completed"}},
    )

    # Auto-attribution promo si l'usager fait partie d'une campagne Saint-Denis & co.
    u_camp = await db.users.find_one(
        {"id": user_id},
        {"_id": 0, "signup_campaign": 1, "referral_code": 1}
    )
    if u_camp and u_camp.get("signup_campaign"):
        try:
            await attempt_auto_attribution(user_id, u_camp["signup_campaign"])
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Auto-attribution échouée: {exc}")
    else:
        # Fallback : auto-attribution par région (flyers sans lien magique)
        try:
            from routes.auto_campaigns import auto_attribute_for_region
            await auto_attribute_for_region(user_id, region_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Auto-attribution région échouée: {exc}")

    # Patch V10 — Commission partenaire commercial (15% à chaque paiement)
    if u_camp and u_camp.get("referral_code"):
        try:
            from routes.commercial_partners import credit_partner_commission
            await credit_partner_commission(
                referral_code=u_camp["referral_code"],
                user_id=user_id,
                order_id=order_id,
                plan_id=plan_id,
                amount_cents=amount_cents,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Commission partenaire échouée: {exc}")

    # Email confirmation
    region = await db.regions.find_one({"id": region_id}, {"_id": 0})
    region_name = (region or {}).get("name", region_id)
    user_lang = (region or {}).get("language", "fr")
    try:
        await send_subscription_confirmation_email(
            user.get("email"),
            user.get("first_name", ""),
            f"{plan['name']} - {region_name}",
            expires_at.strftime("%d/%m/%Y à %H:%M"),
            user_lang,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Email confirmation échoué: {exc}")

    logger.info(f"✅ Sogecommerce: abonnement activé user={user_id} order={order_id} amount={amount_cents}c")
    return "OK"


@router.get("/return")
async def sogecommerce_return(request: Request):
    """Endpoint optionnel de retour usager (GET).

    Le frontend gère le retour via la query string. Cet endpoint sert juste de
    proxy pour vérifier le statut côté serveur depuis le frontend.
    """
    order_id = request.query_params.get("order_id") or request.query_params.get("vads_order_id")
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id manquant")
    tx = await db.payment_transactions.find_one(
        {"order_id": order_id, "provider": "sogecommerce"}, {"_id": 0}
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction inconnue")
    return {
        "order_id": order_id,
        "status": tx.get("status"),
        "payment_status": tx.get("payment_status"),
        "trans_status": tx.get("trans_status"),
        "amount_cents": tx.get("amount_cents"),
        "currency": tx.get("currency"),
        "plan_id": tx.get("plan_id"),
        "region_id": tx.get("region_id"),
    }
