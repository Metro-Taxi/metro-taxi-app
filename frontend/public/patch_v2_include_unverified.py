#!/usr/bin/env python3
"""
Patch v2 — Option include_unverified pour cibler les chauffeurs validés mais email non vérifié.

LOGIQUE :
- include_unverified=False (défaut)  → is_validated=True AND email_verified=True  (les 14 déjà notifiés)
- include_unverified=True            → is_validated=True AND email_verified=False (les 19 restants)
→ ZÉRO risque de doublon car les 2 ensembles sont DISJOINTS.

Idempotent.
"""
import os, sys
from datetime import datetime

ADMIN_FILE = "/var/www/metro-taxi-app/backend/routes/admin.py"

def log(msg, ok=True):
    print(f"{'OK' if ok else '!!'} {msg}")

with open(ADMIN_FILE, "r", encoding="utf-8") as f:
    content = f.read()

if "include_unverified" in content:
    log("Deja patche v2, je passe")
    sys.exit(0)

# Backup
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = f"{ADMIN_FILE}.bak.{ts}"
with open(bak, "w", encoding="utf-8") as g:
    g.write(content)
log(f"Backup: {bak}")

# 1. Ajouter le champ include_unverified au BroadcastConfirmPayload
old_cls = """class BroadcastConfirmPayload(BaseModel):
    confirmation_phrase: str  # Doit être exactement "GO 13 JUIN"
    dry_run: Optional[bool] = False  # Si True, retourne juste la liste sans envoyer"""

new_cls = """class BroadcastConfirmPayload(BaseModel):
    confirmation_phrase: str  # Doit être exactement "GO 13 JUIN"
    dry_run: Optional[bool] = False  # Si True, retourne juste la liste sans envoyer
    include_unverified: Optional[bool] = False  # Si True, cible UNIQUEMENT les validés avec email non vérifié (rattrapage)"""

if old_cls not in content:
    log("Pattern BroadcastConfirmPayload introuvable", ok=False)
    sys.exit(1)
content = content.replace(old_cls, new_cls)
log("BroadcastConfirmPayload patche")

# 2. Modifier le filtre Mongo (logique disjointe)
old_filter = """    cursor = db.drivers.find(
        {"is_validated": True, "email_verified": True},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1, "pioneer_number": 1}
    )
    drivers = await cursor.to_list(length=500)

    if not drivers:
        raise HTTPException(status_code=404, detail="Aucun chauffeur éligible")"""

new_filter = """    # Logique disjointe pour zero doublon
    if payload.include_unverified:
        # Mode RATTRAPAGE : seulement les validés AVEC email NON vérifié
        mongo_filter = {"is_validated": True, "email_verified": {"$ne": True}}
    else:
        # Mode STANDARD : les validés AVEC email vérifié (deja fait)
        mongo_filter = {"is_validated": True, "email_verified": True}

    cursor = db.drivers.find(
        mongo_filter,
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1, "pioneer_number": 1}
    )
    drivers = await cursor.to_list(length=500)

    if not drivers:
        raise HTTPException(status_code=404, detail="Aucun chauffeur eligible avec ce critere")"""

if old_filter not in content:
    log("Pattern filtre Mongo introuvable", ok=False)
    sys.exit(1)
content = content.replace(old_filter, new_filter)
log("Filtre Mongo patche (logique disjointe)")

with open(ADMIN_FILE, "w", encoding="utf-8") as f:
    f.write(content)

log("PATCH V2 APPLIQUE")
print()
print("Redemarre le backend : pm2 restart all --update-env")
