#!/usr/bin/env python3
"""
PATCH v5 — Sogecommerce + Sondage chauffeurs 13 juin + Cleanup Uber/Bolt
========================================================================

Patche le VPS Hostinger /var/www/metro-taxi-app/ avec :
  1. Service signature Sogecommerce (services/sogecommerce.py)
  2. Routes Sogecommerce (routes/sogecommerce.py)
  3. Enregistrement du router dans server.py
  4. Variables d'env Sogecommerce dans backend/.env
  5. Bouton "Payer avec Société Générale" dans Subscription.js
  6. Fonction send_driver_presence_survey_email dans services/emails.py
  7. Endpoints sondage présence chauffeurs (preview/test/confirm/results + public 1-clic)
  8. Cleanup mentions Uber/Bolt s'il en reste dans emails.py

Usage sur le VPS :
    cd /var/www/metro-taxi-app
    curl -fsSL https://metro-taxi-demo.preview.emergentagent.com/patch_v5_full.py -o /tmp/patch_v5.py
    python3 /tmp/patch_v5.py
    cd frontend && yarn build && cd ..
    pm2 restart all --update-env

Idempotent : peut être relancé sans risque (vérifie l'existence avant de patcher).
"""
import os
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path("/var/www/metro-taxi-app")
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

if not ROOT.exists():
    print(f"❌ {ROOT} introuvable. Lance ce script depuis le VPS Hostinger.")
    sys.exit(1)


def log(msg, status="•"):
    icons = {"ok": "✅", "skip": "⏭️ ", "warn": "⚠️ ", "err": "❌", "•": "🔧"}
    print(f"{icons.get(status, '•')} {msg}")


def backup(path: Path):
    if path.exists():
        bk = path.with_suffix(path.suffix + f".bak-{datetime.now():%Y%m%d-%H%M%S}")
        shutil.copy2(path, bk)


# ============================================================
# 1. services/sogecommerce.py
# ============================================================
SOGE_SERVICE = '''"""
Sogecommerce (Société Générale / vads-payment) — Signature & Helpers
Algo officiel HMAC-SHA-256 (Lyra/Systempay).
"""
import base64
import hashlib
import hmac
import os
from typing import Dict


def compute_vads_signature(fields: Dict[str, str], key: str) -> str:
    vads_items = [(k, v) for k, v in fields.items() if k.startswith("vads_")]
    vads_items.sort(key=lambda kv: kv[0])
    joined_values = "+".join(str(v) for _, v in vads_items)
    message = f"{joined_values}+{key}"
    digest = hmac.new(key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def verify_vads_signature(fields: Dict[str, str], received_signature: str, key: str) -> bool:
    if not received_signature:
        return False
    expected = compute_vads_signature(fields, key)
    return hmac.compare_digest(expected, received_signature)


def get_active_key() -> str:
    mode = (os.environ.get("SOGECOMMERCE_MODE") or "TEST").upper()
    if mode == "PRODUCTION":
        key = os.environ.get("SOGECOMMERCE_PROD_KEY")
        if not key:
            raise RuntimeError("SOGECOMMERCE_PROD_KEY manquante en mode PRODUCTION")
        return key
    key = os.environ.get("SOGECOMMERCE_TEST_KEY")
    if not key:
        raise RuntimeError("SOGECOMMERCE_TEST_KEY manquante (mode TEST)")
    return key


def get_ctx_mode() -> str:
    mode = (os.environ.get("SOGECOMMERCE_MODE") or "TEST").upper()
    return "PRODUCTION" if mode == "PRODUCTION" else "TEST"


def get_shop_id() -> str:
    shop_id = os.environ.get("SOGECOMMERCE_SHOP_ID")
    if not shop_id:
        raise RuntimeError("SOGECOMMERCE_SHOP_ID manquant")
    return shop_id


def get_payment_url() -> str:
    return os.environ.get(
        "SOGECOMMERCE_PAYMENT_URL",
        "https://sogecommerce.societegenerale.eu/vads-payment/",
    )
'''


def step1_soge_service():
    p = BACKEND / "services" / "sogecommerce.py"
    if p.exists() and "compute_vads_signature" in p.read_text():
        log(f"sogecommerce.py déjà présent — overwrite pour sécuriser la version", "skip")
    p.write_text(SOGE_SERVICE)
    log(f"services/sogecommerce.py écrit ({p.stat().st_size} bytes)", "ok")


