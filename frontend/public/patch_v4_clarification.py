#!/usr/bin/env python3
"""
Patch v4 — Email de clarification urgente aux 33 chauffeurs.
Lever toute ambiguité : Les chauffeurs NE PAIENT PAS d'abonnement. Ils RECOIVENT 1,50€/km.

Idempotent.
"""
import os, sys
from datetime import datetime

EMAILS_FILE = "/var/www/metro-taxi-app/backend/services/emails.py"
ADMIN_FILE  = "/var/www/metro-taxi-app/backend/routes/admin.py"

def log(msg, ok=True):
    print(f"{'OK' if ok else '!!'} {msg}")

# ============================================
# PATCH emails.py — Ajout fonction
# ============================================
with open(EMAILS_FILE, "r", encoding="utf-8") as f:
    e_content = f.read()

if "send_clarification_email" in e_content:
    log("emails.py: deja patche v4")
else:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"{EMAILS_FILE}.bak.{ts}", "w", encoding="utf-8") as g:
        g.write(e_content)
    log(f"Backup emails.py.bak.{ts}")

    new_fn = '''

# ============================================
# BROADCAST V4 — CLARIFICATION URGENTE CHAUFFEURS
# ============================================
async def send_clarification_email(email: str, name: str, pioneer_number: int = None):
    """Email de clarification anti-confusion : les chauffeurs ne paient PAS, ils RECOIVENT."""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, clarification email NOT sent")
        return False

    pioneer_badge = f"PIONNIER #{pioneer_number}" if pioneer_number else "PIONNIER"

    html_content = f"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Helvetica,Arial,sans-serif;background:#0a0a0a;margin:0;padding:30px 20px;color:#fff;">
  <div style="max-width:620px;margin:0 auto;background:#1a1a1a;border-radius:12px;overflow:hidden;border-top:6px solid #FFD60A;">

    <div style="background:#FFD60A;padding:24px;text-align:center;">
      <p style="margin:0 0 4px 0;color:#000;font-size:11px;font-weight:bold;letter-spacing:2px;">{pioneer_badge} • CLARIFICATION IMPORTANTE</p>
      <h1 style="margin:0;color:#000;font-size:22px;">TU NE PAIES RIEN. TU REÇOIS.</h1>
    </div>

    <div style="padding:30px 26px;">
      <h2 style="color:#FFD60A;font-size:20px;margin:0 0 14px 0;">Salut {name} 👋</h2>

      <p style="color:#e4e4e7;line-height:1.7;font-size:15px;margin:0 0 18px 0;">
        Suite à plusieurs questions reçues ce matin, je clarifie une zone qui peut prêter à confusion 👇
      </p>

      <div style="background:#0a0a0a;border:2px solid #FFD60A;border-radius:10px;padding:20px;margin:24px 0;">
        <h3 style="color:#FFD60A;font-size:18px;margin:0 0 14px 0;">🚖 TOI, EN TANT QUE CHAUFFEUR PIONNIER :</h3>
        <ul style="color:#fff;line-height:1.9;font-size:15px;margin:0;padding-left:20px;">
          <li><strong>Tu REÇOIS</strong> de l'argent — pas l'inverse</li>
          <li><strong>1,50 € / km</strong> parcouru avec un abonné Métro-Taxi à bord</li>
          <li><strong>0 %</strong> de commission, à vie</li>
          <li>Versement <strong>le 10 de chaque mois</strong></li>
          <li><strong>Aucun engagement</strong>, aucun abonnement, aucun prélèvement</li>
          <li>Tu continues tes activités actuelles en parallèle si tu veux</li>
        </ul>
      </div>

      <div style="background:#1a1a1a;border:1px solid #444;border-radius:10px;padding:20px;margin:24px 0;">
        <h3 style="color:#cccccc;font-size:16px;margin:0 0 12px 0;">👥 L'ABONNEMENT (6,99€/jour, 19,99€/7j, 53,99€/30j) :</h3>
        <p style="color:#cccccc;line-height:1.7;font-size:14px;margin:0;">
          Il concerne <strong>UNIQUEMENT les usagers passagers</strong> qui veulent utiliser le service Métro-Taxi pour leurs trajets.
          C'est <strong>EUX</strong> qui paient l'abonnement à l'entreprise. Toi, tu es chauffeur, tu n'es pas concerné par ce paiement.
        </p>
      </div>

      <div style="background:#1a1a1a;border:1px solid #444;border-radius:10px;padding:20px;margin:24px 0;">
        <h3 style="color:#cccccc;font-size:16px;margin:0 0 12px 0;">🎁 L'OFFRE FONDATEUR (1ère course offerte aux 30 premiers abonnés) :</h3>
        <p style="color:#cccccc;line-height:1.7;font-size:14px;margin:0;">
          C'est un <strong>cadeau commercial</strong> pour les 30 premiers usagers passagers qui s'inscrivent.
          Toi en tant que chauffeur, tu ne perds rien : tu seras quand même payé <strong>1,50 € / km</strong> pour la course par l'entreprise Métro-Taxi.
        </p>
      </div>

      <hr style="border:none;border-top:1px solid #333;margin:28px 0 22px 0;">

      <h3 style="color:#FFD60A;font-size:16px;margin:0 0 12px 0;">🎯 Ce qui t'est demandé d'ici le 13 juin :</h3>
      <ol style="color:#cccccc;line-height:1.8;font-size:14px;margin:0 0 20px 0;padding-left:22px;">
        <li>Profil + RIB + immatriculation à jour dans l'app</li>
        <li>Accepter les courses qui passent dans ta zone à partir du 13 juin</li>
        <li>C'est tout.</li>
      </ol>

      <p style="color:#cccccc;line-height:1.7;font-size:14px;margin:0 0 14px 0;">
        Tu as un doute ? Une question ? <strong>Réponds à cet email</strong> ou écris-moi sur WhatsApp au <strong style="color:#FFD60A">06 68 55 00 19</strong> — je réponds personnellement.
      </p>

      <p style="color:#FFD60A;font-size:15px;margin:24px 0 0 0;">
        <strong>— Judée, Capitaine Métro-Taxi 🚖🇫🇷</strong>
      </p>
    </div>

    <div style="background:#09090b;padding:18px;text-align:center;border-top:1px solid #27272a;">
      <p style="color:#52525b;margin:0;font-size:11px;">© 2026 Métro-Taxi — J-12 avant le lancement Saint-Denis</p>
    </div>
  </div>
</body></html>
"""

    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": "✅ PIONNIER — Clarification : tu ne paies RIEN, tu reçois 1,50€/km",
            "html": html_content,
            "reply_to": "judeemane@hotmail.com",
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Clarification email sent to {email}, ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send clarification email to {email}: {str(e)}")
        return False

'''
    anchor = "# EMAIL PERSO ADMIN"
    idx = e_content.find(anchor)
    if idx == -1:
        e_content = e_content.rstrip() + new_fn + "\n"
    else:
        before = e_content[:idx].rstrip()
        lines = before.split("\n")
        while lines and lines[-1].strip().startswith("# ===="):
            lines.pop()
        before = "\n".join(lines).rstrip()
        e_content = before + new_fn + "\n# ============================================\n" + e_content[idx:]

    with open(EMAILS_FILE, "w", encoding="utf-8") as f:
        f.write(e_content)
    log("emails.py: send_clarification_email() ajoutee")

