"""
Routes API pour le chatbot de support IA - Métro-Taxi
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import os
import uuid
import logging
import asyncio

from emergentintegrations.llm.chat import LlmChat, UserMessage
from database import db

router = APIRouter(prefix="/api", tags=["support_chat"])

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

SYSTEM_PROMPT = """Tu es l'assistant virtuel de Métro-Taxi, le système de déplacement intelligent par covoiturage urbain par abonnement.

INFORMATIONS CLÉS SUR MÉTRO-TAXI :

1. CONCEPT :
- Métro-Taxi est un réseau de mobilité urbaine par abonnement
- Les usagers s'abonnent puis voyagent de façon illimitée
- Le système de transbordement intelligent permet de changer de véhicule en route pour atteindre sa destination
- C'est comme un métro, mais avec des véhicules privés

2. ABONNEMENTS ET TARIFS :
- Île-de-France : 24h = 6,99€ | 1 semaine = 16,99€ | 1 mois = 53,99€
- Madrid Zone A : 24h = 4,99€ | 1 semaine = 12,99€ | 1 mois = 34,99€
- Londres Zones 1-2 : 24h = £9.99 | 1 semaine = £29.99 | 1 mois = £79.99
- Londres Zones 1-4 : 24h = £12.99 | 1 semaine = £34.99 | 1 mois = £119.99
- Londres Zones 1-6 : 24h = £14.99 | 1 semaine = £39.99 | 1 mois = £149

3. COMMENT ÇA MARCHE :
- Étape 1 : S'inscrire et choisir un forfait
- Étape 2 : Localiser les véhicules disponibles sur la carte
- Étape 3 : Demander un trajet en un clic
- Étape 4 : Le chauffeur vous récupère et vous dépose
- Si besoin, le système calcule automatiquement des correspondances (transbordements)

4. POUR LES CHAUFFEURS :
- Inscription gratuite, aucune commission prélevée
- Revenus potentiels : 2 250€ - 3 000€/mois en Île-de-France
- Les chauffeurs utilisent la plateforme en toute indépendance
- Métro-Taxi agit exclusivement comme plateforme de mise en relation

5. PROBLÈMES COURANTS :
- Mot de passe oublié : aller sur la page de connexion, cliquer "Mot de passe oublié"
- Paiement échoué : vérifier la carte bancaire, réessayer ou contacter le support
- Application ne charge pas : vider le cache du navigateur, réessayer
- Abonnement expiré : se reconnecter et renouveler depuis la page Abonnements

6. CONTACT :
- Email : contact@metro-taxi.com
- Site web : metro-taxi.com