# ============================================================
# 2. routes/sogecommerce.py
# ============================================================
SOGE_ROUTES_PATH = Path(__file__).parent / "_soge_routes_content.py"

# Le contenu est embarqué directement
SOGE_ROUTES = '''"""Routes paiement Sogecommerce."""
from datetime import datetime, timezone, timedelta
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from database import db
from services.auth import get_current_user
from services.emails import send_subscription_confirmation_email
from services.sogecommerce import (
    compute_vads_signature, verify_vads_signature,
    get_active_key, get_ctx_mode, get_shop_id, get_payment_url,
)
from routes.auto_campaigns import attempt_auto_attribution

router = APIRouter(prefix="/api/payments/sogecommerce", tags=["sogecommerce"])
logger = logging.getLogger(__name__)

CURRENCY_NUM = {"EUR": "978", "GBP": "826", "USD": "840"}


class SogeCheckoutRequest(BaseModel):
    plan_id: str
    region_id: str
    origin_url: str


def _short_trans_id() -> str:
    ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    return str(ms)[-6:]


@router.post("/checkout")
async def create_sogecommerce_checkout(data: SogeCheckoutRequest, request: Request, current_user: dict = Depends(get_current_user)):
    from server import SUBSCRIPTION_PLANS, REGIONAL_PRICING
    if data.plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Plan invalide")
    region = await db.regions.find_one({"id": data.region_id, "is_active": True})
    if not region:
        raise HTTPException(status_code=400, detail="Région non disponible")

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
    now_utc = datetime.now(timezone.utc)
    trans_date = now_utc.strftime("%Y%m%d%H%M%S")
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
        "vads_ext_info_plan_id": data.plan_id,
        "vads_ext_info_region_id": data.region_id,
        "vads_ext_info_user_id": user_id,
    }
    signature = compute_vads_signature(fields, get_active_key())

    await db.payment_transactions.insert_one({
        "id": str(uuid.uuid4()), "provider": "sogecommerce", "order_id": order_id,
        "trans_id": trans_id, "trans_date": trans_date, "user_id": user_id,
        "plan_id": data.plan_id, "region_id": data.region_id, "amount_cents": price_cents,
        "currency": currency_code, "ctx_mode": fields["vads_ctx_mode"],
        "status": "pending", "payment_status": "initiated",
        "created_at": now_utc.isoformat(),
    })
    return {"action_url": get_payment_url(), "fields": {**fields, "signature": signature}, "order_id": order_id}


@router.post("/ipn")
async def sogecommerce_ipn(request: Request):
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

    transaction = await db.payment_transactions.find_one(
        {"order_id": order_id, "provider": "sogecommerce"}, {"_id": 0}
    )
    if not transaction:
        logger.error(f"Sogecommerce IPN: transaction inconnue order_id={order_id}")
        return "OK"

    await db.payment_transactions.update_one(
        {"order_id": order_id, "provider": "sogecommerce"},
        {"$set": {"trans_uuid": trans_uuid, "trans_status": trans_status,
                  "ipn_received_at": datetime.now(timezone.utc).isoformat(),
                  "payment_status": trans_status}},
    )

    success_statuses = {"AUTHORISED", "CAPTURED", "ACCEPTED"}
    if trans_status not in success_statuses:
        return "OK"
    if transaction.get("status") == "completed":
        return "OK"

    from server import SUBSCRIPTION_PLANS
    plan = SUBSCRIPTION_PLANS.get(plan_id)
    if not plan:
        return "OK"

    now = datetime.now(timezone.utc)
    user = await db.users.find_one({"id": user_id})
    if not user:
        return "OK"

    existing_subs = user.get("subscriptions", []) or []
    base_date = now
    for sub in existing_subs:
        if sub.get("region_id") == region_id:
            try:
                existing_expires = datetime.fromisoformat(
                    str(sub.get("expires_at", "")).replace("Z", "+00:00"))
                if existing_expires > now:
                    base_date = existing_expires
            except (ValueError, TypeError):
                pass
            break

    expires_at = base_date + timedelta(hours=plan["duration_hours"])
    new_subscription = {
        "region_id": region_id, "plan_id": plan_id,
        "expires_at": expires_at.isoformat(), "is_active": True,
        "payment_method": "sogecommerce", "created_at": now.isoformat(),
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
        {"$set": {"subscriptions": existing_subs, "subscription_active": True,
                  "subscription_expires": expires_at.isoformat(),
                  "subscription_plan": plan_id}},
    )
    await db.payment_transactions.update_one(
        {"order_id": order_id, "provider": "sogecommerce"},
        {"$set": {"status": "completed"}},
    )

    u_camp = await db.users.find_one({"id": user_id}, {"_id": 0, "signup_campaign": 1})
    if u_camp and u_camp.get("signup_campaign"):
        try:
            await attempt_auto_attribution(user_id, u_camp["signup_campaign"])
        except Exception as exc:
            logger.warning(f"Auto-attribution échouée: {exc}")

    region = await db.regions.find_one({"id": region_id}, {"_id": 0})
    region_name = (region or {}).get("name", region_id)
    user_lang = (region or {}).get("language", "fr")
    try:
        await send_subscription_confirmation_email(
            user.get("email"), user.get("first_name", ""),
            f"{plan['name']} - {region_name}",
            expires_at.strftime("%d/%m/%Y à %H:%M"), user_lang)
    except Exception as exc:
        logger.warning(f"Email confirmation échoué: {exc}")

    logger.info(f"✅ Sogecommerce abo activé user={user_id} order={order_id}")
    return "OK"


@router.get("/return")
async def sogecommerce_return(request: Request):
    order_id = request.query_params.get("order_id") or request.query_params.get("vads_order_id")
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id manquant")
    tx = await db.payment_transactions.find_one(
        {"order_id": order_id, "provider": "sogecommerce"}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction inconnue")
    return {
        "order_id": order_id, "status": tx.get("status"),
        "payment_status": tx.get("payment_status"),
        "trans_status": tx.get("trans_status"),
        "amount_cents": tx.get("amount_cents"), "currency": tx.get("currency"),
        "plan_id": tx.get("plan_id"), "region_id": tx.get("region_id"),
    }
'''


