#!/usr/bin/env python3
"""
Patch v3 — Email booster engagement aux 33 chauffeurs pour les inviter à
liker/commenter les posts Instagram + TikTok du Capitaine, et leur fournir
les liens des Vidéos 2 & 3 à diffuser.

Idempotent.
"""
import os, sys
from datetime import datetime

EMAILS_FILE = "/var/www/metro-taxi-app/backend/services/emails.py"
ADMIN_FILE  = "/var/www/metro-taxi-app/backend/routes/admin.py"

def log(msg, ok=True):
    print(f"{'OK' if ok else '!!'} {msg}")

# ---------- Patch emails.py ----------
with open(EMAILS_FILE, "r", encoding="utf-8") as f:
    e_content = f.read()

if "send_engagement_booster_email" in e_content:
    log("emails.py: deja patche v3")
else:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"{EMAILS_FILE}.bak.{ts}", "w", encoding="utf-8") as g:
        g.write(e_content)
    log(f"Backup emails.py.bak.{ts}")

    new_fn = '''

# ============================================
# BROADCAST V3 — ENGAGEMENT BOOSTER (Instagram + TikTok)
# ============================================
async def send_engagement_booster_email(
    email: str,
    name: str,
    pioneer_number: int = None,
    instagram_url: str = "",
    tiktok_url: str = "",
    video2_url: str = "https://metro-taxi-demo.preview.emergentagent.com/marketing/metrotaxi_scenario2_metro_vs_FINAL.mp4",
    video3_url: str = "https://metro-taxi-demo.preview.emergentagent.com/marketing/metrotaxi_scenario3_transbordement_FINAL.mp4",
):
    """Email aux 33 chauffeurs pour booster l'engagement social media (likes/commentaires)."""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, engagement booster email NOT sent")
        return False

    pioneer_badge = f"PIONNIER #{pioneer_number}" if pioneer_number else "PIONNIER"

    html_content = f"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Helvetica,Arial,sans-serif;background:#0a0a0a;margin:0;padding:30px 20px;color:#fff;">
  <div style="max-width:620px;margin:0 auto;background:#1a1a1a;border-radius:12px;overflow:hidden;border-top:6px solid #FFD60A;">

    <div style="background:#FFD60A;padding:24px;text-align:center;">
      <p style="margin:0 0 4px 0;color:#000;font-size:11px;font-weight:bold;letter-spacing:2px;">{pioneer_badge}</p>
      <h1 style="margin:0;color:#000;font-size:22px;">MISSION TERRAIN — J-12</h1>
    </div>

    <div style="padding:30px 26px;">
      <h2 style="color:#FFD60A;font-size:20px;margin:0 0 14px 0;">Salut {name} 👋</h2>

      <p style="color:#e4e4e7;line-height:1.7;font-size:15px;margin:0 0 18px 0;">
        Hier soir, j'ai publié notre <strong style="color:#FFD60A">première vidéo officielle</strong> sur Instagram et TikTok.
        Premiers résultats : <strong>523 vues sur TikTok</strong> en 12h, plus de 130 sur Instagram.
      </p>

      <p style="color:#e4e4e7;line-height:1.7;font-size:15px;margin:0 0 18px 0;">
        Pour faire <strong>EXPLOSER les chiffres</strong> et que la zone Saint-Denis nous voit avant le 13 juin,
        j'ai besoin de toi pendant <strong>30 secondes</strong> 👇
      </p>

      <h3 style="color:#FFD60A;font-size:16px;margin:28px 0 12px 0;border-bottom:1px solid #27272a;padding-bottom:8px;">📲 MISSION 1 — Like + Commentaire (30 sec)</h3>

      <table width="100%" cellpadding="0" cellspacing="0" style="margin:14px 0;"><tr><td>
        <a href="{instagram_url}" style="display:block;background:#0a0a0a;border:2px solid #E1306C;color:#fff;text-decoration:none;padding:14px 18px;border-radius:10px;margin-bottom:10px;">
          <strong style="color:#E1306C">📷 INSTAGRAM</strong> — Voir le Reel et liker →
        </a>
        <a href="{tiktok_url}" style="display:block;background:#0a0a0a;border:2px solid #fff;color:#fff;text-decoration:none;padding:14px 18px;border-radius:10px;">
          <strong style="color:#fff">🎵 TIKTOK</strong> — Voir la vidéo et liker →
        </a>
      </td></tr></table>

      <p style="color:#a1a1aa;font-size:13px;line-height:1.6;margin:14px 0 0 0;font-style:italic;">
        Tape sur le coeur. Laisse un emoji (🚖❤️🇫🇷) en commentaire. C'est gratuit, c'est rapide, et ça booste
        l'algorithme local Saint-Denis de +50%.
      </p>

      <h3 style="color:#FFD60A;font-size:16px;margin:32px 0 12px 0;border-bottom:1px solid #27272a;padding-bottom:8px;">🎬 MISSION 2 — Diffuse autour de toi (BONUS)</h3>

      <p style="color:#e4e4e7;line-height:1.7;font-size:14px;margin:0 0 14px 0;">
        Voici les <strong>2 vidéos officielles</strong>. Télécharge-les et partage-les sur ton WhatsApp Status,
        ton groupe famille, ton groupe quartier, tes collègues VTC — partout où Saint-Denis vit :
      </p>

      <table width="100%" cellpadding="0" cellspacing="0" style="margin:14px 0;"><tr><td>
        <a href="{video2_url}" style="display:block;background:#FFD60A;color:#000;text-decoration:none;padding:12px 16px;border-radius:8px;font-weight:bold;text-align:center;margin-bottom:8px;font-size:14px;">
          📥 Vidéo 1 — "Métro vs Métro-Taxi" (10s)
        </a>
        <a href="{video3_url}" style="display:block;background:#FFD60A;color:#000;text-decoration:none;padding:12px 16px;border-radius:8px;font-weight:bold;text-align:center;font-size:14px;">
          📥 Vidéo 2 — "Le Transbordement" (10s)
        </a>
      </td></tr></table>

      <hr style="border:none;border-top:1px solid #333;margin:28px 0 22px 0;">

      <p style="color:#cccccc;line-height:1.7;font-size:14px;margin:0 0 14px 0;">
        Vous êtes 33. Si chacun de vous like + commente + partage UNE fois,
        on touche au minimum <strong style="color:#FFD60A">3 000 personnes ce soir</strong>.
        C'est la <strong>vitesse de l'explosion</strong>.
      </p>

      <p style="color:#fff;line-height:1.7;font-size:15px;margin:0 0 14px 0;">
        Je compte sur toi <strong>{name}</strong>. On y va ensemble.
      </p>

      <p style="color:#FFD60A;font-size:15px;margin:24px 0 0 0;">
        <strong>— Judee, Capitaine Métro-Taxi 🚖🇫🇷</strong>
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
            "subject": "🚨 PIONNIER — Mission 30 sec pour faire exploser nos chiffres",
            "html": html_content,
            "reply_to": "judeemane@hotmail.com",
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Engagement booster email sent to {email}, ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send engagement booster email to {email}: {str(e)}")
        return False

'''
    # Insert before "# EMAIL PERSO ADMIN"
    anchor = "# EMAIL PERSO ADMIN"
    idx = e_content.find(anchor)
    if idx == -1:
        e_content = e_content.rstrip() + new_fn + "\n"
    else:
        # Remonter à la separation ====
        before = e_content[:idx].rstrip()
        lines = before.split("\n")
        while lines and lines[-1].strip().startswith("# ===="):
            lines.pop()
        before = "\n".join(lines).rstrip()
        e_content = before + new_fn + "\n# ============================================\n" + e_content[idx:]

    with open(EMAILS_FILE, "w", encoding="utf-8") as f:
        f.write(e_content)
    log("emails.py: send_engagement_booster_email() ajoutee")

