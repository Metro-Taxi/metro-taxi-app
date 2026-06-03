#!/usr/bin/env python3
"""
PATCH v9 — Fix Open Graph Facebook (anti "Metro Taxi Montreal")
================================================================
Corrige frontend/public/index.html :
  - lang="en" → lang="fr"
  - Ajoute og:site_name = Métro-Taxi
  - Ajoute og:url = https://metro-taxi.com (absolu)
  - Ajoute og:locale = fr_FR
  - og:image en URL absolue (au lieu de %PUBLIC_URL%/icons/...)
  - og:description optimisée pour la campagne Saint-Denis 13 juin
  - Ajoute Twitter Card

Usage:
    cd /var/www/metro-taxi-app
    curl -fsSL https://metro-taxi-demo.preview.emergentagent.com/patch_v9_opengraph.py -o /tmp/patch_v9.py
    python3 /tmp/patch_v9.py
    cd frontend && yarn build && cd ..
    pm2 restart all --update-env

⚠️ APRÈS LE PATCH : tu dois aussi DEBUG Facebook Cache (étape manuelle) :
    https://developers.facebook.com/tools/debug/
    Colle https://metro-taxi.com → clique "Récupérer les nouvelles informations"
"""
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path("/var/www/metro-taxi-app")
INDEX_HTML = ROOT / "frontend" / "public" / "index.html"


def log(msg, status="ok"):
    icons = {"ok": "✅", "skip": "⏭️ ", "err": "❌", "warn": "⚠️ "}
    print(f"{icons.get(status, '•')} {msg}")


def backup(path: Path):
    if path.exists():
        bk = path.with_suffix(path.suffix + f".bak-{datetime.now():%Y%m%d-%H%M%S}")
        shutil.copy2(path, bk)


OLD_LANG = '<html lang="en">'
NEW_LANG = '<html lang="fr">'

OLD_OG = '''        <meta property="og:type" content="website" />
        <meta property="og:title" content="Métro-Taxi - Covoiturage par abonnement" />
        <meta property="og:description" content="Rejoignez des véhicules allant dans votre direction. Trajets illimités avec un simple abonnement." />
        <meta property="og:image" content="%PUBLIC_URL%/icons/icon-512x512.png" />'''

NEW_OG = '''        <meta property="og:type" content="website" />
        <meta property="og:site_name" content="Métro-Taxi" />
        <meta property="og:locale" content="fr_FR" />
        <meta property="og:url" content="https://metro-taxi.com" />
        <meta property="og:title" content="Métro-Taxi — Saint-Denis 93 : abonnement transport illimité" />
        <meta property="og:description" content="33 chauffeurs locaux, trajets illimités par abonnement à Saint-Denis et Île-de-France. 1ère course offerte aux 30 premiers abonnés. Lancement samedi 13 juin 2026." />
        <meta property="og:image" content="https://metro-taxi.com/icons/icon-512x512.png" />
        <meta property="og:image:width" content="512" />
        <meta property="og:image:height" content="512" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Métro-Taxi — Saint-Denis 93 : abonnement transport illimité" />
        <meta name="twitter:description" content="33 chauffeurs locaux, trajets illimités par abonnement. Lancement samedi 13 juin 2026." />
        <meta name="twitter:image" content="https://metro-taxi.com/icons/icon-512x512.png" />'''


def main():
    print("\n" + "=" * 70)
    print("  PATCH v9 — Fix Open Graph Facebook")
    print("=" * 70 + "\n")

    if not INDEX_HTML.exists():
        log(f"{INDEX_HTML} introuvable", "err")
        return

    content = INDEX_HTML.read_text()
    changed = False

    if 'og:site_name' in content and 'lang="fr"' in content:
        log("Patch déjà appliqué (og:site_name + lang=fr présents)", "skip")
        return

    if OLD_LANG in content:
        content = content.replace(OLD_LANG, NEW_LANG, 1)
        log("lang='en' → lang='fr'", "ok")
        changed = True
    elif NEW_LANG in content:
        log("lang='fr' déjà présent", "skip")
    else:
        log("ancre lang introuvable", "warn")

    if OLD_OG in content:
        content = content.replace(OLD_OG, NEW_OG, 1)
        log("Bloc Open Graph complété (site_name, url, locale, twitter card)", "ok")
        changed = True
    else:
        log("Bloc Open Graph d'origine introuvable", "warn")

    if changed:
        backup(INDEX_HTML)
        INDEX_HTML.write_text(content)
        log(f"index.html patché", "ok")

    print("\n" + "=" * 70)
    print("  ✅ PATCH v9 APPLIQUÉ — Prochaines étapes :")
    print("=" * 70)
    print("    1. cd /var/www/metro-taxi-app/frontend && yarn build && cd ..")
    print("    2. pm2 restart all --update-env")
    print("    3. ⚠️ INVALIDER LE CACHE FACEBOOK (MANUEL) :")
    print("       Va sur https://developers.facebook.com/tools/debug/")
    print("       Colle: https://metro-taxi.com")
    print("       Clique: 'Récupérer les nouvelles informations'")
    print("       → Tu verras la nouvelle prévisualisation Métro-Taxi")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