def step2_soge_routes():
    p = BACKEND / "routes" / "sogecommerce.py"
    p.write_text(SOGE_ROUTES)
    log(f"routes/sogecommerce.py écrit ({p.stat().st_size} bytes)", "ok")


# ============================================================
# 3. server.py — enregistrement router Sogecommerce + admin_public_router
# ============================================================
def step3_server_py():
    p = BACKEND / "server.py"
    if not p.exists():
        log("server.py introuvable — abandon", "err")
        return
    backup(p)
    content = p.read_text()
    changed = False

    if "from routes.sogecommerce import router as sogecommerce_router" not in content:
        content = content.replace(
            "from routes.payments import router as payments_router",
            "from routes.payments import router as payments_router\nfrom routes.sogecommerce import router as sogecommerce_router",
            1,
        )
        changed = True
        log("server.py : import sogecommerce_router ajouté", "ok")

    if "app.include_router(sogecommerce_router)" not in content:
        content = content.replace(
            "app.include_router(payments_router)",
            "app.include_router(payments_router)\napp.include_router(sogecommerce_router)",
            1,
        )
        changed = True
        log("server.py : include_router(sogecommerce_router) ajouté", "ok")

    if "from routes.admin import public_router as admin_public_router" not in content:
        content = content.replace(
            "from routes.admin import router as admin_router",
            "from routes.admin import router as admin_router\nfrom routes.admin import public_router as admin_public_router",
            1,
        )
        changed = True
        log("server.py : import admin_public_router ajouté", "ok")

    if "app.include_router(admin_public_router)" not in content:
        content = content.replace(
            "app.include_router(admin_router)",
            "app.include_router(admin_router)\napp.include_router(admin_public_router)",
            1,
        )
        changed = True
        log("server.py : include_router(admin_public_router) ajouté", "ok")

    if changed:
        p.write_text(content)
    else:
        log("server.py déjà patché", "skip")


# ============================================================
# 4. backend/.env — variables Sogecommerce
# ============================================================
SOGE_ENV_VARS = """
SOGECOMMERCE_SHOP_ID=43696939
SOGECOMMERCE_TEST_KEY=uqhmpvNV0v45QpNI
SOGECOMMERCE_PROD_KEY=
SOGECOMMERCE_MODE=TEST
SOGECOMMERCE_PAYMENT_URL=https://sogecommerce.societegenerale.eu/vads-payment/
"""


