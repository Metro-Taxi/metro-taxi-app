#!/usr/bin/env python3
"""
PATCH v8 — Auto-attribution par région + Cleanup Stripe frontend
================================================================

Modifications :
  1. backend/routes/auto_campaigns.py : ajout fonction auto_attribute_for_region()
  2. backend/routes/payments.py       : appel fallback région après Stripe & SEPA
  3. backend/routes/sogecommerce.py   : appel fallback région après Sogecommerce
  4. frontend/Subscription.js         : retrait bouton "S'ABONNER" doré (Stripe)
  5. frontend/DriverEarnings.js       : retrait onglet "Compte Stripe"

Usage:
    cd /var/www/metro-taxi-app
    curl -fsSL https://metro-taxi-demo.preview.emergentagent.com/patch_v8_auto_attrib_region.py -o /tmp/patch_v8.py
    python3 /tmp/patch_v8.py
    cd frontend && yarn build && cd ..
    pm2 restart all --update-env
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path("/var/www/metro-taxi-app")
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def log(msg, status="ok"):
    icons = {"ok": "✅", "skip": "⏭️ ", "warn": "⚠️ ", "err": "❌"}
    print(f"{icons.get(status, '•')} {msg}")


def backup(path: Path):
    if path.exists():
        bk = path.with_suffix(path.suffix + f".bak-{datetime.now():%Y%m%d-%H%M%S}")
        shutil.copy2(path, bk)
        return bk
    return None


# =========================================================
# 1. auto_campaigns.py — ajout fonction auto_attribute_for_region
# =========================================================
REGION_FUNC_SIGNATURE = "async def auto_attribute_for_region"
REGION_FUNC_CODE = '''

# -----------------------------------------------------------------------------
# HELPER — Auto-attribution par RÉGION (fallback si pas de signup_campaign)
# -----------------------------------------------------------------------------
async def auto_attribute_for_region(user_id: str, region_id: str):
    """Cherche une campagne auto-attribution active pour cette région et tente
    l'attribution. Permet aux flyers/posts sans lien magique de fonctionner.
    """
    if not region_id:
        return None

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
        sort=[("created_at", -1)],
    )
    if not camp:
        return None

    return await attempt_auto_attribution(user_id, camp["campaign_id"])
'''


def step1_auto_campaigns():
    p = BACKEND / "routes" / "auto_campaigns.py"
    if not p.exists():
        log(f"{p} introuvable — abandon", "err")
        return False
    content = p.read_text()
    if REGION_FUNC_SIGNATURE in content:
        log("auto_campaigns.py : auto_attribute_for_region déjà présente", "skip")
        return True
    backup(p)
    if not content.endswith("\n"):
        content += "\n"
    content += REGION_FUNC_CODE
    p.write_text(content)
    log("auto_campaigns.py : fonction auto_attribute_for_region ajoutée", "ok")
    return True


# =========================================================
# 2. payments.py — fallback région après Stripe + SEPA
# =========================================================
PAYMENTS_OLD_STRIPE = """                        # Auto-attribution promo si l'usager fait partie d'une campagne Saint-Denis & co.
                        u_camp = await db.users.find_one({"id": transaction["user_id"]}, {"_id": 0, "signup_campaign": 1})
                        if u_camp and u_camp.get("signup_campaign"):
                            await attempt_auto_attribution(transaction["user_id"], u_camp["signup_campaign"])"""

PAYMENTS_NEW_STRIPE = """                        # Auto-attribution promo si l'usager fait partie d'une campagne Saint-Denis & co.
                        u_camp = await db.users.find_one({"id": transaction["user_id"]}, {"_id": 0, "signup_campaign": 1})
                        if u_camp and u_camp.get("signup_campaign"):
                            await attempt_auto_attribution(transaction["user_id"], u_camp["signup_campaign"])
                        else:
                            # Fallback : auto-attribution par région
                            from routes.auto_campaigns import auto_attribute_for_region
                            await auto_attribute_for_region(transaction["user_id"], region_id)"""

PAYMENTS_OLD_SEPA = """                            # Auto-attribution promo si l'usager fait partie d'une campagne
                            u_camp = await db.users.find_one({"id": user_id}, {"_id": 0, "signup_campaign": 1})
                            if u_camp and u_camp.get("signup_campaign"):
                                await attempt_auto_attribution(user_id, u_camp["signup_campaign"])"""

PAYMENTS_NEW_SEPA = """                            # Auto-attribution promo si l'usager fait partie d'une campagne
                            u_camp = await db.users.find_one({"id": user_id}, {"_id": 0, "signup_campaign": 1})
                            if u_camp and u_camp.get("signup_campaign"):
                                await attempt_auto_attribution(user_id, u_camp["signup_campaign"])
                            else:
                                # Fallback : auto-attribution par région
                                from routes.auto_campaigns import auto_attribute_for_region
                                await auto_attribute_for_region(user_id, region_id)"""


def step2_payments():
    p = BACKEND / "routes" / "payments.py"
    if not p.exists():
        log("payments.py introuvable", "err")
        return False
    content = p.read_text()
    changed = False

    if "auto_attribute_for_region" in content:
        log("payments.py : fallback région déjà câblé", "skip")
        return True

    if PAYMENTS_OLD_STRIPE in content:
        content = content.replace(PAYMENTS_OLD_STRIPE, PAYMENTS_NEW_STRIPE, 1)
        changed = True
        log("payments.py : fallback région ajouté pour Stripe checkout", "ok")
    else:
        log("payments.py : ancre Stripe checkout introuvable (peut-être déjà patché)", "warn")

    if PAYMENTS_OLD_SEPA in content:
        content = content.replace(PAYMENTS_OLD_SEPA, PAYMENTS_NEW_SEPA, 1)
        changed = True
        log("payments.py : fallback région ajouté pour SEPA", "ok")
    else:
        log("payments.py : ancre SEPA introuvable (peut-être déjà patché)", "warn")

    if changed:
        backup(p)
        p.write_text(content)
    return True


# =========================================================
# 3. sogecommerce.py — fallback région
# =========================================================
SG_OLD = """    # Auto-attribution promo (campagne Saint-Denis & co.)
    u_camp = await db.users.find_one({"id": user_id}, {"_id": 0, "signup_campaign": 1})
    if u_camp and u_camp.get("signup_campaign"):
        try:
            await attempt_auto_attribution(user_id, u_camp["signup_campaign"])
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Auto-attribution échouée: {exc}")"""

