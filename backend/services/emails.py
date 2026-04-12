"""
Services d'envoi d'emails - Métro-Taxi
Utilise Resend SDK v2 (resend.Emails.send)
"""
import os
import asyncio
import logging
import resend
from datetime import datetime

RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


async def send_verification_email(email: str, name: str, verification_url: str, lang: str = "fr"):
    """Send verification email using Resend"""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, skipping email")
        return False

    templates = {
        "fr": {
            "subject": "Vérifiez votre email - Métro-Taxi",
            "title": "Bienvenue sur Métro-Taxi !",
            "greeting": f"Bonjour {name},",
            "message": "Merci de vous être inscrit sur Métro-Taxi. Pour activer votre compte, veuillez cliquer sur le bouton ci-dessous :",
            "button": "Vérifier mon email",
            "footer": "Ce lien expire dans 24 heures.",
            "ignore": "Si vous n'avez pas créé de compte, vous pouvez ignorer cet email."
        },
        "en": {
            "subject": "Verify your email - Métro-Taxi",
            "title": "Welcome to Métro-Taxi!",
            "greeting": f"Hello {name},",
            "message": "Thank you for signing up for Métro-Taxi. To activate your account, please click the button below:",
            "button": "Verify my email",
            "footer": "This link expires in 24 hours.",
            "ignore": "If you didn't create an account, you can ignore this email."
        },
        "es": {
            "subject": "Verifica tu email - Métro-Taxi",
            "title": "¡Bienvenido a Métro-Taxi!",
            "greeting": f"Hola {name},",
            "message": "Gracias por registrarte en Métro-Taxi. Para activar tu cuenta, haz clic en el botón de abajo:",
            "button": "Verificar mi email",
            "footer": "Este enlace expira en 24 horas.",
            "ignore": "Si no creaste una cuenta, puedes ignorar este email."
        },
        "de": {
            "subject": "Bestätigen Sie Ihre E-Mail - Métro-Taxi",
            "title": "Willkommen bei Métro-Taxi!",
            "greeting": f"Hallo {name},",
            "message": "Vielen Dank für Ihre Anmeldung bei Métro-Taxi. Um Ihr Konto zu aktivieren, klicken Sie bitte auf die Schaltfläche unten:",
            "button": "E-Mail bestätigen",
            "footer": "Dieser Link läuft in 24 Stunden ab.",
            "ignore": "Wenn Sie kein Konto erstellt haben, können Sie diese E-Mail ignorieren."
        },
        "pt": {
            "subject": "Verifique seu email - Métro-Taxi",
            "title": "Bem-vindo ao Métro-Taxi!",
            "greeting": f"Olá {name},",
            "message": "Obrigado por se registrar no Métro-Taxi. Para ativar sua conta, clique no botão abaixo:",
            "button": "Verificar meu email",
            "footer": "Este link expira em 24 horas.",
            "ignore": "Se você não criou uma conta, pode ignorar este email."
        }
    }

    t = templates.get(lang[:2], templates["fr"])

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #0a0a0a;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 40px 0;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #18181b; border-radius: 8px; overflow: hidden;">
                    <tr><td style="background-color: #FFD60A; padding: 30px; text-align: center;"><h1 style="margin: 0; color: #000; font-size: 28px; font-weight: bold;">MÉTRO-TAXI</h1></td></tr>
                    <tr><td style="padding: 40px 30px;">
                        <h2 style="color: #ffffff; margin: 0 0 20px 0; font-size: 24px;">{t['title']}</h2>
                        <p style="color: #a1a1aa; margin: 0 0 10px 0; font-size: 16px;">{t['greeting']}</p>
                        <p style="color: #a1a1aa; margin: 0 0 30px 0; font-size: 16px;">{t['message']}</p>
                        <table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
                            <a href="{verification_url}" style="display: inline-block; background-color: #FFD60A; color: #000; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-weight: bold; font-size: 16px;">{t['button']}</a>
                        </td></tr></table>
                        <p style="color: #71717a; margin: 30px 0 0 0; font-size: 14px;">{t['footer']}</p>
                        <p style="color: #52525b; margin: 20px 0 0 0; font-size: 12px;">{t['ignore']}</p>
                    </td></tr>
                    <tr><td style="background-color: #09090b; padding: 20px 30px; text-align: center;"><p style="color: #52525b; margin: 0; font-size: 12px;">© 2026 Métro-Taxi. Système de déplacement intelligent par covoiturage.</p></td></tr>
                </table>
            </td></tr>
        </table>
    </body></html>
    """

    try:
        params = {"from": SENDER_EMAIL, "to": [email], "subject": t['subject'], "html": html_content}
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Verification email sent to {email}, ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send verification email to {email}: {str(e)}")
        return False


async def send_subscription_confirmation_email(email: str, name: str, plan_name: str, expires_at: str, lang: str = "fr"):
    """Send subscription confirmation email using Resend"""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, skipping email")
        return False

    templates = {
        "fr": {
            "subject": "Abonnement activé - Métro-Taxi",
            "title": "Votre abonnement est actif !",
            "greeting": f"Bonjour {name},",
            "message": f"Votre abonnement <strong>{plan_name}</strong> a été activé avec succès.",
            "valid_until": f"Valide jusqu'au : <strong>{expires_at}</strong>",
            "cta": "Accéder à mon compte",
            "enjoy": "Profitez de trajets illimités sur tout le réseau Métro-Taxi !",
            "multi_device_title": "Utiliser sur plusieurs appareils ?",
            "multi_device_text": f"Connectez-vous simplement avec votre email <strong>{email}</strong> sur votre téléphone, tablette ou ordinateur pour accéder à votre abonnement partout.",
            "multi_device_warning": "Ne créez pas un nouveau compte - utilisez toujours le même email pour éviter un double paiement."
        },
        "en": {
            "subject": "Subscription activated - Métro-Taxi",
            "title": "Your subscription is active!",
            "greeting": f"Hello {name},",
            "message": f"Your <strong>{plan_name}</strong> subscription has been successfully activated.",
            "valid_until": f"Valid until: <strong>{expires_at}</strong>",
            "cta": "Access my account",
            "enjoy": "Enjoy unlimited rides across the entire Métro-Taxi network!",
            "multi_device_title": "Use on multiple devices?",
            "multi_device_text": f"Simply log in with your email <strong>{email}</strong> on your phone, tablet or computer to access your subscription everywhere.",
            "multi_device_warning": "Don't create a new account - always use the same email to avoid double payment."
        }
    }

    t = templates.get(lang[:2], templates["fr"])

    html_content = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #0a0a0a;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 40px 0;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #18181b; border-radius: 8px;">
                    <tr><td style="background-color: #22c55e; padding: 30px; text-align: center;"><h1 style="margin: 0; color: #fff; font-size: 28px;">✓ {t['title']}</h1></td></tr>
                    <tr><td style="padding: 40px 30px;">
                        <p style="color: #a1a1aa; margin: 0 0 10px 0; font-size: 16px;">{t['greeting']}</p>
                        <p style="color: #ffffff; margin: 0 0 20px 0; font-size: 18px;">{t['message']}</p>
                        <p style="color: #FFD60A; margin: 0 0 30px 0; font-size: 16px;">{t['valid_until']}</p>
                        <p style="color: #a1a1aa; margin: 0; font-size: 14px;">{t['enjoy']}</p>
                    </td></tr>
                    <tr><td style="padding: 0 30px 30px 30px;">
                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fef3c7; border-radius: 8px; border-left: 4px solid #f59e0b;">
                            <tr><td style="padding: 20px;">
                                <p style="color: #92400e; margin: 0 0 10px 0; font-size: 16px; font-weight: bold;">📱 {t['multi_device_title']}</p>
                                <p style="color: #78350f; margin: 0 0 10px 0; font-size: 14px;">{t['multi_device_text']}</p>
                                <p style="color: #dc2626; margin: 0; font-size: 13px; font-weight: bold;">⚠️ {t['multi_device_warning']}</p>
                            </td></tr>
                        </table>
                    </td></tr>
                    <tr><td style="background-color: #09090b; padding: 20px; text-align: center;"><p style="color: #52525b; margin: 0; font-size: 12px;">© 2026 Métro-Taxi</p></td></tr>
                </table>
            </td></tr>
        </table>
    </body></html>
    """

    try:
        params = {"from": SENDER_EMAIL, "to": [email], "subject": t['subject'], "html": html_content}
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Subscription email sent to {email}, ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send subscription email to {email}: {str(e)}")
        return False