def step4_env():
    p = BACKEND / ".env"
    if not p.exists():
        log(".env introuvable — abandon", "err")
        return
    content = p.read_text()
    if "SOGECOMMERCE_SHOP_ID" in content:
        log(".env contient déjà SOGECOMMERCE_* — pas de doublon", "skip")
        return
    backup(p)
    if not content.endswith("\n"):
        content += "\n"
    content += SOGE_ENV_VARS
    p.write_text(content)
    log(".env : 5 variables SOGECOMMERCE_* ajoutées", "ok")


# ============================================================
# 5. frontend/src/pages/Subscription.js — bouton Société Générale
# ============================================================
SOGE_FRONTEND_FUNC = """
  // Sogecommerce (Société Générale) Payment - auto-submit POST to vads-payment
  const handleSogecommerceSubscribe = async (planId) => {
    if (!selectedRegion) {
      toast.error(t('regions.regionRequired', 'Please select a region first'));
      return;
    }
    setLoading(planId);
    try {
      const originUrl = window.location.origin;
      const response = await axios.post(`${API}/payments/sogecommerce/checkout`, {
        plan_id: planId,
        region_id: selectedRegion.id,
        origin_url: originUrl
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const { action_url, fields } = response.data;
      if (!action_url || !fields) {
        toast.error('Erreur: payload Sogecommerce incomplet');
        setLoading(null);
        return;
      }
      setIsRedirecting(true);
      toast.success(t('subscription.redirectingSG', 'Redirection vers Société Générale...'));
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = action_url;
      form.style.display = 'none';
      Object.entries(fields).forEach(([name, value]) => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        input.value = value == null ? '' : String(value);
        form.appendChild(input);
      });
      document.body.appendChild(form);
      setTimeout(() => form.submit(), 200);
    } catch (error) {
      console.error('Sogecommerce checkout error:', error);
      const message = error.response?.data?.detail || 'Erreur Sogecommerce';
      toast.error(message);
      setLoading(null);
      setIsRedirecting(false);
    }
  };

  // SEPA Payment functions"""

SOGE_FRONTEND_BTN = """              )}

              {/* Sogecommerce (Société Générale) Button - Only for EUR regions */}
              {selectedRegion?.currency === 'EUR' && (
                <Button
                  variant="outline"
                  onClick={() => handleSogecommerceSubscribe(plan.id)}
                  disabled={loading !== null || isRedirecting || sepaLoading}
                  className={`w-full h-10 mt-2 text-sm border-red-700/40 text-red-200 hover:bg-red-950/40 ${(loading !== null || isRedirecting || sepaLoading) ? 'opacity-50 cursor-not-allowed' : ''}`}
                  data-testid={`sogecommerce-${plan.id}-btn`}
                  title="Paiement sécurisé Société Générale (Apple Pay supporté)"
                >
                  <CreditCard className="w-4 h-4 mr-2" />
                  Payer avec Société Générale
                </Button>
              )}"""


def step5_frontend_subscription():
    p = FRONTEND / "src" / "pages" / "Subscription.js"
    if not p.exists():
        log("Subscription.js introuvable — abandon", "err")
        return
    content = p.read_text()
    changed = False

    if "handleSogecommerceSubscribe" not in content:
        # Insertion avant "// SEPA Payment functions"
        if "// SEPA Payment functions" in content:
            backup(p)
            content = content.replace("  // SEPA Payment functions", SOGE_FRONTEND_FUNC, 1)
            changed = True
            log("Subscription.js : fonction handleSogecommerceSubscribe ajoutée", "ok")
        else:
            log("Subscription.js : ancre '// SEPA Payment functions' introuvable", "warn")

    if 'data-testid={`sogecommerce-' not in content and "handleSogecommerceSubscribe" in content:
        # Insertion bouton — on cherche le bouton SEPA existant
        marker_sepa_end = """                  {t('sepa.payWithSepa', 'Payer par prélèvement SEPA')}
                </Button>
              )}"""
        if marker_sepa_end in content:
            content = content.replace(marker_sepa_end, marker_sepa_end[:-3] + SOGE_FRONTEND_BTN, 1)
            changed = True
            log("Subscription.js : bouton Société Générale ajouté sous SEPA", "ok")
        else:
            log("Subscription.js : ancre bouton SEPA introuvable, bouton non ajouté", "warn")

    if changed:
        p.write_text(content)
    elif "handleSogecommerceSubscribe" in content:
        log("Subscription.js déjà patché", "skip")


