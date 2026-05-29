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



async def send_admin_otp_email(email: str, otp_code: str, client_ip: str = "N/A"):
    """Send a 6-digit OTP to admin email for 2FA login."""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, admin OTP email NOT sent")
        return False

    html_content = f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"></head>
    <body style="font-family:Helvetica,Arial,sans-serif;background:#0a0a0a;margin:0;padding:40px 20px;color:#ffffff;">
      <div style="max-width:540px;margin:0 auto;background:#1a1a1a;border-radius:12px;padding:40px;border-top:4px solid #F7C600;">
        <div style="text-align:center;margin-bottom:30px;">
          <div style="display:inline-block;background:#F7C600;width:60px;height:60px;border-radius:14px;line-height:60px;font-size:34px;">🚖</div>
          <h1 style="color:#F7C600;margin:16px 0 4px 0;font-size:22px;letter-spacing:-0.5px;">MÉTRO-TAXI</h1>
          <p style="color:#888;margin:0;font-size:13px;letter-spacing:1px;">ADMINISTRATION — 2FA</p>
        </div>
        <h2 style="color:#ffffff;font-size:20px;margin:20px 0 10px 0;">Code de connexion sécurisé</h2>
        <p style="color:#cccccc;line-height:1.6;margin-bottom:24px;">
          Utilisez ce code pour finaliser votre connexion au dashboard administrateur&nbsp;:
        </p>
        <div style="background:#0a0a0a;border:2px dashed #F7C600;border-radius:10px;padding:24px;text-align:center;margin:20px 0;">
          <div style="color:#F7C600;font-size:42px;font-weight:900;letter-spacing:12px;font-family:'Courier New',monospace;">
            {otp_code}
          </div>
        </div>
        <p style="color:#999;font-size:13px;line-height:1.6;">
          ⏱️ Ce code expire dans <strong style="color:#F7C600;">5 minutes</strong>.<br>
          🌍 Tentative depuis l'adresse IP&nbsp;: <code style="background:#0a0a0a;padding:2px 6px;border-radius:3px;">{client_ip}</code>
        </p>
        <hr style="border:none;border-top:1px solid #333;margin:30px 0;">
        <p style="color:#ff6b6b;font-size:13px;line-height:1.5;">
          <strong>⚠️ Vous n'êtes pas à l'origine de cette demande&nbsp;?</strong><br>
          Ignorez ce message et changez immédiatement votre mot de passe administrateur.
        </p>
        <p style="color:#555;font-size:11px;text-align:center;margin-top:30px;">
          Métro-Taxi © 2026 — Email automatique, ne pas répondre.
        </p>
      </div>
    </body></html>
    """

    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": "🔐 Code de connexion Admin Métro-Taxi",
            "html": html_content
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Admin OTP email sent to {email}, ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send admin OTP email to {email}: {str(e)}")
        return False




async def send_pioneer_welcome_email(email: str, name: str, pioneer_number: int, source: str = None):
    """Send 'Welcome Pioneer #X' email to newly registered driver (after email verification)."""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, pioneer welcome email NOT sent")
        return False

    source_line = f"<p style='color:#999;font-size:13px;margin:0 0 18px 0;'>Source d'inscription : <strong style='color:#FFD60A;'>{source}</strong></p>" if source else ""

    html_content = f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"></head>
    <body style="font-family:Helvetica,Arial,sans-serif;background:#0a0a0a;margin:0;padding:40px 20px;color:#ffffff;">
      <div style="max-width:600px;margin:0 auto;background:#1a1a1a;border-radius:12px;overflow:hidden;border-top:6px solid #FFD60A;">

        <div style="background:#FFD60A;padding:30px;text-align:center;">
          <h1 style="margin:0;color:#000;font-size:30px;letter-spacing:-1px;">MÉTRO-TAXI</h1>
          <p style="margin:8px 0 0 0;color:#000;font-size:14px;font-weight:bold;">CHAUFFEUR PIONNIER #{pioneer_number}</p>
        </div>

        <div style="padding:36px 30px;">
          <h2 style="color:#FFD60A;font-size:22px;margin:0 0 18px 0;">Bonjour {name} 👋</h2>

          <p style="color:#e4e4e7;line-height:1.7;font-size:15px;margin:0 0 16px 0;">
            Bienvenue chez <strong style="color:#FFD60A;">Métro-Taxi</strong> 🇫🇷. Tu es désormais notre <strong style="color:#FFD60A;">chauffeur pionnier #{pioneer_number}</strong> — un statut que personne ne pourra te prendre.
          </p>
          {source_line}

          <h3 style="color:#FFD60A;font-size:16px;margin:28px 0 12px 0;">📋 La stratégie en transparence</h3>
          <p style="color:#cccccc;line-height:1.7;font-size:14px;margin:0 0 16px 0;">
            On a fait un choix volontaire : <strong>ne pas vendre d'abonnements clients tant qu'on n'a pas atteint une couverture chauffeurs suffisante</strong> en zone pilote (Paris + petite couronne 92/93/94). Pourquoi ? Pour éviter qu'un client paie et attende sans chauffeur dispo dans sa zone — ça tuerait la réputation de Métro-Taxi avant qu'on décolle.
          </p>
          <p style="color:#cccccc;line-height:1.7;font-size:14px;margin:0 0 16px 0;">
            Donc concrètement :
          </p>
          <ul style="color:#cccccc;line-height:1.8;font-size:14px;margin:0 0 18px 0;padding-left:20px;">
            <li>🚖 On recrute à fond les chauffeurs (<strong>objectif 150 inscrits</strong> pour lancer la zone pilote payante)</li>
            <li>🚖 Pendant cette période, <strong>continue ton activité actuelle</strong> (Uber/Bolt/Heetch) en parallèle</li>
            <li>🚖 Dès qu'on franchit le cap, tu commences à recevoir des courses</li>
          </ul>

          <h3 style="color:#FFD60A;font-size:16px;margin:28px 0 12px 0;">💰 Ton modèle Métro-Taxi</h3>
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;border-radius:8px;border-left:4px solid #FFD60A;margin:0 0 18px 0;">
            <tr><td style="padding:18px 20px;">
              <p style="color:#fff;margin:0 0 8px 0;font-size:14px;">✅ <strong>1,50 € / km parcouru</strong> avec au moins un abonné Métro-Taxi à bord</p>
              <p style="color:#fff;margin:0 0 8px 0;font-size:14px;">✅ <strong>0 % de commission</strong>, à vie</p>
              <p style="color:#fff;margin:0 0 8px 0;font-size:14px;">✅ <strong>Versement chaque 10 du mois</strong>, ponctuel</p>
              <p style="color:#fff;margin:0;font-size:14px;">✅ <strong>Aucun engagement</strong>, compatible avec tes autres plateformes</p>
            </tr></td>
          </table>

          <h3 style="color:#FFD60A;font-size:16px;margin:28px 0 12px 0;">🎁 Ton statut de pionnier</h3>
          <p style="color:#cccccc;line-height:1.7;font-size:14px;margin:0 0 18px 0;">
            En tant que <strong>chauffeur pionnier #{pioneer_number}</strong>, tu auras la <strong>priorité</strong> sur les premières courses dans ta zone et un statut de référent dans la communauté Métro-Taxi quand on grandira. Ta place dans l'histoire de la plateforme est gravée.
          </p>

          <hr style="border:none;border-top:1px solid #333;margin:28px 0;">

          <p style="color:#a1a1aa;font-size:14px;line-height:1.6;margin:0 0 18px 0;">
            Si tu as la moindre question, écris-moi directement sur WhatsApp ou réponds à cet email — je m'en occupe personnellement.
          </p>

          <p style="color:#FFD60A;font-size:15px;margin:24px 0 0 0;">
            Bonne route 🚖🇫🇷<br>
            <strong>— Judée, fondateur Métro-Taxi</strong>
          </p>
        </div>

        <div style="background:#09090b;padding:20px;text-align:center;border-top:1px solid #27272a;">
          <p style="color:#52525b;margin:0;font-size:12px;">© 2026 Métro-Taxi — Plateforme française de covoiturage à maillage intelligent</p>
        </div>
      </div>
    </body></html>
    """

    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": f"🚖 Bienvenue chauffeur pionnier #{pioneer_number} chez Métro-Taxi",
            "html": html_content
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Pioneer welcome email sent to {email} (#{pioneer_number}), ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send pioneer welcome email to {email}: {str(e)}")
        return False


async def send_founder_alert_new_driver(driver_data: dict):
    """Send instant alert to founder when a new driver signs up.

    driver_data must contain: first_name, last_name, email, phone, pioneer_number,
    region_id (optional), vehicle_type, source_inscription (optional)
    """
    founder_email = os.environ.get('FOUNDER_ALERT_EMAIL')
    if not founder_email:
        logging.warning("FOUNDER_ALERT_EMAIL not configured, founder alert email NOT sent")
        return False
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, founder alert email NOT sent")
        return False

    name = f"{driver_data.get('first_name', '')} {driver_data.get('last_name', '')}".strip()
    email = driver_data.get('email', 'N/A')
    phone = driver_data.get('phone', 'N/A')
    pioneer_number = driver_data.get('pioneer_number', '?')
    vehicle_type = driver_data.get('vehicle_type', 'N/A')
    source = driver_data.get('source_inscription') or 'Non précisée'
    region_id = driver_data.get('region_id', 'N/A')
    now = datetime.now().strftime("%d/%m/%Y à %H:%M")

    html_content = f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"></head>
    <body style="font-family:Helvetica,Arial,sans-serif;background:#0a0a0a;margin:0;padding:30px 20px;color:#ffffff;">
      <div style="max-width:560px;margin:0 auto;background:#1a1a1a;border-radius:10px;overflow:hidden;border-top:4px solid #22c55e;">
        <div style="background:#22c55e;padding:24px;text-align:center;">
          <h1 style="margin:0;color:#fff;font-size:22px;">🚖 NOUVEAU CHAUFFEUR PIONNIER #{pioneer_number}</h1>
        </div>
        <div style="padding:28px 26px;">
          <p style="color:#a1a1aa;margin:0 0 18px 0;font-size:14px;">Inscrit le {now}</p>

          <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 20px 0;">
            <tr><td style="padding:10px 0;border-bottom:1px solid #27272a;width:35%;"><span style="color:#71717a;font-size:13px;">Nom complet</span></td>
                <td style="padding:10px 0;border-bottom:1px solid #27272a;text-align:right;"><span style="color:#fff;font-size:14px;font-weight:bold;">{name}</span></td></tr>
            <tr><td style="padding:10px 0;border-bottom:1px solid #27272a;"><span style="color:#71717a;font-size:13px;">Email</span></td>
                <td style="padding:10px 0;border-bottom:1px solid #27272a;text-align:right;"><span style="color:#fff;font-size:13px;">{email}</span></td></tr>
            <tr><td style="padding:10px 0;border-bottom:1px solid #27272a;"><span style="color:#71717a;font-size:13px;">Téléphone</span></td>
                <td style="padding:10px 0;border-bottom:1px solid #27272a;text-align:right;"><span style="color:#fff;font-size:14px;font-weight:bold;">{phone}</span></td></tr>
            <tr><td style="padding:10px 0;border-bottom:1px solid #27272a;"><span style="color:#71717a;font-size:13px;">Véhicule</span></td>
                <td style="padding:10px 0;border-bottom:1px solid #27272a;text-align:right;"><span style="color:#fff;font-size:13px;">{vehicle_type}</span></td></tr>
            <tr><td style="padding:10px 0;border-bottom:1px solid #27272a;"><span style="color:#71717a;font-size:13px;">Région</span></td>
                <td style="padding:10px 0;border-bottom:1px solid #27272a;text-align:right;"><span style="color:#fff;font-size:13px;">{region_id}</span></td></tr>
            <tr><td style="padding:10px 0;"><span style="color:#71717a;font-size:13px;">Comment a-t-il connu Métro-Taxi&nbsp;?</span></td>
                <td style="padding:10px 0;text-align:right;"><span style="color:#FFD60A;font-size:14px;font-weight:bold;">{source}</span></td></tr>
          </table>

          <p style="color:#cccccc;font-size:13px;line-height:1.6;margin:24px 0 0 0;text-align:center;">
            📊 <a href="https://metro-taxi.com/admin" style="color:#FFD60A;text-decoration:none;font-weight:bold;">Voir dans le dashboard admin</a>
          </p>
        </div>
        <div style="background:#09090b;padding:14px;text-align:center;">
          <p style="color:#52525b;margin:0;font-size:11px;">Alerte automatique fondateur — Métro-Taxi © 2026</p>
        </div>
      </div>
    </body></html>
    """

    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [founder_email],
            "subject": f"🚖 Nouveau chauffeur pionnier #{pioneer_number} — {name}",
            "html": html_content
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Founder alert email sent for new driver #{pioneer_number} to {founder_email}, ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send founder alert email: {str(e)}")
        return False



async def send_founding_member_welcome(email: str, name: str, founding_number: int, total_drivers: int = 9, target_drivers: int = 150):
    """Send welcome email to a new Membre Fondateur (founding member).

    Tells them they're locked in at 53,99€/mois for life when subscriptions open.
    """
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, skipping founding member email")
        return False

    progress_pct = round((total_drivers / target_drivers) * 100, 1)

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background:#0A0A0B; color:#E4E4E7; padding:0; margin:0; }}
  .wrap {{ max-width:600px; margin:0 auto; background:#0A0A0B; padding:32px 24px; }}
  .badge {{ display:inline-block; background:#FFD60A; color:#000; padding:8px 16px; border-radius:999px; font-weight:bold; font-size:14px; letter-spacing:0.5px; }}
  h1 {{ color:#FFD60A; font-size:28px; margin:24px 0 8px; }}
  h2 {{ color:#FFD60A; font-size:18px; margin:32px 0 12px; }}
  p {{ line-height:1.6; color:#D4D4D8; }}
  .card {{ background:#18181B; border:1px solid #27272A; border-radius:8px; padding:20px; margin:20px 0; }}
  .price {{ font-size:36px; font-weight:bold; color:#FFD60A; }}
  .price small {{ font-size:14px; color:#A1A1AA; font-weight:normal; }}
  .strike {{ text-decoration:line-through; color:#71717A; font-size:18px; margin-left:8px; }}
  .bar {{ background:#27272A; border-radius:999px; height:10px; overflow:hidden; margin:8px 0; }}
  .bar-fill {{ background:linear-gradient(90deg,#FFD60A,#F59E0B); height:100%; width:{progress_pct}%; }}
  .perks li {{ margin:8px 0; color:#E4E4E7; }}
  .perks li::marker {{ color:#FFD60A; }}
  .footer {{ color:#71717A; font-size:12px; text-align:center; margin-top:32px; padding-top:24px; border-top:1px solid #27272A; }}
  a {{ color:#FFD60A; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="badge">🏆 MEMBRE FONDATEUR #{founding_number}</div>
  <h1>Bienvenue dans le cercle Judée, {name} !</h1>
  <p>Tu fais désormais partie des <strong style="color:#FFD60A">membres fondateurs Métro-Taxi</strong> — les visionnaires qui nous ont fait confiance avant tout le monde.</p>

  <div class="card">
    <h2 style="margin-top:0">🔒 Ton tarif verrouillé À VIE</h2>
    <p class="price">53,99€<small>/mois</small><span class="strike">79€/mois (tarif futur)</span></p>
    <p style="color:#A1A1AA; font-size:14px">Ce tarif te sera réservé pour <strong>toute la durée de ton abonnement</strong>, peu importe les hausses futures. Une promesse de fondateur à fondateur.</p>
  </div>

  <h2>🎁 Tes 4 privilèges exclusifs</h2>
  <ul class="perks">
    <li><strong>Tarif fondateur 53,99€/mois verrouillé à vie</strong> (vs ~79€/mois en tarif standard)</li>
    <li><strong>Accès prioritaire 48h avant l'ouverture publique</strong> des abonnements</li>
    <li><strong>Badge "Membre Fondateur"</strong> visible dans l'application</li>
    <li><strong>Newsletter privée</strong> avec les coulisses du projet et nos décisions stratégiques</li>
  </ul>

  <div class="card">
    <h2 style="margin-top:0">📍 Où on en est aujourd'hui</h2>
    <p>{total_drivers} chauffeurs VTC pionniers / {target_drivers} pour l'ouverture officielle</p>
    <div class="bar"><div class="bar-fill"></div></div>
    <p style="color:#A1A1AA; font-size:14px">Tu seras notifié·e par email dès qu'on atteint les 150 chauffeurs zone pilote (Paris + petite couronne).</p>
  </div>

  <h2>🤝 Pourquoi cette attente ?</h2>
  <p>On a fait le choix difficile mais juste : <strong>ne pas vendre d'abonnement avant d'avoir assez de chauffeurs</strong> pour te transporter. Pas de vent vendu, pas de promesse en l'air. Quand on ouvre, tout fonctionne.</p>

  <p style="margin-top:32px">À très vite,<br><strong style="color:#FFD60A">Judée Mané</strong><br>Fondateur — Métro-Taxi</p>

  <div class="footer">
    Métro-Taxi · <a href="https://metro-taxi.com">metro-taxi.com</a><br>
    Cet email a été envoyé à {email}. Tu reçois cet email car tu as rejoint la liste des Membres Fondateurs.
  </div>
</div>
</body>
</html>
"""

    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": f"🏆 Bienvenue Membre Fondateur #{founding_number} — Tarif 53,99€/mois verrouillé à vie",
            "html": html_content,
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Founding member welcome email sent to {email} (member #{founding_number}), ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send founding member email: {str(e)}")
        return False



# ============================================
# PARTENARIAT PATRON VTC (B2B flotte)
# ============================================
async def send_fleet_partnership_alert(application: dict):
    """Alerte fondateur quand un patron VTC soumet une demande de partenariat flotte."""
    founder_email = os.environ.get('FOUNDER_ALERT_EMAIL')
    if not founder_email or not RESEND_API_KEY:
        logging.warning("FOUNDER_ALERT_EMAIL or RESEND_API_KEY missing — fleet partnership alert skipped")
        return False

    name = application.get('full_name', 'N/A')
    company = application.get('company_name', '')
    email = application.get('email', 'N/A')
    phone = application.get('phone', 'N/A')
    fleet_size = application.get('fleet_size', 0)
    city = application.get('city', 'N/A')
    message = (application.get('message') or '').replace('\n', '<br>')
    now = datetime.now().strftime("%d/%m/%Y à %H:%M")

    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"></head>
    <body style="font-family:Helvetica,Arial,sans-serif;background:#0a0a0a;margin:0;padding:30px 20px;color:#fff;">
      <div style="max-width:560px;margin:0 auto;background:#1a1a1a;border-radius:10px;overflow:hidden;border-top:4px solid #FFD60A;">
        <div style="background:#FFD60A;padding:24px;text-align:center;">
          <h1 style="margin:0;color:#000;font-size:22px;">🏢 NOUVEAU PATRON VTC — DEMANDE B2B</h1>
        </div>
        <div style="padding:28px 26px;">
          <p style="color:#a1a1aa;margin:0 0 18px 0;font-size:14px;">Reçue le {now}</p>
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td style="padding:10px 0;border-bottom:1px solid #27272a;width:38%;color:#71717a;font-size:13px;">Contact</td>
                <td style="padding:10px 0;border-bottom:1px solid #27272a;text-align:right;color:#fff;font-weight:bold;">{name}</td></tr>
            <tr><td style="padding:10px 0;border-bottom:1px solid #27272a;color:#71717a;font-size:13px;">Société</td>
                <td style="padding:10px 0;border-bottom:1px solid #27272a;text-align:right;color:#fff;">{company or '—'}</td></tr>
            <tr><td style="padding:10px 0;border-bottom:1px solid #27272a;color:#71717a;font-size:13px;">Email</td>
                <td style="padding:10px 0;border-bottom:1px solid #27272a;text-align:right;color:#fff;font-size:13px;">{email}</td></tr>
            <tr><td style="padding:10px 0;border-bottom:1px solid #27272a;color:#71717a;font-size:13px;">Téléphone</td>
                <td style="padding:10px 0;border-bottom:1px solid #27272a;text-align:right;color:#fff;font-weight:bold;">{phone}</td></tr>
            <tr><td style="padding:10px 0;border-bottom:1px solid #27272a;color:#71717a;font-size:13px;">Taille flotte</td>
                <td style="padding:10px 0;border-bottom:1px solid #27272a;text-align:right;color:#FFD60A;font-size:18px;font-weight:bold;">{fleet_size} véhicules</td></tr>
            <tr><td style="padding:10px 0;color:#71717a;font-size:13px;">Ville</td>
                <td style="padding:10px 0;text-align:right;color:#fff;">{city}</td></tr>
          </table>
          {f'<div style="margin-top:20px;padding:14px;background:#0a0a0a;border-radius:6px;border-left:3px solid #FFD60A;"><p style="color:#a1a1aa;font-size:12px;margin:0 0 6px 0;text-transform:uppercase;">Message</p><p style="color:#fff;font-size:14px;line-height:1.6;margin:0;">{message}</p></div>' if message else ''}
          <p style="color:#cccccc;font-size:13px;text-align:center;margin:24px 0 0 0;">
            📊 <a href="https://metro-taxi.com/admin" style="color:#FFD60A;text-decoration:none;font-weight:bold;">Voir dans le dashboard admin</a>
          </p>
        </div>
        <div style="background:#09090b;padding:14px;text-align:center;">
          <p style="color:#52525b;margin:0;font-size:11px;">Alerte B2B — Métro-Taxi © 2026</p>
        </div>
      </div>
    </body></html>
    """
    try:
        result = await asyncio.to_thread(resend.Emails.send, {
            "from": SENDER_EMAIL,
            "to": [founder_email],
            "subject": f"🏢 Patron VTC — {name} ({fleet_size} véhicules)",
            "html": html,
        })
        logging.info(f"Fleet partnership alert sent to {founder_email}, ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send fleet partnership alert: {str(e)}")
        return False


async def send_fleet_partnership_confirmation(email: str, name: str, fleet_size: int):
    """Confirme à un patron VTC que sa demande a bien été reçue."""
    if not RESEND_API_KEY:
        return False
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"></head>
    <body style="font-family:Helvetica,Arial,sans-serif;background:#0a0a0a;margin:0;padding:30px 20px;color:#fff;">
      <div style="max-width:560px;margin:0 auto;background:#1a1a1a;border-radius:10px;overflow:hidden;border-top:4px solid #FFD60A;">
        <div style="background:#FFD60A;padding:24px;text-align:center;">
          <h1 style="margin:0;color:#000;font-size:22px;">Demande reçue ✅</h1>
        </div>
        <div style="padding:28px 26px;">
          <p style="color:#fff;font-size:15px;line-height:1.6;">Bonjour {name},</p>
          <p style="color:#cccccc;font-size:14px;line-height:1.6;">
            Merci pour votre intérêt — nous avons bien reçu votre demande de partenariat pour votre flotte de
            <strong style="color:#FFD60A;">{fleet_size} véhicules</strong>.
          </p>
          <p style="color:#cccccc;font-size:14px;line-height:1.6;">
            Judée Souleymane Nazim, fondateur de Métro-Taxi, vous contactera personnellement sous <strong style="color:#FFD60A;">48h</strong>
            pour étudier les modalités de votre partenariat B2B.
          </p>
          <div style="margin:24px 0;padding:16px;background:#0a0a0a;border-radius:8px;">
            <p style="color:#FFD60A;font-size:14px;margin:0 0 8px 0;font-weight:bold;">Modèle Métro-Taxi pour votre flotte :</p>
            <ul style="color:#cccccc;font-size:13px;line-height:1.7;padding-left:20px;margin:0;">
              <li>0% de commission sur vos chauffeurs</li>
              <li>1,50€/km versés à vos chauffeurs avec abonnés à bord</li>
              <li>Paiement le 10 de chaque mois</li>
              <li>Algorithme de mutualisation = revenus optimisés</li>
            </ul>
          </div>
          <p style="color:#71717a;font-size:13px;text-align:center;margin:20px 0 0 0;">À très vite,<br><strong style="color:#FFD60A;">L'équipe Métro-Taxi</strong></p>
        </div>
        <div style="background:#09090b;padding:14px;text-align:center;">
          <p style="color:#52525b;margin:0;font-size:11px;">Métro-Taxi © 2026 — Le covoiturage VTC à 0% de commission</p>
        </div>
      </div>
    </body></html>
    """
    try:
        await asyncio.to_thread(resend.Emails.send, {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": "✅ Demande de partenariat reçue — Métro-Taxi",
            "html": html,
        })
        return True
    except Exception as e:
        logging.error(f"Failed to send fleet partnership confirmation: {str(e)}")
        return False


# ============================================
# BROADCAST LANCEMENT SAINT-DENIS 13 JUIN 2026
# ============================================
async def send_launch_announcement_email(email: str, name: str, pioneer_number: int = None):
    """Email d'annonce officielle du lancement Saint-Denis (13 juin 2026) aux 33 chauffeurs pionniers."""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, launch announcement email NOT sent")
        return False

    pioneer_badge = f"PIONNIER #{pioneer_number}" if pioneer_number else "CHAUFFEUR PIONNIER"
    pioneer_line = f"Tu es <strong style='color:#FFD60A'>chauffeur pionnier #{pioneer_number}</strong> — tu fais partie des 33 visages qui vont incarner cette ouverture." if pioneer_number else "Tu es un de nos <strong style='color:#FFD60A'>chauffeurs pionniers</strong> — tu fais partie des 33 visages qui vont incarner cette ouverture."

    html_content = f"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Helvetica,Arial,sans-serif;background:#0a0a0a;margin:0;padding:30px 20px;color:#fff;">
  <div style="max-width:620px;margin:0 auto;background:#1a1a1a;border-radius:12px;overflow:hidden;border-top:6px solid #FFD60A;">

    <div style="background:#FFD60A;padding:28px 24px;text-align:center;">
      <p style="margin:0 0 6px 0;color:#000;font-size:12px;font-weight:bold;letter-spacing:2px;">{pioneer_badge}</p>
      <h1 style="margin:0;color:#000;font-size:26px;letter-spacing:-1px;">🚖 ZONE SAINT-DENIS</h1>
      <p style="margin:8px 0 0 0;color:#000;font-size:14px;font-weight:bold;">OUVERTURE OFFICIELLE — VENDREDI 13 JUIN 2026</p>
    </div>

    <div style="padding:36px 30px;">
      <h2 style="color:#FFD60A;font-size:22px;margin:0 0 18px 0;">Bonjour {name} 👋</h2>

      <p style="color:#e4e4e7;line-height:1.7;font-size:15px;margin:0 0 16px 0;">
        C'est officiel : <strong style="color:#FFD60A">vendredi 13 juin 2026</strong>, Métro-Taxi ouvre sa <strong>première zone pilote payante à Saint-Denis</strong> (93).
      </p>

      <p style="color:#e4e4e7;line-height:1.7;font-size:15px;margin:0 0 24px 0;">
        {pioneer_line}
      </p>

      <h3 style="color:#FFD60A;font-size:16px;margin:28px 0 12px 0;border-bottom:1px solid #27272a;padding-bottom:8px;">⚡ Ce qui va se passer le 13 juin</h3>
      <ul style="color:#cccccc;line-height:1.8;font-size:14px;margin:0 0 18px 0;padding-left:20px;">
        <li>Ouverture des <strong>abonnements usagers</strong> pour la zone Saint-Denis</li>
        <li>Les <strong style="color:#FFD60A">30 premiers abonnés</strong> recevront automatiquement une <strong>première course offerte (≤ 10 km)</strong></li>
        <li><strong>Toi</strong>, tu commences à recevoir des courses dès le premier abonné actif dans ta zone</li>
      </ul>

      <h3 style="color:#FFD60A;font-size:16px;margin:28px 0 12px 0;border-bottom:1px solid #27272a;padding-bottom:8px;">💰 Ton modèle (il ne change pas)</h3>
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;border-radius:8px;border-left:4px solid #FFD60A;margin:0 0 18px 0;">
        <tr><td style="padding:18px 20px;">
          <p style="color:#fff;margin:0 0 8px 0;font-size:14px;">✅ <strong>1,50 € / km parcouru</strong> avec au moins un abonné Métro-Taxi à bord</p>
          <p style="color:#fff;margin:0 0 8px 0;font-size:14px;">✅ <strong>0 % de commission</strong>, à vie</p>
          <p style="color:#fff;margin:0 0 8px 0;font-size:14px;">✅ <strong>Versement chaque 10 du mois</strong></p>
          <p style="color:#fff;margin:0;font-size:14px;">✅ <strong>Aucun engagement</strong> — tu continues Uber/Bolt en parallèle si tu veux</p>
        </td></tr>
      </table>
      <p style="color:#a1a1aa;font-size:13px;line-height:1.6;margin:0 0 24px 0;font-style:italic;">
        Le tarif fondateur t'est garanti à vie. Tu es entré dans le projet avant l'ouverture publique, ta place est gravée.
      </p>

      <h3 style="color:#FFD60A;font-size:16px;margin:28px 0 12px 0;border-bottom:1px solid #27272a;padding-bottom:8px;">🎯 3 actions à faire AVANT le 13 juin (5 min top chrono)</h3>
      <ol style="color:#cccccc;line-height:1.8;font-size:14px;margin:0 0 24px 0;padding-left:22px;">
        <li>Connecte-toi à l'app et vérifie que ton <strong>profil + RIB + immatriculation</strong> sont à jour</li>
        <li>Confirme ta <strong>disponibilité</strong> dans l'agenda chauffeur (créneaux Saint-Denis)</li>
        <li>Active les <strong>notifications push</strong> sur ton téléphone — c'est par là qu'arrivent les courses</li>
      </ol>

      <table width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;"><tr><td align="center">
        <a href="https://metro-taxi.com/driver/dashboard" style="display:inline-block;background:#FFD60A;color:#000;text-decoration:none;padding:16px 36px;border-radius:10px;font-weight:bold;font-size:15px;letter-spacing:0.3px;">
          VÉRIFIER MA FICHE CHAUFFEUR →
        </a>
      </td></tr></table>

      <hr style="border:none;border-top:1px solid #333;margin:28px 0;">

      <h3 style="color:#FFD60A;font-size:16px;margin:0 0 12px 0;">🤝 Un dernier mot</h3>
      <p style="color:#cccccc;line-height:1.7;font-size:14px;margin:0 0 14px 0;">
        Vous êtes 33. Vous êtes les fondations. Sans vous, Saint-Denis ne se lance pas le 13 juin — il se lance "un jour". C'est grâce à votre confiance qu'on a tenu le cap.
      </p>
      <p style="color:#fff;line-height:1.7;font-size:15px;margin:0 0 14px 0;">
        <strong>Merci.</strong> Vraiment.
      </p>
      <p style="color:#a1a1aa;font-size:13px;line-height:1.6;margin:0 0 20px 0;">
        Si tu as la moindre question, réponds directement à cet email ou écris-moi sur WhatsApp au <strong style="color:#FFD60A">06 05 78 64 25</strong> — je m'en occupe personnellement.
      </p>

      <p style="color:#FFD60A;font-size:15px;margin:24px 0 0 0;">
        Bonne route 🚖🇫🇷<br>
        <strong>— Judée, fondateur Métro-Taxi</strong>
      </p>
    </div>

    <div style="background:#09090b;padding:18px 24px;text-align:center;border-top:1px solid #27272a;">
      <p style="color:#52525b;margin:0 0 6px 0;font-size:12px;">© 2026 Métro-Taxi — Plateforme française de covoiturage à maillage intelligent</p>
      <p style="color:#52525b;margin:0;font-size:11px;">
        <a href="https://metro-taxi.com/saint-denis" style="color:#71717a;text-decoration:none;">metro-taxi.com/saint-denis</a>
      </p>
    </div>
  </div>
</body></html>
"""

    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": "🚖 Pionniers, c'est confirmé : ouverture zone Saint-Denis le 13 juin",
            "html": html_content,
            "reply_to": "judeemane@hotmail.com",
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Launch announcement email sent to {email} (#{pioneer_number}), ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send launch announcement email to {email}: {str(e)}")
        return False


# ============================================
# EMAIL PERSO ADMIN → CHAUFFEUR
# ============================================
async def send_admin_personal_email(to_email: str, recipient_name: str, subject: str, body: str, admin_name: str = "Métro-Taxi"):
    """
    Envoie un email personnalisé depuis l'admin vers un chauffeur (ou usager).
    Le `body` peut contenir des sauts de ligne — ils sont convertis en <br>.
    """
    if not RESEND_API_KEY:
        return False

    safe_body = (body or '').replace('\n', '<br>')
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"></head>
    <body style="font-family:Helvetica,Arial,sans-serif;background:#0a0a0a;margin:0;padding:30px 20px;color:#fff;">
      <div style="max-width:560px;margin:0 auto;background:#1a1a1a;border-radius:10px;overflow:hidden;border-top:4px solid #FFD60A;">
        <div style="background:#FFD60A;padding:18px 24px;">
          <h1 style="margin:0;color:#000;font-size:18px;">Métro-Taxi</h1>
        </div>
        <div style="padding:28px 26px;">
          <p style="color:#fff;font-size:15px;line-height:1.6;">Bonjour {recipient_name},</p>
          <div style="color:#cccccc;font-size:14px;line-height:1.7;margin:16px 0;">
            {safe_body}
          </div>
          <p style="color:#71717a;font-size:13px;margin:24px 0 0 0;">
            Cordialement,<br>
            <strong style="color:#FFD60A;">{admin_name}</strong><br>
            <span style="color:#52525b;font-size:11px;">Métro-Taxi</span>
          </p>
        </div>
        <div style="background:#09090b;padding:14px;text-align:center;">
          <p style="color:#52525b;margin:0;font-size:11px;">Cet email a été envoyé personnellement par l'équipe Métro-Taxi.</p>
        </div>
      </div>
    </body></html>
    """
    try:
        result = await asyncio.to_thread(resend.Emails.send, {
            "from": SENDER_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html,
        })
        logging.info(f"Admin personal email sent to {to_email} (subject: {subject}), ID: {result.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send admin personal email to {to_email}: {str(e)}")
        return False
