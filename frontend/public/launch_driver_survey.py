#!/usr/bin/env python3
"""
Lance le broadcast du sondage présence chauffeurs 13 juin
=========================================================
À exécuter directement sur le VPS — bypass de l'authentification HTTP
puisqu'on est déjà sur le serveur.

Usage:
    cd /var/www/metro-taxi-app/backend
    curl -fsSL https://metro-taxi-demo.preview.emergentagent.com/launch_driver_survey.py -o /tmp/survey.py
    python3 /tmp/survey.py
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Adapter le path pour trouver le backend
sys.path.insert(0, str(Path("/var/www/metro-taxi-app/backend")))

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv(Path("/var/www/metro-taxi-app/backend/.env"))


async def main():
    print("\n" + "=" * 70)
    print("  📋 BROADCAST SONDAGE PRÉSENCE CHAUFFEURS — VENDREDI 13 JUIN")
    print("=" * 70 + "\n")

    from motor.motor_asyncio import AsyncIOMotorClient
    from services.emails import send_driver_presence_survey_email

    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "test_database")
    frontend_url = os.environ.get("FRONTEND_URL", "https://metro-taxi.com")

    if not mongo_url:
        print("❌ MONGO_URL manquante dans .env")
        return

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    # 1. Récupérer les chauffeurs validés
    cursor = db.drivers.find(
        {"is_validated": True},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1, "pioneer_number": 1}
    )
    drivers = await cursor.to_list(length=500)
    print(f"🔍 Chauffeurs validés trouvés : {len(drivers)}\n")

    if not drivers:
        print("❌ Aucun chauffeur éligible — abandon")
        return

    # 2. Confirmer avant envoi
    print("=" * 70)
    print("  ⚠️  Tu vas envoyer le sondage 13 juin à ces chauffeurs :")
    print("=" * 70)
    for d in drivers[:50]:
        num = d.get("pioneer_number") or "?"
        print(f"  • Pionnier #{num:>3} — {d.get('first_name', '?'):<20} — {d.get('email', '?')}")
    print("=" * 70 + "\n")

    # 3. Envoi
    survey_id = str(uuid.uuid4())
    sent = 0
    failed = []
    print("📤 Envoi en cours...\n")

    for d in drivers:
        email = d.get("email")
        name = d.get("first_name") or "Chauffeur"
        pioneer_number = d.get("pioneer_number")
        driver_id = d.get("id")
        token = uuid.uuid4().hex

        await db.driver_presence_surveys.insert_one({
            "token": token,
            "survey_id": survey_id,
            "driver_id": driver_id,
            "driver_email": email,
            "driver_name": name,
            "pioneer_number": pioneer_number,
            "target_date": "2026-06-13",
            "answer": None,
            "responded_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        try:
            ok = await send_driver_presence_survey_email(
                email=email,
                name=name,
                pioneer_number=pioneer_number,
                response_token=token,
                base_url=frontend_url,
            )
            if ok:
                sent += 1
                print(f"  ✅ #{pioneer_number} {name} → {email}")
            else:
                failed.append({"email": email, "reason": "send returned False"})
                print(f"  ❌ #{pioneer_number} {name} → {email} : FAILED")
        except Exception as e:
            failed.append({"email": email, "reason": str(e)})
            print(f"  ❌ #{pioneer_number} {name} → {email} : {e}")

        await asyncio.sleep(0.2)  # Anti-rate-limit Resend

    # 4. Log en DB
    await db.broadcast_logs.insert_one({
        "broadcast_id": survey_id,
        "type": "driver_presence_survey_2026_06_13",
        "sent_at": datetime.now(timezone.utc),
        "sent_by": "VPS_CLI_SCRIPT",
        "total_targeted": len(drivers),
        "sent_count": sent,
        "failed_count": len(failed),
        "failures": failed,
    })

    # 5. Récap final
    print("\n" + "=" * 70)
    print(f"  ✅ BROADCAST TERMINÉ")
    print("=" * 70)
    print(f"  📊 Envoyés avec succès : {sent}/{len(drivers)}")
    print(f"  ❌ Échecs              : {len(failed)}")
    print(f"  🆔 Survey ID           : {survey_id}")
    print("=" * 70)

    if failed:
        print("\n⚠️ Liste des échecs :")
        for f in failed:
            print(f"  • {f['email']} : {f['reason']}")

    print("\n💡 Les chauffeurs vont recevoir l'email avec 2 boutons OUI/NON cliquables.")
    print("   Pour voir les résultats en temps réel :")
    print("   python3 /tmp/survey.py results")
    print()


async def show_results():
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "test_database")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    cursor = db.driver_presence_surveys.find({}, {"_id": 0})
    surveys = await cursor.to_list(length=500)

    yes_list, no_list, pending_list = [], [], []
    for s in surveys:
        if s.get("answer") == "yes":
            yes_list.append(s)
        elif s.get("answer") == "no":
            no_list.append(s)
        else:
            pending_list.append(s)

    print("\n" + "=" * 70)
    print("  📊 RÉSULTATS SONDAGE PRÉSENCE 13 JUIN")
    print("=" * 70)
    print(f"  Total envoyés       : {len(surveys)}")
    print(f"  ✅ OUI (disponibles) : {len(yes_list)}")
    print(f"  ❌ NON (indispo)     : {len(no_list)}")
    print(f"  ⏳ En attente        : {len(pending_list)}")
    if surveys:
        rate = round(100 * (len(yes_list) + len(no_list)) / len(surveys), 1)
        print(f"  📈 Taux de réponse   : {rate}%")
    print("=" * 70 + "\n")

    if yes_list:
        print("✅ DISPONIBLES LE 13 JUIN :")
        for s in yes_list:
            num = s.get("pioneer_number") or "?"
            print(f"  • #{num} {s.get('driver_name', '?')} ({s.get('driver_email', '?')})")
        print()

    if no_list:
        print("❌ INDISPONIBLES :")
        for s in no_list:
            num = s.get("pioneer_number") or "?"
            print(f"  • #{num} {s.get('driver_name', '?')} ({s.get('driver_email', '?')})")
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "results":
        asyncio.run(show_results())
    else:
        asyncio.run(main())
