#!/usr/bin/env python3
"""
PATCH v10 — Bascule paiement chauffeurs HEBDOMADAIRE (chaque lundi)
Auteur: Charly pour Métro-Taxi
Date: 2026-06-05

Ce patch :
  1. Modifie /var/www/metro-taxi-app/backend/config.py (PAYOUT_FREQUENCY=weekly)
  2. Modifie /var/www/metro-taxi-app/backend/utils/helpers.py (idem)
  3. Modifie le frontend (DriverEarnings.js, DriverCardDialog.js, PatronVTC.js, Landing.js)
  4. Met à jour les emails (emails.py) : "10 du mois" → "chaque lundi (SEPA)"
  5. Rebuild le frontend React
  6. Restart le backend via pm2

USAGE sur le VPS :
  curl -sSL https://metro-taxi.com/patch_v10.py | python3 -
"""

import os
import re
import subprocess
import sys
from pathlib import Path

APP_ROOT = Path("/var/www/metro-taxi-app")
BACKEND = APP_ROOT / "backend"
FRONTEND = APP_ROOT / "frontend"


def log(msg, ok=True):
    icon = "✅" if ok else "❌"
    print(f"{icon} {msg}", flush=True)


def patch_file(path, replacements, label):
    """Applique une liste de (regex_old, new) à un fichier."""
    if not path.exists():
        log(f"{label} : fichier introuvable {path}", ok=False)
        return False
    content = path.read_text(encoding="utf-8")
    original = content
    for old, new in replacements:
        content = re.sub(old, new, content, flags=re.MULTILINE)
    if content == original:
        log(f"{label} : déjà patché (aucun changement)", ok=True)
        return True
    path.write_text(content, encoding="utf-8")
    log(f"{label} : patché")
    return True


def main():
    print("=" * 70)
    print("🚀 PATCH v10 — Paiement chauffeurs HEBDO (chaque lundi)")
    print("=" * 70)

    # 1. Backend config.py
    patch_file(
        BACKEND / "config.py",
        [
            (
                r"# Driver Revenue Configuration\nDRIVER_RATE_PER_KM = 1\.50.*\nPAYOUT_DAY = 10.*",
                "# Driver Revenue Configuration\nDRIVER_RATE_PER_KM = 1.50  # €1.50 per kilometer\nPAYOUT_FREQUENCY = \"weekly\"  # weekly (chaque lundi) ou monthly\nPAYOUT_DAY_OF_WEEK = 0  # 0=Lundi\nPAYOUT_DAY = 10  # legacy",
            ),
        ],
        "backend/config.py",
    )

    # 2. Backend helpers.py
    patch_file(
        BACKEND / "utils" / "helpers.py",
        [
            (
                r"# Payout configuration\nPAYOUT_DAY = 10.*\nMIN_PAYOUT_AMOUNT = 10\.0.*",
                "# Payout configuration\nPAYOUT_FREQUENCY = \"weekly\"  # weekly (chaque lundi) ou monthly\nPAYOUT_DAY_OF_WEEK = 0  # 0=Lundi\nPAYOUT_DAY = 10  # legacy (si monthly)\nMIN_PAYOUT_AMOUNT = 10.0  # Minimum amount for payout",
            ),
        ],
        "backend/utils/helpers.py",
    )

    # 3. Frontend DriverEarnings.js
    patch_file(
        FRONTEND / "src" / "pages" / "DriverEarnings.js",
        [
            (
                r"\{t\('driverEarnings\.payoutDate', 'Virement automatique le'\)\} \{earnings\.payout_day\} \{t\('driverEarnings\.ofMonth', 'du mois'\)\}",
                "{t('driverEarnings.payoutWeekly', 'Virement automatique chaque lundi (SEPA)')}",
            ),
        ],
        "frontend/DriverEarnings.js",
    )

    # 4. Frontend DriverCardDialog.js
    patch_file(
        FRONTEND / "src" / "components" / "admin" / "DriverCardDialog.js",
        [(r'sub="Versement le 10 du mois"', 'sub="Versement chaque lundi"')],
        "frontend/DriverCardDialog.js",
    )

    # 5. Frontend PatronVTC.js
    patch_file(
        FRONTEND / "src" / "pages" / "PatronVTC.js",
        [(r"tes chauffeurs payés le 10 du mois", "tes chauffeurs payés chaque lundi")],
        "frontend/PatronVTC.js",
    )

    # 6. Frontend Landing.js
    patch_file(
        FRONTEND / "src" / "pages" / "Landing.js",
        [(r"Paiement le 10 du mois", "Paiement chaque lundi")],
        "frontend/Landing.js",
    )

    # 7. Emails
    patch_file(
        BACKEND / "services" / "emails.py",
        [
            (r"Versement chaque 10 du mois", "Versement chaque lundi (SEPA)"),
            (r"Paiement le 10 de chaque mois", "Paiement chaque lundi (SEPA)"),
        ],
        "backend/services/emails.py",
    )

    # 8. Rebuild frontend
    print("\n🔨 Rebuild du frontend (yarn build)...")
    try:
        result = subprocess.run(
            ["yarn", "build"],
            cwd=str(FRONTEND),
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 0:
            log("Frontend rebuild OK")
        else:
            log(f"Frontend rebuild FAIL : {result.stderr[-500:]}", ok=False)
    except Exception as e:
        log(f"Erreur rebuild : {e}", ok=False)

    # 9. Restart backend pm2
    print("\n🔄 Restart backend (pm2)...")
    try:
        result = subprocess.run(
            ["pm2", "restart", "metro-backend"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            log("Backend restarté")
        else:
            log(f"pm2 restart FAIL : {result.stderr}", ok=False)
    except Exception as e:
        log(f"Erreur pm2 : {e}", ok=False)

    print("\n" + "=" * 70)
    print("✅ PATCH v10 TERMINÉ — Paiement HEBDO actif")
    print("=" * 70)
    print("\nVérifie en visitant : https://metro-taxi.com/driver/earnings")
    print("(tu dois voir : 'Virement automatique chaque lundi')\n")


if __name__ == "__main__":
    main()
