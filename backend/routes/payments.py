"""
Routes API pour les paiements et abonnements - Métro-Taxi
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import Response
from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel
import os
import logging
import uuid
import stripe
import json

from database import db
from models.schemas import CheckoutRequest, CheckoutRequestWithRegion
from services.auth import get_current_user
from services.emails import send_subscription_confirmation_email
from routes.auto_campaigns import attempt_auto_attribution
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest


async def _activate_subscription_and_attribution(user_id: str, plan_id: str, expires_at: datetime):
    """Helper centralisé pour activer un abonnement ET tenter une auto-attribution
    promo si l'usager fait partie d'une campagne (Saint-Denis pionniers, etc.).

    Idempotent : si l'abonnement est déjà actif, ne fait rien de spécial.
    """
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "subscription_active": True,
            "subscription_expires": expires_at.isoformat(),
            "subscription_plan": plan_id,
        }},
    )
    # Tentative d'auto-attribution si signup_campaign est défini sur le profil
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "signup_campaign": 1})
    campaign_id = (user or {}).get("signup_campaign")
    if campaign_id:
        await attempt_auto_attribution(user_id, campaign_id)

# Config from environment
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY

# Import pricing config from server
from server import SUBSCRIPTION_PLANS, REGIONAL_PRICING, get_regional_pricing

router = APIRouter(prefix="/api", tags=["payments"])

# Subscription & Payment Routes
@router.get("/subscriptions/plans")
async def get_subscription_plans(region_id: Optional[str] = None):
    """Get subscription plans, optionally filtered by region"""
    if region_id and region_id in REGIONAL_PRICING:
        regional = REGIONAL_PRICING[region_id]
        plans_with_duration = {}
        for plan_id, plan_data in regional["plans"].items():
            plans_with_duration[plan_id] = {
                **plan_data,
                "duration_hours": SUBSCRIPTION_PLANS[plan_id]["duration_hours"],
                "currency": regional["currency"],
                "currency_symbol": regional["currency_symbol"]
            }
        return {
            "plans": plans_with_duration,
            "region_id": region_id,
            "currency": regional["currency"],
            "driver_rate_per_km": regional["driver_rate_per_km"]
        }
    return {"plans": SUBSCRIPTION_PLANS, "currency": "EUR", "currency_symbol": "€"}

@router.get("/subscriptions/plans/region/{region_id}")
async def get_subscription_plans_for_region(region_id: str):
    """Get subscription plans for a specific region"""
    if region_id not in REGIONAL_PRICING:
        # Fallback to default pricing
        region_id = "paris"
    
    regional = REGIONAL_PRICING[region_id]
    plans_with_duration = {}
    for plan_id, plan_data in regional["plans"].items():
        plans_with_duration[plan_id] = {
            **plan_data,
            "duration_hours": SUBSCRIPTION_PLANS[plan_id]["duration_hours"],
            "currency": regional["currency"],
            "currency_symbol": regional["currency_symbol"]
        }
    
    return {
        "plans": plans_with_duration,
        "region_id": region_id,
        "currency": regional["currency"],
        "currency_symbol": regional["currency_symbol"],
        "driver_rate_per_km": regional["driver_rate_per_km"]
    }

@router.get("/pricing/regions")
async def get_all_regional_pricing():
    """Get pricing for all regions (admin view)"""
    return {
        "pricing": REGIONAL_PRICING,
        "default_plans": SUBSCRIPTION_PLANS
    }

@router.post("/payments/checkout")
async def create_checkout(data: CheckoutRequest, request: Request, current_user: dict = Depends(get_current_user)):
    if data.plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Plan invalide")
    
    plan = SUBSCRIPTION_PLANS[data.plan_id]
    user_id = current_user["user_id"]
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_key = os.environ.get('STRIPE_API_KEY')
    
    stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url=webhook_url)
    
    success_url = f"{data.origin_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{data.origin_url}/subscription"
    
    checkout_request = CheckoutSessionRequest(
        amount=plan["price_cents"] / 100,  # Convert cents to euros for the API
        currency="eur",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": user_id, "plan_id": data.plan_id}
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    transaction = {
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "user_id": user_id,
        "plan_id": data.plan_id,
        "amount": plan["price"],
        "currency": "eur",
        "status": "pending",
        "payment_status": "initiated",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction)
    
    return {"url": session.url, "session_id": session.session_id}

# NEW: Multi-region subscription checkout
@router.post("/payments/checkout/region")
async def create_checkout_with_region(data: CheckoutRequestWithRegion, request: Request, current_user: dict = Depends(get_current_user)):
    """Create checkout session for a specific region"""
    if data.plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Plan invalide")
    
    # Verify region exists and is active
    region = await db.regions.find_one({"id": data.region_id, "is_active": True})
    if not region:
        raise HTTPException(status_code=400, detail="Région non disponible")
    
    plan = SUBSCRIPTION_PLANS[data.plan_id]
    user_id = current_user["user_id"]
    
    # ==========================================
    # PROTECTION DOUBLE PAIEMENT (A)
    # Vérifier si l'utilisateur a déjà un abonnement actif pour cette région
    # Permet le renouvellement si l'abonnement expire dans moins de 48h
    # ==========================================
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user:
        existing_subs = user.get("subscriptions", [])
        now = datetime.now(timezone.utc)
        for sub in existing_subs:
            if sub.get("region_id") == data.region_id:
                try:
                    expires_str = sub.get("expires_at", "")
                    expires = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                    hours_remaining = (expires - now).total_seconds() / 3600
                    
                    # Permettre le renouvellement si expire dans moins de 48h
                    if expires > now and hours_remaining > 48:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Vous avez déjà un abonnement actif pour cette région (expire dans {round(hours_remaining)}h). Connectez-vous sur vos autres appareils avec le même email pour y accéder."
                        )
                except (ValueError, TypeError):
                    pass
    
    # Get currency from region (default EUR)
    currency = region.get("currency", "EUR").lower()
    
    stripe_key = os.environ.get('STRIPE_API_KEY')
    stripe.api_key = stripe_key
    
    success_url = f"{data.origin_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}&region={data.region_id}"
    cancel_url = f"{data.origin_url}/subscription?region={data.region_id}"
    
    try:
        # Use Stripe API directly for precise amount handling (in cents)
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': currency,
                    'unit_amount': plan["price_cents"],  # Amount in cents (integer)
                    'product_data': {
                        'name': f"Métro-Taxi - {plan['name']}",
                        'description': f"Abonnement {plan['name']} - {region.get('name', data.region_id)}"
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": user_id, 
                "plan_id": data.plan_id,
                "region_id": data.region_id
            }
        )
        
        # Create payment transaction record with region
        transaction = {
            "id": str(uuid.uuid4()),
            "session_id": session.id,
            "user_id": user_id,
            "plan_id": data.plan_id,
            "region_id": data.region_id,
            "amount": plan["price"],
            "currency": currency,
            "status": "pending",
            "payment_status": "initiated",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.payment_transactions.insert_one(transaction)
        
        # Remove _id from region before returning
        region_response = {k: v for k, v in region.items() if k != "_id"}
        
        return {"url": session.url, "session_id": session.id, "region": region_response}
    
    except stripe.error.StripeError as e:
        logging.error(f"Stripe checkout error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# SEPA Direct Debit Payment Model
class SepaCheckoutRequest(BaseModel):
    plan_id: str
    region_id: str
    iban: str
    account_holder_name: str
    email: str
    origin_url: str

@router.post("/payments/checkout/sepa")
async def create_sepa_checkout(data: SepaCheckoutRequest, request: Request, current_user: dict = Depends(get_current_user)):
    """Create SEPA Direct Debit payment for subscription - Lower fees (0.35€ flat)"""
    if data.plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Plan invalide")
    
    # Verify region exists and is active
    region = await db.regions.find_one({"id": data.region_id, "is_active": True})
    if not region:
        raise HTTPException(status_code=400, detail="Région non disponible")
    
    plan = SUBSCRIPTION_PLANS[data.plan_id]
    user_id = current_user["user_id"]
    
    # ==========================================
    # PROTECTION DOUBLE PAIEMENT (A)
    # Vérifier si l'utilisateur a déjà un abonnement actif pour cette région
    # Permet le renouvellement si l'abonnement expire dans moins de 48h
    # ==========================================
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user:
        existing_subs = user.get("subscriptions", [])
        now = datetime.now(timezone.utc)
        for sub in existing_subs:
            if sub.get("region_id") == data.region_id:
                try:
                    expires_str = sub.get("expires_at", "")
                    expires = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                    hours_remaining = (expires - now).total_seconds() / 3600
                    
                    # Permettre le renouvellement si expire dans moins de 48h
                    if expires > now and hours_remaining > 48:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Vous avez déjà un abonnement actif pour cette région (expire dans {round(hours_remaining)}h). Connectez-vous sur vos autres appareils avec le même email pour y accéder."
                        )
                except (ValueError, TypeError):
                    pass
    
    stripe_key = os.environ.get('STRIPE_API_KEY')
    stripe.api_key = stripe_key
    
    try:
        # Create a PaymentIntent with SEPA Direct Debit
        payment_intent = stripe.PaymentIntent.create(
            amount=plan["price_cents"],
            currency="eur",
            payment_method_types=["sepa_debit"],
            payment_method_data={
                "type": "sepa_debit",
                "sepa_debit": {"iban": data.iban},
                "billing_details": {
                    "name": data.account_holder_name,
                    "email": data.email
                }
            },
            confirm=True,
            mandate_data={
                "customer_acceptance": {
                    "type": "online",
                    "online": {
                        "ip_address": request.client.host,
                        "user_agent": request.headers.get("user-agent", "")
                    }
                }
            },
            metadata={
                "user_id": user_id,
                "plan_id": data.plan_id,
                "region_id": data.region_id,
                "payment_method": "sepa"
            },
            return_url=f"{data.origin_url}/subscription/success?payment_intent={{PAYMENT_INTENT_ID}}&region={data.region_id}"
        )
        
        # Create payment transaction record
        transaction = {
            "id": str(uuid.uuid4()),
            "payment_intent_id": payment_intent.id,
            "user_id": user_id,
            "plan_id": data.plan_id,
            "region_id": data.region_id,
            "amount": plan["price"],
            "currency": "eur",
            "payment_method": "sepa",
            "status": "pending",
            "payment_status": payment_intent.status,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.payment_transactions.insert_one(transaction)
        
        logging.info(f"SEPA PaymentIntent created: {payment_intent.id} - Status: {payment_intent.status}")
        
        # SEPA can be processing, succeeded, or requires_action
        if payment_intent.status == "succeeded":
            # Immediate success (rare for SEPA)
            return {
                "status": "succeeded",
                "payment_intent_id": payment_intent.id,
                "message": "Paiement SEPA réussi"
            }
        elif payment_intent.status == "processing":
            # Normal for SEPA - payment is being processed
            return {
                "status": "processing",
                "payment_intent_id": payment_intent.id,
                "message": "Paiement SEPA en cours de traitement. Vous recevrez une confirmation par email sous 5-14 jours ouvrés."
            }
        elif payment_intent.status == "requires_action":
            return {
                "status": "requires_action",
                "payment_intent_id": payment_intent.id,
                "next_action": payment_intent.next_action,
                "message": "Action supplémentaire requise"
            }
        else:
            return {
                "status": payment_intent.status,
                "payment_intent_id": payment_intent.id
            }
            
    except stripe.error.CardError as e:
        logging.error(f"SEPA error: {e.user_message}")
        raise HTTPException(status_code=400, detail=e.user_message)
    except stripe.error.InvalidRequestError as e:
        logging.error(f"SEPA invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail="IBAN invalide ou données incorrectes")
    except Exception as e:
        logging.error(f"SEPA payment error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors du traitement du paiement SEPA")

@router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    """Check payment status using Stripe API directly to avoid emergentintegrations bug"""
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Stripe API key not configured")
    
    try:
        # Use Stripe API directly instead of emergentintegrations (bug with metadata validation)
        stripe.api_key = stripe_key
        session = stripe.checkout.Session.retrieve(session_id)
        
        payment_status = session.payment_status or "unpaid"
        status = session.status or "open"
        amount_total = session.amount_total or 0
        currency = session.currency or "eur"
        
        # Update transaction and subscription if paid
        if payment_status == "paid":
            transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
            if transaction and transaction.get("payment_status") != "paid":
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {"status": "completed", "payment_status": "paid"}}
                )
                
                # Activate subscription
                plan = SUBSCRIPTION_PLANS.get(transaction["plan_id"])
                if plan:
                    expires_at = datetime.now(timezone.utc) + timedelta(hours=plan["duration_hours"])
                    await _activate_subscription_and_attribution(
                        transaction["user_id"], transaction["plan_id"], expires_at
                    )
                    logging.info(f"✅ Subscription activated for user {transaction['user_id']} via status check")
        
        return {
            "status": status,
            "payment_status": payment_status,
            "amount_total": amount_total,
            "currency": currency
        }
    except stripe.error.StripeError as e:
        logging.error(f"Stripe error checking payment status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur Stripe: {str(e)}")
    except Exception as e:
        logging.error(f"Error checking payment status: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la vérification du paiement")

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    stripe_key = os.environ.get('STRIPE_API_KEY')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    stripe.api_key = stripe_key
    
    try:
        event = stripe.Webhook.construct_event(body, signature, webhook_secret)
        logging.info(f"Webhook received: type={event['type']}")
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            session_id = session['id']
            payment_status = session.get('payment_status', '')
            
            logging.info(f"Checkout completed: session_id={session_id}, payment_status={payment_status}")
            
            if payment_status == "paid":
                transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
                
                if transaction:
                    await db.payment_transactions.update_one(
                        {"session_id": session_id},
                        {"$set": {"status": "completed", "payment_status": "paid"}}
                    )
                    
                    plan = SUBSCRIPTION_PLANS.get(transaction["plan_id"])
                    if plan:
                        now = datetime.now(timezone.utc)
                        region_id = transaction.get("region_id")
                        user_id = transaction.get("user_id")
                        
                        user = await db.users.find_one({"id": user_id})
                        
                        if region_id and user:
                            # Check if user has an existing active subscription for this region
                            existing_subs = user.get("subscriptions", [])
                            base_date = now  # Default: start from now
                            
                            for sub in existing_subs:
                                if sub.get("region_id") == region_id:
                                    try:
                                        existing_expires = datetime.fromisoformat(sub.get("expires_at", "").replace('Z', '+00:00'))
                                        # If subscription is still active, chain the new one after it
                                        if existing_expires > now:
                                            base_date = existing_expires
                                            logging.info(f"Chaining subscription: new period starts at {base_date.isoformat()}")
                                    except (ValueError, TypeError):
                                        pass
                                    break
                            
                            # Calculate expiration from base_date (either now or end of current subscription)
                            expires_at = base_date + timedelta(hours=plan["duration_hours"])
                            
                            # Multi-region subscription
                            new_subscription = {
                                "region_id": region_id,
                                "plan_id": transaction["plan_id"],
                                "expires_at": expires_at.isoformat(),
                                "is_active": True,
                                "payment_method": "card",
                                "created_at": now.isoformat()
                            }
                            
                            updated = False
                            for i, sub in enumerate(existing_subs):
                                if sub.get("region_id") == region_id:
                                    existing_subs[i] = new_subscription
                                    updated = True
                                    break
                            
                            if not updated:
                                existing_subs.append(new_subscription)
                        
                        await db.users.update_one(
                            {"id": transaction["user_id"]},
                            {"$set": {
                                "subscriptions": existing_subs,
                                # Keep legacy fields for backward compatibility
                                "subscription_active": True,
                                "subscription_expires": expires_at.isoformat(),
                                "subscription_plan": transaction["plan_id"]
                            }}
                        )
                        # Auto-attribution promo si l'usager fait partie d'une campagne Saint-Denis & co.
                        u_camp = await db.users.find_one({"id": transaction["user_id"]}, {"_id": 0, "signup_campaign": 1})
                        if u_camp and u_camp.get("signup_campaign"):
                            await attempt_auto_attribution(transaction["user_id"], u_camp["signup_campaign"])
                        else:
                            # Fallback : auto-attribution par région
                            from routes.auto_campaigns import auto_attribute_for_region
                            await auto_attribute_for_region(transaction["user_id"], region_id)
                        logging.info(f"✅ Subscription activated for user {transaction['user_id']} in region {region_id}")
                        
                        # Send confirmation email
                        if user:
                            region = await db.regions.find_one({"id": region_id}, {"_id": 0})
                            region_name = region.get("name", region_id) if region else region_id
                            plan_display = f"{plan['name']} - {region_name}"
                            expires_str = expires_at.strftime("%d/%m/%Y à %H:%M")
                            user_lang = region.get("language", "fr") if region else "fr"
                            await send_subscription_confirmation_email(
                                user.get("email"),
                                user.get("first_name", ""),
                                plan_display,
                                expires_str,
                                user_lang
                            )
                    else:
                        # Legacy single-region subscription
                        await _activate_subscription_and_attribution(
                            transaction["user_id"], transaction["plan_id"], expires_at
                        )
                        
                        # Send confirmation email for legacy subscription
                        user = await db.users.find_one({"id": transaction["user_id"]})
                        if user:
                            expires_str = expires_at.strftime("%d/%m/%Y à %H:%M")
                            await send_subscription_confirmation_email(
                                user.get("email"),
                                user.get("first_name", ""),
                                plan["name"],
                                expires_str,
                                "fr"
                            )
        
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return {"status": "error"}

@router.post("/webhook/stripe/sepa")
async def stripe_sepa_webhook(request: Request):
    """Handle SEPA payment webhooks separately"""
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    stripe_key = os.environ.get('STRIPE_API_KEY')
    stripe.api_key = stripe_key
    
    try:
        event = stripe.Webhook.construct_event(body, signature, webhook_secret)
        logging.info(f"SEPA Webhook event: {event['type']}")
        
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            payment_intent_id = payment_intent['id']
            metadata = payment_intent.get('metadata', {})
            
            # Check if this is a SEPA payment
            if metadata.get('payment_method') == 'sepa':
                transaction = await db.payment_transactions.find_one(
                    {"payment_intent_id": payment_intent_id}, 
                    {"_id": 0}
                )
                
                if transaction:
                    await db.payment_transactions.update_one(
                        {"payment_intent_id": payment_intent_id},
                        {"$set": {"status": "completed", "payment_status": "succeeded"}}
                    )
                    
                    plan = SUBSCRIPTION_PLANS.get(transaction["plan_id"])
                    if plan:
                        now = datetime.now(timezone.utc)
                        region_id = transaction.get("region_id")
                        user_id = transaction.get("user_id")
                        
                        user = await db.users.find_one({"id": user_id})
                        
                        if region_id and user:
                            # Check if user has an existing active subscription for this region
                            existing_subs = user.get("subscriptions", [])
                            base_date = now  # Default: start from now
                            
                            for sub in existing_subs:
                                if sub.get("region_id") == region_id:
                                    try:
                                        existing_expires = datetime.fromisoformat(sub.get("expires_at", "").replace('Z', '+00:00'))
                                        # If subscription is still active, chain the new one after it
                                        if existing_expires > now:
                                            base_date = existing_expires
                                            logging.info(f"SEPA: Chaining subscription: new period starts at {base_date.isoformat()}")
                                    except (ValueError, TypeError):
                                        pass
                                    break
                            
                            # Calculate expiration from base_date
                            expires_at = base_date + timedelta(hours=plan["duration_hours"])
                            
                            # Multi-region subscription
                            new_subscription = {
                                "region_id": region_id,
                                "plan_id": transaction["plan_id"],
                                "expires_at": expires_at.isoformat(),
                                "is_active": True,
                                "payment_method": "sepa",
                                "created_at": now.isoformat()
                            }
                            
                            updated = False
                            for i, sub in enumerate(existing_subs):
                                if sub.get("region_id") == region_id:
                                    existing_subs[i] = new_subscription
                                    updated = True
                                    break
                            
                            if not updated:
                                existing_subs.append(new_subscription)
                            
                            await db.users.update_one(
                                {"id": user_id},
                                {"$set": {
                                    "subscriptions": existing_subs,
                                    "subscription_active": True,
                                    "subscription_expires": expires_at.isoformat(),
                                    "subscription_plan": transaction["plan_id"]
                                }}
                            )
                            # Auto-attribution promo si l'usager fait partie d'une campagne
                            u_camp = await db.users.find_one({"id": user_id}, {"_id": 0, "signup_campaign": 1})
                            if u_camp and u_camp.get("signup_campaign"):
                                await attempt_auto_attribution(user_id, u_camp["signup_campaign"])
                            else:
                                # Fallback : auto-attribution par région
                                from routes.auto_campaigns import auto_attribute_for_region
                                await auto_attribute_for_region(user_id, region_id)
                            
                            logging.info(f"✅ SEPA Subscription activated for user {user_id} in region {region_id}")
                            
                            # Send confirmation email
                            region = await db.regions.find_one({"id": region_id}, {"_id": 0})
                            region_name = region.get("name", region_id) if region else region_id
                            plan_display = f"{plan['name']} - {region_name} (SEPA)"
                            expires_str = expires_at.strftime("%d/%m/%Y à %H:%M")
                            user_lang = region.get("language", "fr") if region else "fr"
                            
                            await send_subscription_confirmation_email(
                                user.get("email"),
                                user.get("first_name", ""),
                                plan_display,
                                expires_str,
                                user_lang
                            )
        
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            payment_intent_id = payment_intent['id']
            
            await db.payment_transactions.update_one(
                {"payment_intent_id": payment_intent_id},
                {"$set": {"status": "failed", "payment_status": "failed"}}
            )
            logging.warning(f"SEPA payment failed: {payment_intent_id}")
        
        return {"status": "ok"}
    except stripe.error.SignatureVerificationError as e:
        logging.error(f"SEPA Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logging.error(f"SEPA Webhook error: {e}")
        return {"status": "error"}