async def send_payout_notification_email(email: str, name: str, amount: float, total_km: float, rides_count: int, months: list, payout_date: str, lang: str = "fr"):
    """Send payout notification email to driver when payment is processed"""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, skipping payout email")
        return False

    months_str = ", ".join(months) if months else "N/A"

    templates = {
        "fr": {
            "subject": f"Virement effectué - €{amount:.2f} - Métro-Taxi",
            "title": "Virement effectué !",
            "greeting": f"Bonjour {name},",
            "message": "Votre virement mensuel a été traité avec succès.",
            "amount_label": "Montant viré", "amount": f"€{amount:.2f}",
            "details_title": "Détails du virement",
            "km_label": "Kilomètres parcourus", "km_value": f"{total_km:.1f} km",
            "rides_label": "Nombre de trajets", "rides_value": f"{rides_count}",
            "period_label": "Période", "period_value": months_str,
            "date_label": "Date du virement", "date_value": payout_date,
            "note": "Le virement sera crédité sur votre compte bancaire sous 2-3 jours ouvrés.",
            "thanks": "Merci pour votre engagement avec Métro-Taxi !"
        },
        "en": {
            "subject": f"Payout processed - €{amount:.2f} - Métro-Taxi",
            "title": "Payout processed!",
            "greeting": f"Hello {name},",
            "message": "Your monthly payout has been successfully processed.",
            "amount_label": "Amount transferred", "amount": f"€{amount:.2f}",
            "details_title": "Payout details",
            "km_label": "Kilometers driven", "km_value": f"{total_km:.1f} km",
            "rides_label": "Number of rides", "rides_value": f"{rides_count}",
            "period_label": "Period", "period_value": months_str,
            "date_label": "Payout date", "date_value": payout_date,
            "note": "The transfer will be credited to your bank account within 2-3 business days.",
            "thanks": "Thank you for your commitment with Métro-Taxi!"
        }
    }

    t = templates.get(lang[:2], templates["fr"])

    html_content = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #0a0a0a;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 40px 0;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #18181b; border-radius: 8px;">
                    <tr><td style="background-color: #FFD60A; padding: 30px; text-align: center;"><h1 style="margin: 0; color: #000; font-size: 28px;">💰 {t['title']}</h1></td></tr>
                    <tr><td style="padding: 40px 30px;">
                        <p style="color: #a1a1aa; margin: 0 0 10px 0; font-size: 16px;">{t['greeting']}</p>
                        <p style="color: #ffffff; margin: 0 0 30px 0; font-size: 18px;">{t['message']}</p>
                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #22c55e; border-radius: 8px; margin-bottom: 30px;">
                            <tr><td style="padding: 25px; text-align: center;">
                                <p style="color: rgba(255,255,255,0.8); margin: 0 0 5px 0; font-size: 14px;">{t['amount_label']}</p>
                                <p style="color: #fff; margin: 0; font-size: 36px; font-weight: bold;">{t['amount']}</p>
                            </td></tr>
                        </table>
                        <p style="color: #FFD60A; margin: 0 0 15px 0; font-size: 16px; font-weight: bold;">{t['details_title']}</p>
                        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 25px;">
                            <tr><td style="padding: 10px 0; border-bottom: 1px solid #27272a;"><span style="color: #71717a; font-size: 14px;">{t['km_label']}</span></td><td style="padding: 10px 0; border-bottom: 1px solid #27272a; text-align: right;"><span style="color: #fff; font-size: 14px; font-weight: bold;">{t['km_value']}</span></td></tr>
                            <tr><td style="padding: 10px 0; border-bottom: 1px solid #27272a;"><span style="color: #71717a; font-size: 14px;">{t['rides_label']}</span></td><td style="padding: 10px 0; border-bottom: 1px solid #27272a; text-align: right;"><span style="color: #fff; font-size: 14px; font-weight: bold;">{t['rides_value']}</span></td></tr>
                            <tr><td style="padding: 10px 0; border-bottom: 1px solid #27272a;"><span style="color: #71717a; font-size: 14px;">{t['period_label']}</span></td><td style="padding: 10px 0; border-bottom: 1px solid #27272a; text-align: right;"><span style="color: #fff; font-size: 14px;">{t['period_value']}</span></td></tr>
                            <tr><td style="padding: 10px 0;"><span style="color: #71717a; font-size: 14px;">{t['date_label']}</span></td><td style="padding: 10px 0; text-align: right;"><span style="color: #fff; font-size: 14px;">{t['date_value']}</span></td></tr>
                        </table>
                        <p style="color: #a1a1aa; margin: 0 0 20px 0; font-size: 13px; padding: 15px; background-color: #27272a; border-radius: 6px;">ℹ️ {t['note']}</p>
                        <p style="color: #FFD60A; margin: 0; font-size: 14px; text-align: center;">{t['thanks']}</p>
                    </td></tr>
                    <tr><td style="background-color: #09090b; padding: 20px; text-align: center;"><p style="color: #52525b; margin: 0; font-size: 12px;">© 2026 Métro-Taxi - Plateforme de transport partagé</p></td></tr>
                </table>
            </td></tr>
        </table>
    </body></html>
    """

    try:
        params = {"from": SENDER_EMAIL, "to": [email], "subject": t['subject'], "html": html_content}
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Payout notification email sent to {email}, ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send payout email to {email}: {str(e)}")
        return False


async def send_subscription_expiry_reminder_email(email: str, name: str, hours_remaining: int, expires_at: str, lang: str = "fr"):
    """Send subscription expiry reminder email to user"""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, skipping expiry reminder email")
        return False

    frontend_url = os.environ.get("FRONTEND_URL", "https://metro-taxi-demo.emergent.host")
    renewal_url = f"{frontend_url}/subscription"

    if hours_remaining <= 1:
        urgency, urgency_color = "critical", "#ef4444"
    elif hours_remaining <= 24:
        urgency, urgency_color = "high", "#f97316"
    else:
        urgency, urgency_color = "medium", "#eab308"

    templates = {
        "fr": {
            "critical": {"subject": "⚠️ URGENT - Votre abonnement Métro-Taxi expire AUJOURD'HUI", "title": "Abonnement expire aujourd'hui !", "message": "Votre abonnement Métro-Taxi expire dans moins d'une heure. Renouvelez immédiatement pour éviter toute interruption de service."},
            "high": {"subject": "⚠️ Rappel - Votre abonnement Métro-Taxi expire dans 24h", "title": "Abonnement expire demain !", "message": f"Votre abonnement Métro-Taxi expire dans {hours_remaining} heures. Pensez à le renouveler dès maintenant."},
            "medium": {"subject": "📢 Rappel - Votre abonnement Métro-Taxi expire bientôt", "title": "Abonnement expire bientôt", "message": f"Votre abonnement Métro-Taxi expire dans {hours_remaining} heures. Nous vous recommandons de le renouveler avant l'expiration."},
            "greeting": f"Bonjour {name},",
            "expires_label": "Date d'expiration",
            "button_text": "RENOUVELER MON ABONNEMENT",
            "note": "Si vous ne renouvelez pas votre abonnement, vous ne pourrez plus utiliser les services Métro-Taxi.",
            "thanks": "L'équipe Métro-Taxi"
        },
        "en": {
            "critical": {"subject": "⚠️ URGENT - Your Métro-Taxi subscription expires TODAY", "title": "Subscription expires today!", "message": "Your Métro-Taxi subscription expires in less than an hour. Renew immediately to avoid any service interruption."},
            "high": {"subject": "⚠️ Reminder - Your Métro-Taxi subscription expires in 24h", "title": "Subscription expires tomorrow!", "message": f"Your Métro-Taxi subscription expires in {hours_remaining} hours. Consider renewing now."},
            "medium": {"subject": "📢 Reminder - Your Métro-Taxi subscription expires soon", "title": "Subscription expires soon", "message": f"Your Métro-Taxi subscription expires in {hours_remaining} hours. We recommend renewing before expiration."},
            "greeting": f"Hello {name},",
            "expires_label": "Expiration date",
            "button_text": "RENEW MY SUBSCRIPTION",
            "note": "If you don't renew your subscription, you won't be able to use Métro-Taxi services.",
            "thanks": "The Métro-Taxi Team"
        }
    }

    t = templates.get(lang[:2], templates["fr"])
    urgency_t = t[urgency]

    try:
        expires_dt = datetime.fromisoformat(expires_at)
        expires_formatted = expires_dt.strftime("%d/%m/%Y à %H:%M")
    except Exception:
        expires_formatted = expires_at

    html_content = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #0a0a0a;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 40px 0;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #18181b; border-radius: 8px;">
                    <tr><td style="background-color: {urgency_color}; padding: 30px; text-align: center;"><h1 style="margin: 0; color: #000; font-size: 24px;">⚠️ {urgency_t['title']}</h1></td></tr>
                    <tr><td style="padding: 40px 30px;">
                        <p style="color: #a1a1aa; margin: 0 0 10px 0; font-size: 16px;">{t['greeting']}</p>
                        <p style="color: #ffffff; margin: 0 0 30px 0; font-size: 18px;">{urgency_t['message']}</p>
                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #27272a; border-radius: 8px; margin-bottom: 30px; border-left: 4px solid {urgency_color};">
                            <tr><td style="padding: 20px;">
                                <p style="color: #a1a1aa; margin: 0 0 5px 0; font-size: 14px;">{t['expires_label']}</p>
                                <p style="color: #ffffff; margin: 0; font-size: 20px; font-weight: bold;">{expires_formatted}</p>
                            </td></tr>
                        </table>
                        <table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
                            <a href="{renewal_url}" style="display: inline-block; background-color: #FFD60A; color: #000; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-weight: bold; font-size: 16px;">{t['button_text']}</a>
                        </td></tr></table>
                        <p style="color: #71717a; margin: 30px 0 0 0; font-size: 14px; text-align: center;">{t['note']}</p>
                    </td></tr>
                    <tr><td style="background-color: #09090b; padding: 20px; text-align: center;">
                        <p style="color: #52525b; margin: 0 0 5px 0; font-size: 14px;">{t['thanks']}</p>
                        <p style="color: #52525b; margin: 0; font-size: 12px;">© 2026 Métro-Taxi - Plateforme de transport partagé</p>
                    </td></tr>
                </table>
            </td></tr>
        </table>
    </body></html>
    """

    try:
        params = {"from": SENDER_EMAIL, "to": [email], "subject": urgency_t['subject'], "html": html_content}
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Subscription expiry reminder email sent to {email}, ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send expiry reminder email to {email}: {str(e)}")
        return False