# ============================================================
# 6. services/emails.py — fonction send_driver_presence_survey_email
# ============================================================
SURVEY_EMAIL_FUNC = '''async def send_driver_presence_survey_email(email: str, name: str, pioneer_number: int, response_token: str, base_url: str = "https://metro-taxi.com"):
    """Sondage de présence chauffeur pour le 13 juin. Boutons OUI/NON cliquables (token-based)."""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, presence survey email NOT sent")
        return False

    yes_url = f"{base_url}/api/driver-presence-survey/respond?token={response_token}&answer=yes"
    no_url = f"{base_url}/api/driver-presence-survey/respond?token={response_token}&answer=no"
    pioneer_badge = f"PIONNIER #{pioneer_number}" if pioneer_number else "CHAUFFEUR PIONNIER"

    html_content = f"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Helvetica,Arial,sans-serif;background:#0a0a0a;margin:0;padding:30px 20px;color:#fff;">
  <div style="max-width:600px;margin:0 auto;background:#1a1a1a;border-radius:12px;overflow:hidden;border-top:6px solid #FFD60A;">
    <div style="background:#FFD60A;padding:24px;text-align:center;">
      <p style="margin:0 0 6px 0;color:#000;font-size:12px;font-weight:bold;letter-spacing:2px;">{pioneer_badge}</p>
      <h1 style="margin:0;color:#000;font-size:22px;">📋 SONDAGE PRÉSENCE — VENDREDI 13 JUIN</h1>
    </div>
    <div style="padding:32px 28px;">
      <h2 style="color:#FFD60A;font-size:20px;margin:0 0 16px 0;">Salut {name} 👋</h2>
      <p style="color:#e4e4e7;line-height:1.7;font-size:15px;margin:0 0 18px 0;">
        On y est presque : <strong style="color:#FFD60A">vendredi 13 juin 2026</strong>, ouverture officielle de Métro-Taxi à Saint-Denis.
      </p>
      <p style="color:#e4e4e7;line-height:1.7;font-size:15px;margin:0 0 24px 0;">
        Pour bien calibrer la jauge des <strong>30 courses offertes</strong> et savoir combien de VTC seront sur le terrain le Jour J, j'ai besoin de toi en <strong>30 secondes top chrono</strong> :
      </p>
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;border-radius:8px;border-left:4px solid #FFD60A;margin:0 0 28px 0;">
        <tr><td style="padding:20px 22px;">
          <p style="color:#fff;margin:0;font-size:16px;line-height:1.5;text-align:center;font-weight:bold;">
            🗓️ Es-tu disponible pour rouler<br>le <span style="color:#FFD60A">vendredi 13 juin 2026</span> ?
          </p>
        </td></tr>
      </table>
      <table width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;">
        <tr>
          <td align="center" width="50%" style="padding:0 8px;">
            <a href="{yes_url}" style="display:block;background:#22c55e;color:#fff;text-decoration:none;padding:18px 12px;border-radius:10px;font-weight:bold;font-size:16px;">✅ OUI je suis dispo</a>
          </td>
          <td align="center" width="50%" style="padding:0 8px;">
            <a href="{no_url}" style="display:block;background:#ef4444;color:#fff;text-decoration:none;padding:18px 12px;border-radius:10px;font-weight:bold;font-size:16px;">❌ NON indisponible</a>
          </td>
        </tr>
      </table>
      <p style="color:#a1a1aa;font-size:13px;line-height:1.6;margin:24px 0 0 0;text-align:center;font-style:italic;">
        1 clic suffit. Aucun mot de passe, aucun formulaire. Tu peux changer ta réponse en re-cliquant.
      </p>
      <hr style="border:none;border-top:1px solid #333;margin:28px 0 20px 0;">
      <p style="color:#cccccc;line-height:1.7;font-size:14px;margin:0 0 14px 0;">
        Si tu réponds NON, aucun souci — préviens-moi juste par WhatsApp <strong style="color:#FFD60A">06 05 78 64 25</strong> pour qu'on cale ton retour sur la semaine suivante.
      </p>
      <p style="color:#FFD60A;font-size:14px;margin:20px 0 0 0;">
        Merci Champion 🚖<br><strong>— Judée, fondateur Métro-Taxi</strong>
      </p>
    </div>
    <div style="background:#09090b;padding:16px 24px;text-align:center;border-top:1px solid #27272a;">
      <p style="color:#52525b;margin:0;font-size:11px;">© 2026 Métro-Taxi — Sondage de présence chauffeurs zone Saint-Denis</p>
    </div>
  </div>
</body></html>
"""
    try:
        params = {
            "from": SENDER_EMAIL, "to": [email],
            "subject": "📋 30 sec : tu roules le 13 juin ? (1 clic OUI/NON)",
            "html": html_content, "reply_to": "judeemane@hotmail.com",
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        result_id = result.get("id")
        logging.info(f"Presence survey email sent to {email} (#{pioneer_number}), ID: {result_id}")
        return True
    except Exception as e:
        logging.error(f"Failed to send presence survey to {email}: {str(e)}")
        return False


'''