# ---------- Patch admin.py ----------
with open(ADMIN_FILE, "r", encoding="utf-8") as f:
    a_content = f.read()

if "/admin/broadcast/engagement-booster" in a_content:
    log("admin.py: deja patche v3")
    print("\n*** PATCH V3 deja applique - aucun changement ***")
    sys.exit(0)

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
with open(f"{ADMIN_FILE}.bak.{ts}", "w", encoding="utf-8") as g:
    g.write(a_content)
log(f"Backup admin.py.bak.{ts}")

# Add import
if "send_engagement_booster_email" not in a_content:
    a_content = a_content.replace(
        "send_admin_personal_email, send_launch_announcement_email",
        "send_admin_personal_email, send_launch_announcement_email, send_engagement_booster_email",
        1
    )
    log("Import send_engagement_booster_email ajoute")

# Append endpoint
new_endpoint = '''


# ==========================================================
# BROADCAST V3 — ENGAGEMENT BOOSTER (Instagram + TikTok)
# ==========================================================
class EngagementBoosterPayload(BaseModel):
    confirmation_phrase: str
    instagram_url: str
    tiktok_url: str
    include_unverified: Optional[bool] = True  # Default True : on cible TOUS les 33 chauffeurs
    dry_run: Optional[bool] = False


@router.post("/admin/broadcast/engagement-booster")
async def broadcast_engagement_booster(
    payload: EngagementBoosterPayload,
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Acces reserve aux administrateurs")

    if payload.confirmation_phrase != "GO BOOSTER":
        raise HTTPException(
            status_code=400,
            detail="Phrase de confirmation invalide. Envoie exactement: 'GO BOOSTER'"
        )

    if not payload.instagram_url or not payload.tiktok_url:
        raise HTTPException(status_code=400, detail="instagram_url et tiktok_url sont obligatoires")

    # Cible TOUS les chauffeurs validés (par defaut email_verified ignore = on touche TOUS les 33)
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

    if payload.dry_run:
        return {
            "status": "dry_run",
            "would_send_to": len(drivers),
            "instagram_url": payload.instagram_url,
            "tiktok_url": payload.tiktok_url,
        }

    results = {"sent": [], "failed": []}
    for d in drivers:
        email = d.get("email")
        name = d.get("first_name", "Chauffeur")
        pioneer_number = d.get("pioneer_number")

        try:
            ok = await send_engagement_booster_email(
                email=email,
                name=name,
                pioneer_number=pioneer_number,
                instagram_url=payload.instagram_url,
                tiktok_url=payload.tiktok_url,
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
        "type": "engagement_booster_2026_06_01",
        "sent_at": datetime.now(timezone.utc),
        "sent_by": current_user.get("email", "unknown"),
        "instagram_url": payload.instagram_url,
        "tiktok_url": payload.tiktok_url,
        "total_targeted": len(drivers),
        "sent_count": len(results["sent"]),
        "failed_count": len(results["failed"]),
    })

    return {
        "status": "engagement_booster_done",
        "total_targeted": len(drivers),
        "sent_count": len(results["sent"]),
        "failed_count": len(results["failed"]),
        "failures": results["failed"],
    }
'''

a_content = a_content.rstrip() + new_endpoint + "\n"

with open(ADMIN_FILE, "w", encoding="utf-8") as f:
    f.write(a_content)
log("admin.py: endpoint engagement-booster ajoute")

print()
print("PATCH V3 APPLIQUE")
print("Redemarre: pm2 restart all --update-env")