RÈGLES :
- Réponds TOUJOURS dans la langue utilisée par l'usager
- Sois poli, concis et utile
- Si tu ne peux pas résoudre le problème, propose d'envoyer un email à l'équipe support
- Ne donne JAMAIS d'informations fausses, dis que tu ne sais pas si c'est le cas
- Ne partage pas de détails techniques sur l'algorithme ou le code
"""


class SupportChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    language: str = Field(default="fr")


class SupportChatResponse(BaseModel):
    response: str
    session_id: str
    needs_escalation: bool = False


class EscalateRequest(BaseModel):
    session_id: str
    user_email: str
    user_name: str = ""
    subject: str = "Demande de support"


@router.post("/support/chat", response_model=SupportChatResponse)
async def support_chat(request: SupportChatRequest):
    """Handle support chatbot messages"""
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")

    session_id = request.session_id or str(uuid.uuid4())

    # Store user message in DB
    await db.support_messages.insert_one({
        "session_id": session_id,
        "role": "user",
        "content": request.message,
        "language": request.language
    })

    # Get conversation history
    history = await db.support_messages.find(
        {"session_id": session_id},
        {"_id": 0, "role": 1, "content": 1}
    ).sort("_id", 1).to_list(20)

    # Build system message with language instruction
    lang_instruction = {
        "fr": "Réponds en français.",
        "en": "Reply in English.",
        "en-GB": "Reply in British English.",
        "es": "Responde en español.",
        "de": "Antworte auf Deutsch.",
        "pt": "Responda em português.",
        "nl": "Antwoord in het Nederlands.",
        "no": "Svar på norsk.",
        "sv": "Svara på svenska.",
        "da": "Svar på dansk.",
        "zh": "用中文回复。",
        "hi": "हिन्दी में जवाब दें।",
        "pa": "ਪੰਜਾਬੀ ਵਿੱਚ ਜਵਾਬ ਦਿਓ।",
        "ar": "أجب بالعربية.",
        "ru": "Отвечай на русском.",
        "it": "Rispondi in italiano."
    }.get(request.language, "Réponds dans la langue de l'utilisateur.")

    system_msg = f"{SYSTEM_PROMPT}\n\nIMPORTANT: {lang_instruction}"

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"support-{session_id}",
            system_message=system_msg
        ).with_model("openai", "gpt-4.1-mini")

        # Send previous messages for context
        for msg in history[:-1]:
            if msg["role"] == "user":
                await chat.send_message(UserMessage(text=msg["content"]))

        # Send current message
        response_text = await chat.send_message(UserMessage(text=request.message))

        # Check if escalation is needed
        needs_escalation = any(keyword in response_text.lower() for keyword in [
            "contact@metro-taxi.com", "contacter l'équipe", "contact the team",
            "envoyer un email", "send an email", "escalade", "escalate"
        ])

        # Store assistant response
        await db.support_messages.insert_one({
            "session_id": session_id,
            "role": "assistant",
            "content": response_text,
            "language": request.language
        })

        return SupportChatResponse(
            response=response_text,
            session_id=session_id,
            needs_escalation=needs_escalation
        )

    except Exception as e:
        logging.error(f"Support chat error: {e}")
        fallback = {
            "fr": "Désolé, je rencontre un problème technique. Veuillez contacter contact@metro-taxi.com pour assistance.",
            "en": "Sorry, I'm experiencing a technical issue. Please contact contact@metro-taxi.com for assistance.",
            "es": "Lo siento, estoy experimentando un problema técnico. Contacte contact@metro-taxi.com para asistencia."
        }
        return SupportChatResponse(
            response=fallback.get(request.language[:2], fallback["fr"]),
            session_id=session_id,
            needs_escalation=True
        )


@router.post("/support/escalate")
async def escalate_to_email(request: EscalateRequest):
    """Escalate conversation to human support via email"""
    # Get conversation history
    messages = await db.support_messages.find(
        {"session_id": request.session_id},
        {"_id": 0, "role": 1, "content": 1}
    ).sort("_id", 1).to_list(50)

    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Build email body
    conversation_html = ""
    for msg in messages:
        role_label = "Usager" if msg["role"] == "user" else "Assistant IA"
        bg_color = "#27272a" if msg["role"] == "user" else "#18181b"
        conversation_html += f'<div style="background:{bg_color};padding:12px;border-radius:8px;margin:8px 0;"><strong style="color:#FFD60A">{role_label}:</strong><p style="color:#fff;margin:5px 0 0 0">{msg["content"]}</p></div>'

    html_content = f"""
    <html><body style="background:#0a0a0a;font-family:Arial,sans-serif;padding:20px;">
        <h2 style="color:#FFD60A;">Demande de support escaladée</h2>
        <p style="color:#a1a1aa;">De: {request.user_name} ({request.user_email})</p>
        <p style="color:#a1a1aa;">Sujet: {request.subject}</p>
        <hr style="border-color:#27272a;">
        <h3 style="color:#fff;">Historique de conversation:</h3>
        {conversation_html}
    </body></html>
    """

    try:
        import resend
        RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
        if RESEND_API_KEY:
            resend.api_key = RESEND_API_KEY
            params = {
                "from": SENDER_EMAIL,
                "to": ["contact@metro-taxi.com"],
                "reply_to": request.user_email,
                "subject": f"[Support Métro-Taxi] {request.subject}",
                "html": html_content
            }
            await asyncio.to_thread(resend.Emails.send, params)
            return {"success": True, "message": "Email envoyé à l'équipe support"}
        else:
            return {"success": False, "message": "Service email non configuré"}
    except Exception as e:
        logging.error(f"Escalation email error: {e}")
        return {"success": False, "message": "Erreur lors de l'envoi de l'email"}


@router.get("/support/history/{session_id}")
async def get_support_history(session_id: str):
    """Get conversation history for a session"""
    messages = await db.support_messages.find(
        {"session_id": session_id},
        {"_id": 0, "role": 1, "content": 1}
    ).sort("_id", 1).to_list(50)
    return {"messages": messages, "session_id": session_id}