def step6_emails_survey_func():
    p = BACKEND / "services" / "emails.py"
    if not p.exists():
        log("emails.py introuvable — abandon", "err")
        return
    content = p.read_text()
    if "send_driver_presence_survey_email" in content:
        log("emails.py : send_driver_presence_survey_email déjà présent", "skip")
        return
    backup(p)
    # Insère juste avant le marker "send_admin_personal_email"
    marker = "# ============================================\n# EMAIL PERSO ADMIN → CHAUFFEUR"
    if marker in content:
        content = content.replace(marker, SURVEY_EMAIL_FUNC + marker, 1)
        p.write_text(content)
        log("emails.py : fonction send_driver_presence_survey_email ajoutée", "ok")
    else:
        # Fallback : ajouter à la fin
        if not content.endswith("\n"):
            content += "\n"
        content += "\n\n" + SURVEY_EMAIL_FUNC
        p.write_text(content)
        log("emails.py : fonction ajoutée en fin de fichier", "ok")


# ============================================================
# 7. routes/admin.py — endpoints sondage + public_router
# ============================================================
ADMIN_SURVEY_BLOCK = '''

# ============================================================
# 📋 BROADCAST #4 — Sondage présence chauffeurs 13 juin
# ============================================================

@router.get("/admin/broadcast/driver-presence-survey/preview")
async def driver_presence_survey_preview(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    cursor = db.drivers.find(
        {"is_validated": True},
        {"_id": 0, "id": 1, "first_name": 1, "email": 1, "pioneer_number": 1}
    )
    drivers = await cursor.to_list(length=500)
    return {
        "subject": "📋 30 sec : tu roules le 13 juin ? (1 clic OUI/NON)",
        "recipient_count": len(drivers),
        "criteria": "drivers WHERE is_validated=True",
        "ready": len(drivers) > 0,
    }


@router.post("/admin/broadcast/driver-presence-survey/test")
async def driver_presence_survey_test(payload: BroadcastTestPayload, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    if not payload.test_email or "@" not in payload.test_email:
        raise HTTPException(status_code=400, detail="Email de test invalide")
    test_token = "test-" + uuid.uuid4().hex[:16]
    sent = await send_driver_presence_survey_email(
        email=payload.test_email, name="Capitaine (TEST)", pioneer_number=0,
        response_token=test_token,
        base_url=os.environ.get("FRONTEND_URL", "https://metro-taxi.com"),
    )
    if not sent:
        raise HTTPException(status_code=500, detail="Échec envoi email test")
    return {"status": "test_sent", "to": payload.test_email, "test_token": test_token}


@router.post("/admin/broadcast/driver-presence-survey/confirm")
async def driver_presence_survey_confirm(payload: BroadcastConfirmPayload, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    if payload.confirmation_phrase != "GO 13 JUIN":
        raise HTTPException(status_code=400, detail="Phrase de confirmation invalide. Envoie exactement: 'GO 13 JUIN'")
    cursor = db.drivers.find(
        {"is_validated": True},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1, "pioneer_number": 1}
    )
    drivers = await cursor.to_list(length=500)
    if not drivers:
        raise HTTPException(status_code=404, detail="Aucun chauffeur éligible")
    if payload.dry_run:
        return {"status": "dry_run", "would_send_to": len(drivers)}

    base_url = os.environ.get("FRONTEND_URL", "https://metro-taxi.com")
    survey_id = str(uuid.uuid4())
    results = {"sent": [], "failed": []}

    for d in drivers:
        email = d.get("email")
        name = d.get("first_name", "Chauffeur")
        pioneer_number = d.get("pioneer_number")
        driver_id = d.get("id")
        token = uuid.uuid4().hex
        await db.driver_presence_surveys.insert_one({
            "token": token, "survey_id": survey_id, "driver_id": driver_id,
            "driver_email": email, "driver_name": name, "pioneer_number": pioneer_number,
            "target_date": "2026-06-13", "answer": None, "responded_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        try:
            ok = await send_driver_presence_survey_email(
                email=email, name=name, pioneer_number=pioneer_number,
                response_token=token, base_url=base_url)
            if ok:
                results["sent"].append({"email": email, "pioneer_number": pioneer_number})
            else:
                results["failed"].append({"email": email, "reason": "send returned False"})
        except Exception as e:
            results["failed"].append({"email": email, "reason": str(e)})
        await asyncio.sleep(0.2)

    await db.broadcast_logs.insert_one({
        "broadcast_id": survey_id, "type": "driver_presence_survey_2026_06_13",
        "sent_at": datetime.now(timezone.utc),
        "sent_by": current_user.get("email", "unknown"),
        "total_targeted": len(drivers), "sent_count": len(results["sent"]),
        "failed_count": len(results["failed"]), "failures": results["failed"],
    })
    return {
        "status": "broadcast_done", "survey_id": survey_id,
        "total_targeted": len(drivers), "sent_count": len(results["sent"]),
        "failed_count": len(results["failed"]),
    }


@router.get("/admin/broadcast/driver-presence-survey/results")
async def driver_presence_survey_results(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    cursor = db.driver_presence_surveys.find({}, {"_id": 0})
    surveys = await cursor.to_list(length=500)
    yes_list, no_list, pending_list = [], [], []
    for s in surveys:
        item = {
            "name": s.get("driver_name"), "email": s.get("driver_email"),
            "pioneer_number": s.get("pioneer_number"),
            "responded_at": s.get("responded_at"),
        }
        if s.get("answer") == "yes":
            yes_list.append(item)
        elif s.get("answer") == "no":
            no_list.append(item)
        else:
            pending_list.append(item)
    return {
        "total_sent": len(surveys), "yes_count": len(yes_list),
        "no_count": len(no_list), "pending_count": len(pending_list),
        "response_rate_pct": round(100 * (len(yes_list) + len(no_list)) / len(surveys), 1) if surveys else 0,
        "available_for_june_13": len(yes_list),
        "yes_list": yes_list, "no_list": no_list, "pending_list": pending_list,
    }


public_router = APIRouter(prefix="/api", tags=["public-survey"])


@public_router.get("/driver-presence-survey/respond")
async def respond_driver_presence_survey(token: str, answer: str):
    if answer not in ("yes", "no"):
        raise HTTPException(status_code=400, detail="answer doit être 'yes' ou 'no'")
    survey = await db.driver_presence_surveys.find_one({"token": token}, {"_id": 0})
    if not survey:
        return _survey_html_response(
            "Lien invalide ou expiré",
            "Ce lien ne correspond à aucun sondage actif. Contacte Judée au 06 05 78 64 25.",
            status="error")
    await db.driver_presence_surveys.update_one(
        {"token": token},
        {"$set": {"answer": answer,
                  "responded_at": datetime.now(timezone.utc).isoformat()}})
    name = survey.get("driver_name", "Champion")
    if answer == "yes":
        title = f"Merci {name} ! ✅"
        message = "C'est noté : tu es dispo le <strong>vendredi 13 juin 2026</strong>. À très vite sur la route 🚖"
        status = "yes"
    else:
        title = f"OK {name}, c'est noté ❌"
        message = "Pas de souci. Tu peux changer d'avis en recliquant sur OUI dans le mail. Contacte Judée au 06 05 78 64 25 pour ajuster."
        status = "no"
    return _survey_html_response(title, message, status=status)


def _survey_html_response(title: str, message: str, status: str = "yes"):
    from fastapi.responses import HTMLResponse
    color = {"yes": "#22c55e", "no": "#ef4444", "error": "#71717a"}.get(status, "#FFD60A")
    icon = {"yes": "✅", "no": "❌", "error": "⚠️"}.get(status, "ℹ️")
    html = f"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Métro-Taxi — Sondage 13 juin</title></head>
<body style="font-family:Helvetica,Arial,sans-serif;background:#0a0a0a;margin:0;padding:30px 20px;color:#fff;min-height:100vh;display:flex;align-items:center;justify-content:center;">
  <div style="max-width:500px;width:100%;background:#1a1a1a;border-radius:12px;border-top:6px solid {color};padding:36px 28px;text-align:center;">
    <div style="font-size:64px;margin-bottom:16px;">{icon}</div>
    <h1 style="color:{color};margin:0 0 16px 0;font-size:24px;">{title}</h1>
    <p style="color:#cccccc;line-height:1.7;font-size:15px;margin:0 0 24px 0;">{message}</p>
    <hr style="border:none;border-top:1px solid #27272a;margin:24px 0;">
    <p style="color:#71717a;font-size:13px;margin:0;">© 2026 Métro-Taxi — Saint-Denis 13 juin 2026</p>
  </div>
</body></html>
"""
    return HTMLResponse(content=html, status_code=200)
'''