async def send_gift_subscription_email(email: str, name: str, plan_name: str, expires_at: str, reason: str = "", lang: str = "fr"):
    """Send gift subscription notification email"""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, skipping gift email")
        return False

    templates = {
        "fr": {
            "subject": "🎁 Abonnement offert - Métro-Taxi",
            "title": "Un abonnement vous a été offert !",
            "greeting": f"Bonjour {name},",
            "message": f"Un abonnement <strong>{plan_name}</strong> vous a été offert par l'équipe Métro-Taxi.",
            "valid_until": f"Valide jusqu'au : <strong>{expires_at}</strong>",
            "reason_label": "Motif",
            "enjoy": "Profitez de trajets illimités !"
        },
        "en": {
            "subject": "🎁 Subscription gifted - Métro-Taxi",
            "title": "A subscription has been gifted to you!",
            "greeting": f"Hello {name},",
            "message": f"A <strong>{plan_name}</strong> subscription has been gifted to you by the Métro-Taxi team.",
            "valid_until": f"Valid until: <strong>{expires_at}</strong>",
            "reason_label": "Reason",
            "enjoy": "Enjoy unlimited rides!"
        }
    }

    t = templates.get(lang[:2], templates["fr"])
    reason_html = f"<p style='color: #a1a1aa; font-size: 14px;'>{t['reason_label']}: {reason}</p>" if reason else ""

    html_content = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #0a0a0a;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 40px 0;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #18181b; border-radius: 8px;">
                    <tr><td style="background-color: #FFD60A; padding: 30px; text-align: center;"><h1 style="margin: 0; color: #000; font-size: 28px;">🎁 {t['title']}</h1></td></tr>
                    <tr><td style="padding: 40px 30px;">
                        <p style="color: #a1a1aa; margin: 0 0 10px 0; font-size: 16px;">{t['greeting']}</p>
                        <p style="color: #ffffff; margin: 0 0 20px 0; font-size: 18px;">{t['message']}</p>
                        <p style="color: #FFD60A; margin: 0 0 20px 0; font-size: 16px;">{t['valid_until']}</p>
                        {reason_html}
                        <p style="color: #a1a1aa; margin: 20px 0 0 0; font-size: 14px;">{t['enjoy']}</p>
                    </td></tr>
                    <tr><td style="background-color: #09090b; padding: 20px; text-align: center;"><p style="color: #52525b; margin: 0; font-size: 12px;">© 2026 Métro-Taxi</p></td></tr>
                </table>
            </td></tr>
        </table>
    </body></html>
    """

    try:
        params = {"from": SENDER_EMAIL, "to": [email], "subject": t['subject'], "html": html_content}
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Gift subscription email sent to {email}, ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send gift email to {email}: {str(e)}")
        return False
