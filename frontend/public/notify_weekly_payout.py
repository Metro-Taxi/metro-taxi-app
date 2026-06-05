#!/usr/bin/env python3
"""
NOTIFICATION CHAUFFEURS — Annonce du passage au paiement HEBDOMADAIRE
À exécuter UNE SEULE FOIS après le patch_v10.

USAGE sur le VPS :
  cd /var/www/metro-taxi-app/backend && python3 notify_weekly_payout.py
"""

import asyncio
import os
import sys
from datetime import datetime

# Importe l'environnement du backend
sys.path.insert(0, "/var/www/metro-taxi-app/backend")

from dotenv import load_dotenv
load_dotenv("/var/www/metro-taxi-app/backend/.env")

from motor.motor_asyncio import AsyncIOMotorClient
import resend

resend.api_key = os.environ.get("RESEND_API_KEY")
FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "Métro-Taxi <contact@metro-taxi.com>")


def build_email(driver_name: str) -> str:
    name = driver_name or "Chauffeur"
    return f"""
    <!doctype html>
    <html><body style="margin:0;padding:0;background:#0a0a0a;font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
      <div style="max-width:600px;margin:0 auto;padding:40px 20px;color:#fff;">
        <div style="background:linear-gradient(135deg,#FFD60A,#FFA500);padding:30px;border-radius:16px 16px 0 0;text-align:center;">
          <h1 style="margin:0;color:#000;font-size:28px;">💰 Bonne nouvelle, {name} !</h1>
        </div>
        <div style="background:#18181b;padding:30px;border-radius:0 0 16px 16px;">
          <p style="font-size:16px;line-height:1.6;color:#fff;">
            Suite à de nombreux retours terrain de nos chauffeurs pionniers, on a écouté.
          </p>
          <div style="background:#27272a;border-left:4px solid #FFD60A;padding:20px;margin:24px 0;border-radius:8px;">
            <p style="margin:0;font-size:18px;font-weight:bold;color:#FFD60A;">
              🚀 PAIEMENT HEBDOMADAIRE désormais en place
            </p>
            <p style="margin:12px 0 0 0;color:#d4d4d8;">
              Tu seras payé(e) <strong style="color:#fff;">chaque LUNDI par virement SEPA</strong>
              sur l'IBAN renseigné dans ton tableau de bord. Fini d'attendre le 10 du mois.
            </p>
          </div>
          <p style="font-size:15px;line-height:1.6;color:#d4d4d8;">
            ✅ Cycle de paie : du lundi au dimanche<br>
            ✅ Virement le lundi suivant (J+1 ouvré)<br>
            ✅ Montant minimum : 10 €<br>
            ✅ Aucune commission pour tes 6 premiers mois (statut Pionnier)
          </p>
          <div style="text-align:center;margin:32px 0;">
            <a href="https://metro-taxi.com/driver/earnings"
               style="background:#FFD60A;color:#000;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block;">
              Voir mes revenus →
            </a>
          </div>
          <p style="font-size:14px;color:#a1a1aa;line-height:1.6;border-top:1px solid #3f3f46;padding-top:20px;">
            <strong style="color:#fff;">Important :</strong> assure-toi que ton <strong>IBAN/BIC</strong> est bien renseigné
            dans ton espace chauffeur. Si ce n'est pas le cas, fais-le maintenant pour ne pas rater le 1er virement.
          </p>
          <p style="font-size:14px;color:#a1a1aa;margin-top:24px;">
            Hâte de rouler avec toi le <strong style="color:#FFD60A;">samedi 13 juin 2026</strong>,<br>
            — Judée &amp; toute l'équipe Métro-Taxi 🚗
          </p>
        </div>
      </div>
    </body></html>
    """


async def main():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    drivers = await db.users.find(
        {"role": "driver"},
        {"_id": 0, "email": 1, "first_name": 1, "pioneer_number": 1},
    ).to_list(length=500)

    print(f"📧 {len(drivers)} chauffeurs à notifier...\n")

    sent = 0
    failed = 0
    for d in drivers:
        email = d.get("email")
        name = d.get("first_name") or ""
        if not email:
            continue
        try:
            resend.Emails.send({
                "from": FROM_EMAIL,
                "to": [email],
                "subject": "💰 Métro-Taxi : tu seras payé(e) chaque LUNDI maintenant !",
                "html": build_email(name),
            })
            sent += 1
            print(f"  ✅ #{d.get('pioneer_number','?')} {name} <{email}>")
        except Exception as e:
            failed += 1
            print(f"  ❌ {email} : {e}")

    print(f"\n{'='*60}")
    print(f"  ✅ Envoyés : {sent}")
    print(f"  ❌ Échecs  : {failed}")
    print(f"{'='*60}\n")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
