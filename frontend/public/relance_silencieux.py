#!/usr/bin/env python3
"""
Relance ciblée (Broadcast v6) — uniquement les chauffeurs sans réponse au sondage
================================================================================
- Récupère les chauffeurs avec un token de sondage et answer=None
- Renvoie un email "Reminder J-10" avec les mêmes boutons OUI/NON
  (mêmes tokens donc on conserve l'historique des réponses)

Usage:
    curl -fsSL https://metro-taxi-demo.preview.emergentagent.com/relance_silencieux.py -o /tmp/relance.py
    python3 /tmp/relance.py
"""
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path("/var/www/metro-taxi-app/backend")))

from dotenv import load_dotenv
load_dotenv(Path("/var/www/metro-taxi-app/backend/.env"))


async def send_reminder(email, name, pioneer_number, response_token, base_url):
    """Email reminder avec ton plus pressant que le 1er envoi."""
    import resend
    import asyncio as aio

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        return False
    resend.api_key = api_key

    sender = os.environ.get("SENDER_EMAIL", "Métro-Taxi <hello@metro-taxi.com>")
    yes_url = f"{base_url}/api/driver-presence-survey/respond?token={response_token}&answer=yes"
    no_url = f"{base_url}/api/driver-presence-survey/respond?token={response_token}&answer=no"
    badge = f"PIONNIER #{pioneer_number}" if pioneer_number else "CHAUFFEUR PIONNIER"

    html = f"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Helvetica,Arial,sans-serif;background:#0a0a0a;margin:0;padding:30px 20px;color:#fff;">
  <div style="max-width:600px;margin:0 auto;background:#1a1a1a;border-radius:12px;overflow:hidden;border-top:6px solid #ef4444;">
    <div style="background:#ef4444;padding:24px;text-align:center;">
      <p style="margin:0 0 6px 0;color:#fff;font-size:12px;font-weight:bold;letter-spacing:2px;">{badge}</p>
      <h1 style="margin:0;color:#fff;font-size:22px;">⏰ RAPPEL J-10 — TU N'AS PAS ENCORE RÉPONDU</h1>
    </div>
    <div style="padding:32px 28px;">
      <h2 style="color:#FFD60A;font-size:20px;margin:0 0 16px 0;">Salut {name} 👋</h2>
      <p style="color:#e4e4e7;line-height:1.7;font-size:15px;margin:0 0 18px 0;">
        Je t'ai envoyé hier un mail pour savoir si tu seras dispo le
        <strong style="color:#FFD60A">SAMEDI 13 JUIN 2026</strong> (ouverture officielle Saint-Denis).
      </p>
      <p style="color:#e4e4e7;line-height:1.7;font-size:15px;margin:0 0 18px 0;">
        Je n'ai pas encore reçu ta réponse 🤔
      </p>
      <p style="color:#fff;line-height:1.7;font-size:15px;margin:0 0 24px 0;background:#0a0a0a;border-left:4px solid #FFD60A;padding:14px 18px;border-radius:4px;">
        J'ai <strong style="color:#FFD60A">besoin de toi en 1 clic</strong> pour calibrer
        la jauge des 30 courses offertes le Jour J. Sans ta réponse, je dois te considérer
        comme non-disponible — ce serait dommage si tu comptais bien venir !
      </p>
      <table width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;">
        <tr>
          <td align="center" width="50%" style="padding:0 8px;">
            <a href="{yes_url}" style="display:block;background:#22c55e;color:#fff;text-decoration:none;padding:18px 12px;border-radius:10px;font-weight:bold;font-size:16px;">✅ OUI je suis dispo</a>
          </td>
          <td align="center" width="50%" style="padding:0 8px;">
            <a href="{no_url}" style="display:block;background:#71717a;color:#fff;text-decoration:none;padding:18px 12px;border-radius:10px;font-weight:bold;font-size:16px;">❌ NON indisponible</a>
          </td>
        </tr>
      </table>
      <p style="color:#a1a1aa;font-size:13px;line-height:1.6;margin:24px 0 0 0;text-align:center;font-style:italic;">
        1 clic, ça prend littéralement 1 seconde 🙏
      </p>
      <hr style="border:none;border-top:1px solid #333;margin:28px 0 20px 0;">
      <p style="color:#FFD60A;font-size:14px;margin:0;">
        À très vite Champion 🚖<br>
        <strong>— Judée, fondateur Métro-Taxi</strong>
      </p>
    </div>
    <div style="background:#09090b;padding:16px 24px;text-align:center;border-top:1px solid #27272a;">
      <p style="color:#52525b;margin:0;font-size:11px;">© 2026 Métro-Taxi — Saint-Denis 13 juin 2026</p>
    </div>
  </div>
</body></html>
"""
    try:
        params = {
            "from": sender,
            "to": [email],
            "subject": f"⏰ {name}, il manque ta réponse pour le 13 juin (1 clic)",
            "html": html,
            "reply_to": "judeemane@hotmail.com",
        }
        result = await aio.to_thread(resend.Emails.send, params)
        return bool(result.get("id"))
    except Exception as e:
        print(f"❌ Échec {email}: {e}")
        return False


async def main():
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "test_database")
    frontend_url = os.environ.get("FRONTEND_URL", "https://metro-taxi.com")

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    # Récupère tous les sondages SANS réponse
    cursor = db.driver_presence_surveys.find({"answer": None}, {"_id": 0})
    pending = await cursor.to_list(length=500)

    print("\n" + "=" * 70)
    print("  ⏰ RELANCE BROADCAST v6 — Chauffeurs silencieux du sondage 13 juin")
    print("=" * 70 + "\n")
    print(f"🔍 Chauffeurs SANS réponse : {len(pending)}\n")

    if not pending:
        print("✅ Tout le monde a répondu, rien à relancer.")
        return

    for s in pending[:50]:
        num = s.get("pioneer_number") or "?"
        print(f"  • #{num:>3} — {s.get('driver_name', '?'):<20} — {s.get('driver_email', '?')}")
    print()

    print("📤 Envoi des relances...\n")
    sent = 0
    failed = []
    for s in pending:
        email = s.get("driver_email")
        name = s.get("driver_name") or "Chauffeur"
        pioneer = s.get("pioneer_number")
        token = s.get("token")  # IMPORTANT : on réutilise le même token
        if not (email and token):
            continue
        ok = await send_reminder(email, name, pioneer, token, frontend_url)
        if ok:
            sent += 1
            print(f"  ✅ #{pioneer} {name}")
        else:
            failed.append({"email": email})
            print(f"  ❌ #{pioneer} {name} : échec")
        await asyncio.sleep(0.25)

    await db.broadcast_logs.insert_one({
        "type": "driver_presence_survey_2026_06_13_REMINDER",
        "sent_at": datetime.now(timezone.utc),
        "sent_by": "VPS_CLI_SCRIPT_v6",
        "total_targeted": len(pending),
        "sent_count": sent,
        "failed_count": len(failed),
        "failures": failed,
    })

    print("\n" + "=" * 70)
    print(f"  ✅ RELANCE TERMINÉE")
    print("=" * 70)
    print(f"  📊 Envoyés : {sent}/{len(pending)}")
    print(f"  ❌ Échecs  : {len(failed)}")
    print("=" * 70)
    print("\n💡 Pour suivre les nouvelles réponses :")
    print("   python3 /tmp/survey.py results\n")


if __name__ == "__main__":
    asyncio.run(main())