def step7_admin_survey_endpoints():
    p = BACKEND / "routes" / "admin.py"
    if not p.exists():
        log("admin.py introuvable — abandon", "err")
        return
    content = p.read_text()
    if "driver_presence_survey_preview" in content:
        log("admin.py : endpoints sondage déjà présents", "skip")
        return
    backup(p)

    # 1. Étendre l'import emails pour inclure send_driver_presence_survey_email
    if "send_driver_presence_survey_email" not in content:
        content = re.sub(
            r"(from services\\.emails import [^\\n]+)",
            lambda m: m.group(1) + ", send_driver_presence_survey_email"
            if "send_driver_presence_survey_email" not in m.group(1)
            else m.group(1),
            content, count=1)

    # 2. Append survey block at end
    if not content.endswith("\n"):
        content += "\n"
    content += ADMIN_SURVEY_BLOCK
    p.write_text(content)
    log("admin.py : endpoints sondage + public_router ajoutés", "ok")


# ============================================================
# 8. Cleanup mentions Uber/Bolt dans emails.py
# ============================================================
def step8_cleanup_competitors():
    p = BACKEND / "services" / "emails.py"
    if not p.exists():
        return
    content = p.read_text()
    original = content
    # Remplacements neutres (case-insensitive)
    replacements = [
        (re.compile(r"\\bUber\\b", re.IGNORECASE), "plateformes concurrentes"),
        (re.compile(r"\\bBolt\\b", re.IGNORECASE), "plateformes concurrentes"),
    ]
    hits = 0
    for pattern, replacement in replacements:
        new_content, count = pattern.subn(replacement, content)
        hits += count
        content = new_content
    if hits == 0:
        log("Cleanup Uber/Bolt : aucune occurrence trouvée (emails.py déjà propre)", "skip")
        return
    backup(p)
    p.write_text(content)
    log(f"Cleanup Uber/Bolt : {hits} occurrence(s) remplacée(s) dans emails.py", "ok")


# ============================================================
# MAIN
# ============================================================
def main():
    print("\\n" + "=" * 70)
    print("  PATCH v5 — Sogecommerce + Sondage 13 juin + Cleanup")
    print("=" * 70 + "\\n")
    step1_soge_service()
    step2_soge_routes()
    step3_server_py()
    step4_env()
    step5_frontend_subscription()
    step6_emails_survey_func()
    step7_admin_survey_endpoints()
    step8_cleanup_competitors()
    print("\\n" + "=" * 70)
    print("  ✅ PATCH v5 APPLIQUÉ — Prochaines étapes :")
    print("=" * 70)
    print("    1. cd /var/www/metro-taxi-app/frontend && yarn build && cd ..")
    print("    2. pm2 restart all --update-env")
    print("    3. Tester l'admin : POST /api/admin/broadcast/driver-presence-survey/preview")
    print("=" * 70 + "\\n")


if __name__ == "__main__":
    main()
