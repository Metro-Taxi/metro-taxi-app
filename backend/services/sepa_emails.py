"""
SEPA batch email service.

Envoie chaque lundi le fichier SEPA XML à l'administrateur (donneur d'ordre) en pièce
jointe, avec un récap clair des virements à exécuter.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import os

import resend


RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


async def send_sepa_batch_to_admin(
    admin_email: str,
    xml_bytes: bytes,
    filename: str,
    week: str,
    transactions_count: int,
    total_amount_eur: str,
    driver_records: list[dict],
) -> bool:
    """Envoie le fichier SEPA XML à l'admin avec un récap des virements."""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, skipping SEPA admin email")
        return False

    # Construire le tableau récap HTML
    rows_html = ""
    for rec in driver_records:
        d = rec.get("driver", {})
        rows_html += (
            f'<tr>'
            f'<td style="padding:8px;border-bottom:1px solid #27272a;color:#e4e4e7;">'
            f'{d.get("first_name", "")} {d.get("last_name", "")}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #27272a;color:#a1a1aa;font-family:monospace;font-size:12px;">'
            f'{d.get("iban", "")}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #27272a;color:#FFD60A;text-align:right;font-weight:bold;">'
            f'{rec.get("amount", 0):.2f} €</td>'
            f'</tr>'
        )

    html_content = f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background-color:#09090b;font-family:-apple-system,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#09090b;padding:20px 0;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0" style="background-color:#18181B;border-radius:12px;overflow:hidden;">
        <tr><td style="background-color:#FFD60A;padding:30px 30px 20px 30px;">
          <h1 style="color:#000;margin:0;font-size:24px;">Batch SEPA — Semaine {week}</h1>
          <p style="color:#000;margin:8px 0 0 0;font-size:14px;">À uploader dans Société Générale Pro avant J+1.</p>
        </td></tr>
        <tr><td style="padding:30px;">
          <p style="color:#e4e4e7;margin:0 0 20px 0;font-size:16px;">Salut Capitaine,</p>
          <p style="color:#a1a1aa;margin:0 0 20px 0;font-size:14px;line-height:1.6;">
            Voici le fichier SEPA XML généré automatiquement pour les virements chauffeurs de cette semaine.
            <b style="color:#FFD60A;">{transactions_count} chauffeur{"s" if transactions_count > 1 else ""}</b>,
            total <b style="color:#FFD60A;">{total_amount_eur} €</b>.
          </p>

          <div style="background-color:#FFD60A22;border-left:4px solid #FFD60A;padding:12px 16px;margin:0 0 24px 0;border-radius:4px;">
            <p style="color:#FFD60A;margin:0;font-weight:bold;font-size:14px;">À faire dans les 30 prochaines secondes</p>
            <ol style="color:#e4e4e7;margin:8px 0 0 0;padding-left:20px;font-size:13px;line-height:1.7;">
              <li>Télécharger le fichier <code style="background-color:#27272a;padding:2px 6px;border-radius:3px;">{filename}</code> en pièce jointe.</li>
              <li>Te connecter à ton espace Société Générale Pro.</li>
              <li>Aller dans Virements &gt; Virement multiple &gt; Importer un fichier SEPA.</li>
              <li>Uploader le XML et valider le batch.</li>
            </ol>
          </div>

          <h2 style="color:#e4e4e7;margin:24px 0 12px 0;font-size:18px;">Récap des virements</h2>
          <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#27272a;border-radius:8px;overflow:hidden;">
            <thead>
              <tr style="background-color:#3f3f46;">
                <th style="padding:10px 8px;color:#FFD60A;text-align:left;font-size:12px;text-transform:uppercase;">Chauffeur</th>
                <th style="padding:10px 8px;color:#FFD60A;text-align:left;font-size:12px;text-transform:uppercase;">IBAN</th>
                <th style="padding:10px 8px;color:#FFD60A;text-align:right;font-size:12px;text-transform:uppercase;">Montant</th>
              </tr>
            </thead>
            <tbody>{rows_html}</tbody>
          </table>

          <p style="color:#71717a;margin:24px 0 0 0;font-size:12px;line-height:1.6;">
            Fichier conforme à la norme ISO 20022 (pain.001.001.03). Les chauffeurs ont déjà été notifiés
            qu'un virement de leur montant est en cours de traitement (réception sous 1 à 3 jours ouvrés).
          </p>
        </td></tr>
        <tr><td style="background-color:#09090b;padding:20px 30px;text-align:center;">
          <p style="color:#52525b;margin:0;font-size:12px;">© 2026 Métro-Taxi — Système automatique de virement SEPA hebdomadaire.</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""

    # Encoder le fichier XML en base64 pour Resend
    xml_b64 = base64.b64encode(xml_bytes).decode("ascii")

    params = {
        "from": SENDER_EMAIL,
        "to": [admin_email],
        "subject": f"[Metro-Taxi] Batch SEPA semaine {week} — {transactions_count} virement{'s' if transactions_count > 1 else ''}, {total_amount_eur} €",
        "html": html_content,
        "attachments": [
            {
                "filename": filename,
                "content": xml_b64,
            }
        ],
    }

    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"SEPA batch email sent to {admin_email}, ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send SEPA batch email: {e}")
        return False