SG_NEW = """    # Auto-attribution promo (campagne Saint-Denis & co.)
    u_camp = await db.users.find_one({"id": user_id}, {"_id": 0, "signup_campaign": 1})
    if u_camp and u_camp.get("signup_campaign"):
        try:
            await attempt_auto_attribution(user_id, u_camp["signup_campaign"])
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Auto-attribution échouée: {exc}")
    else:
        # Fallback : auto-attribution par région
        try:
            from routes.auto_campaigns import auto_attribute_for_region
            await auto_attribute_for_region(user_id, region_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Auto-attribution région échouée: {exc}")"""


def step3_sogecommerce():
    p = BACKEND / "routes" / "sogecommerce.py"
    if not p.exists():
        log("sogecommerce.py introuvable", "err")
        return False
    content = p.read_text()
    if "auto_attribute_for_region" in content:
        log("sogecommerce.py : fallback région déjà câblé", "skip")
        return True
    if SG_OLD not in content:
        log("sogecommerce.py : ancre introuvable", "warn")
        return False
    backup(p)
    content = content.replace(SG_OLD, SG_NEW, 1)
    p.write_text(content)
    log("sogecommerce.py : fallback région ajouté", "ok")
    return True


# =========================================================
# 4. Subscription.js — retrait bouton S'ABONNER doré (Stripe)
# =========================================================
SUB_OLD = """              <Button
                onClick={() => handleSubscribe(plan.id)}
                disabled={loading !== null || isRedirecting}
                className={`w-full h-12 font-bold ${
                  plan.popular 
                    ? 'bg-[#FFD60A] text-black hover:bg-[#E6C209]' 
                    : 'bg-zinc-800 text-white hover:bg-zinc-700'
                } ${(loading !== null || isRedirecting) ? 'opacity-50 cursor-not-allowed' : ''}`}
                data-testid={`subscribe-${plan.id}-btn`}
              >
                {loading === plan.id ? (
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    <span>{t('subscription.processing', 'Traitement...')}</span>
                  </div>
                ) : (loading !== null || isRedirecting) ? (
                  <span className="text-zinc-400">{t('subscription.pleaseWait', 'Veuillez patienter...')}</span>
                ) : (
                  <>
                    <CreditCard className="w-4 h-4 mr-2" />
                    {t('subscription.subscribeBtn', "S'ABONNER")}
                  </>
                )}
              </Button>
              
              {/* SEPA Button - Only for EUR regions */}"""