# ============================================
# PATCH admin.py — Ajout endpoint
# ============================================
with open(ADMIN_FILE, "r", encoding="utf-8") as f:
    a_content = f.read()

if "/admin/broadcast/clarification" in a_content:
    log("admin.py: deja patche v4")
    print("\n*** PATCH V4 deja applique ***")
    sys.exit(0)

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
with open(f"{ADMIN_FILE}.bak.{ts}", "w", encoding="utf-8") as g:
    g.write(a_content)
log(f"Backup admin.py.bak.{ts}")

if "send_clarification_email" not in a_content:
    a_content = a_content.replace(
        "send_engagement_booster_email",
        "send_engagement_booster_email, send_clarification_email",
        1
    )
    log("Import send_clarification_email ajoute")

new_endpoint = '''


# ==========================================================
# BROADCAST V4 — CLARIFICATION URGENTE CHAUFFEURS
# ==========================================================
class ClarificationPayload(BaseModel):
    confirmation_phrase: str  # Doit etre "GO CLARIFICATION"
    include_unverified: Optional[bool] = True


@router.post("/admin/broadcast/clarification")
async def broadcast_clarification(
    payload: ClarificationPayload,
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Acces reserve aux administrateurs")

    if payload.confirmation_phrase != "GO CLARIFICATION":
        raise HTTPException(
            status_code=400,
            detail="Phrase de confirmation invalide. Envoie exactement: 'GO CLARIFICATION'"
        )

    if payload.include_unverified:
        mongo_filter = {"is_validated": True}
    else:
        mongo_filter = {"is_validated": True, "email_verified": True}

    cursor = db.drivers.find(
        mongo_filter,
        {"_id": 0, "id": 1, "first_name": 1, "email": 1, "pioneer_number": 1}
    )
    drivers = await cursor.to_list(length=500)

    if not drivers:
        raise HTTPException(status_code=404, detail="Aucun chauffeur eligible")

    results = {"sent": [], "failed": []}
    for d in drivers:
        email = d.get("email")
        name = d.get("first_name", "Chauffeur")
        pioneer_number = d.get("pioneer_number")

        try:
            ok = await send_clarification_email(
                email=email,
                name=name,
                pioneer_number=pioneer_number,
            )
            if ok:
                results["sent"].append({"email": email, "pioneer_number": pioneer_number})
            else:
                results["failed"].append({"email": email, "reason": "send returned False"})
        except Exception as e:
            results["failed"].append({"email": email, "reason": str(e)})
        await asyncio.sleep(0.2)

    await db.broadcast_logs.insert_one({
        "broadcast_id": str(uuid.uuid4()),
        "type": "clarification_2026_06_01",
        "sent_at": datetime.now(timezone.utc),
        "sent_by": current_user.get("email", "unknown"),
        "total_targeted": len(drivers),
        "sent_count": len(results["sent"]),
        "failed_count": len(results["failed"]),
    })

    return {
        "status": "clarification_done",
        "total_targeted": len(drivers),
        "sent_count": len(results["sent"]),
        "failed_count": len(results["failed"]),
        "failures": results["failed"],
    }
'''

a_content = a_content.rstrip() + new_endpoint + "\n"

with open(ADMIN_FILE, "w", encoding="utf-8") as f:
    f.write(a_content)
log("admin.py: endpoint clarification ajoute")

print()
print("PATCH V4 APPLIQUE")
print("Redemarre: pm2 restart all --update-env")