SUB_NEW = """              {/* Stripe button (S'ABONNER doré) removed — Sogecommerce + SEPA only since 2026-06-03 */}

              {/* SEPA Button - Only for EUR regions */}"""


def step4_subscription():
    p = FRONTEND / "src" / "pages" / "Subscription.js"
    if not p.exists():
        log("Subscription.js introuvable", "err")
        return False
    content = p.read_text()
    if "Stripe button (S'ABONNER doré) removed" in content:
        log("Subscription.js : bouton Stripe déjà retiré", "skip")
        return True
    if SUB_OLD not in content:
        log("Subscription.js : ancre Stripe button introuvable", "warn")
        return False
    backup(p)
    content = content.replace(SUB_OLD, SUB_NEW, 1)
    p.write_text(content)
    log("Subscription.js : bouton S'ABONNER doré (Stripe) retiré", "ok")
    return True


# =========================================================
# 5. DriverEarnings.js — retrait onglet Compte Stripe
# =========================================================
DE_OLD = """          <button
            onClick={() => setActiveTab('earnings')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'earnings' 
                ? 'bg-[#FFD60A] text-black' 
                : 'bg-zinc-800 text-zinc-400 hover:text-white'
            }`}
          >
            {t('driverEarnings.tabEarnings', 'Revenus')}
          </button>
          <button
            onClick={() => setActiveTab('stripe')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'stripe' 
                ? 'bg-[#FFD60A] text-black' 
                : 'bg-zinc-800 text-zinc-400 hover:text-white'
            }`}
          >
            {t('driverEarnings.tabStripe', 'Compte Stripe')}
          </button>
          <button
            onClick={() => setActiveTab('history')}"""

DE_NEW = """          <button
            onClick={() => setActiveTab('earnings')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'earnings' 
                ? 'bg-[#FFD60A] text-black' 
                : 'bg-zinc-800 text-zinc-400 hover:text-white'
            }`}
          >
            {t('driverEarnings.tabEarnings', 'Revenus')}
          </button>
          {/* Onglet Compte Stripe retiré le 2026-06-03 — paiements migrés vers Sogecommerce */}
          <button
            onClick={() => setActiveTab('history')}"""


def step5_driver_earnings():
    p = FRONTEND / "src" / "pages" / "DriverEarnings.js"
    if not p.exists():
        log("DriverEarnings.js introuvable", "err")
        return False
    content = p.read_text()
    if "Onglet Compte Stripe retiré" in content:
        log("DriverEarnings.js : onglet Stripe déjà retiré", "skip")
        return True
    if DE_OLD not in content:
        log("DriverEarnings.js : ancre onglet Stripe introuvable", "warn")
        return False
    backup(p)
    content = content.replace(DE_OLD, DE_NEW, 1)
    p.write_text(content)
    log("DriverEarnings.js : onglet 'Compte Stripe' retiré", "ok")
    return True


def main():
    print("\n" + "=" * 70)
    print("  PATCH v8 — Auto-attribution région + Cleanup Stripe")
    print("=" * 70 + "\n")

    step1_auto_campaigns()
    step2_payments()
    step3_sogecommerce()
    step4_subscription()
    step5_driver_earnings()

    print("\n" + "=" * 70)
    print("  ✅ PATCH v8 APPLIQUÉ — Prochaines étapes :")
    print("=" * 70)
    print("    1. cd /var/www/metro-taxi-app/frontend && yarn build && cd ..")
    print("    2. pm2 restart all --update-env")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
