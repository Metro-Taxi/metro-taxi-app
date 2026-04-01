"""
Routes API pour les notifications push - Métro-Taxi
Gère : souscriptions, envoi de notifications, statut d'abonnement
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional
import os
import uuid
import json
import logging

try:
    from pywebpush import webpush, WebPushException
except ImportError:
    webpush = None
    WebPushException = Exception

# Imports locaux
from database import db
from models.schemas import PushSubscription, NotificationPayload
from services.auth import get_current_user

router = APIRouter(prefix="/api", tags=["notifications"])


# ============================================
# VAPID CONFIGURATION
# ============================================

@router.get("/notifications/vapid-public-key")
async def get_vapid_public_key():
    """Obtenir la clé publique VAPID pour l'inscription aux notifications"""
    vapid_public_key = os.environ.get("VAPID_PUBLIC_KEY", "")
    if not vapid_public_key:
        raise HTTPException(status_code=500, detail="VAPID keys not configured")
    return {"publicKey": vapid_public_key}


# ============================================
# SUBSCRIPTION MANAGEMENT
# ============================================

@router.post("/notifications/subscribe")
async def subscribe_push_notifications(subscription: PushSubscription, current_user: dict = Depends(get_current_user)):
    """S'abonner aux notifications push"""
    user_id = current_user.get("user_id") or current_user.get("id")
    user_type = current_user.get("role", "user")
    
    sub_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_type": user_type,
        "endpoint": subscription.endpoint,
        "keys": subscription.keys,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Upsert pour éviter les doublons
    await db.push_subscriptions.update_one(
        {"endpoint": subscription.endpoint},
        {"$set": sub_doc},
        upsert=True
    )
    
    return {"success": True, "message": "Subscription registered"}


@router.delete("/notifications/unsubscribe")
async def unsubscribe_push_notifications(endpoint: str, current_user: dict = Depends(get_current_user)):
    """Se désabonner des notifications push"""
    await db.push_subscriptions.delete_one({"endpoint": endpoint})
    return {"success": True, "message": "Subscription removed"}


# ============================================
# NOTIFICATION RETRIEVAL
# ============================================

@router.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user), limit: int = 20):
    """Obtenir les notifications de l'utilisateur"""
    user_id = current_user.get("user_id") or current_user.get("id")
    user_type = current_user.get("role", "user")
    
    notifications = await db.notifications.find(
        {"user_id": user_id, "user_type": user_type},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    unread_count = await db.notifications.count_documents(
        {"user_id": user_id, "user_type": user_type, "read": False}
    )
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Marquer une notification comme lue"""
    await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"read": True}}
    )
    return {"success": True}


@router.put("/notifications/read-all")
async def mark_all_notifications_read(current_user: dict = Depends(get_current_user)):
    """Marquer toutes les notifications comme lues"""
    user_id = current_user.get("user_id") or current_user.get("id")
    user_type = current_user.get("role", "user")
    
    await db.notifications.update_many(
        {"user_id": user_id, "user_type": user_type},
        {"$set": {"read": True}}
    )
    return {"success": True}


# ============================================
# SUBSCRIPTION STATUS
# ============================================

@router.get("/subscription/status")
async def get_subscription_status(current_user: dict = Depends(get_current_user)):
    """Obtenir le statut d'abonnement avec détails d'expiration"""
    user_id = current_user.get("user_id") or current_user.get("id")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    now = datetime.now(timezone.utc)
    subscription_active = user.get("subscription_active", False)
    subscription_expires = user.get("subscription_expires")
    
    hours_remaining = None
    expiring_soon = False
    expired = False
    
    if subscription_expires:
        try:
            expires_dt = datetime.fromisoformat(subscription_expires.replace('Z', '+00:00'))
            time_diff = expires_dt - now
            hours_remaining = max(0, time_diff.total_seconds() / 3600)
            
            if hours_remaining <= 0:
                expired = True
                subscription_active = False
            elif hours_remaining <= 48:
                expiring_soon = True
        except (ValueError, TypeError):
            pass
    
    return {
        "subscription_active": subscription_active,
        "subscription_expires": subscription_expires,
        "hours_remaining": round(hours_remaining, 1) if hours_remaining else None,
        "expiring_soon": expiring_soon,
        "expired": expired,
        "message": _get_status_message(subscription_active, expiring_soon, expired, hours_remaining)
    }


def _get_status_message(active: bool, expiring_soon: bool, expired: bool, hours: Optional[float]) -> str:
    """Générer le message de statut approprié"""
    if expired:
        return "Votre abonnement a expiré. Renouvelez-le pour continuer à utiliser Métro-Taxi."
    if expiring_soon and hours:
        return f"Votre abonnement expire dans {int(hours)} heures. Pensez à le renouveler."
    if active:
        return "Votre abonnement est actif."
    return "Aucun abonnement actif."


# ============================================
# HELPER FUNCTION - Envoi de notification
# ============================================

async def send_push_notification(user_id: str, notification: NotificationPayload, user_type: str = "user"):
    """Envoyer une notification push à un utilisateur spécifique"""
    subscriptions = await db.push_subscriptions.find(
        {"user_id": user_id, "user_type": user_type}
    ).to_list(10)
    
    # Stocker la notification pour récupération in-app
    notif_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_type": user_type,
        "title": notification.title,
        "body": notification.body,
        "data": notification.data,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notif_doc)
    
    if not webpush:
        return 0
    
    # Envoyer les vraies notifications push via WebPush
    vapid_private_key = os.environ.get("VAPID_PRIVATE_KEY")
    vapid_contact = os.environ.get("VAPID_CONTACT", "mailto:contact@metro-taxi.com")
    
    sent_count = 0
    for sub in subscriptions:
        try:
            subscription_info = {
                "endpoint": sub.get("endpoint"),
                "keys": sub.get("keys", {})
            }
            
            if vapid_private_key and subscription_info.get("endpoint") and subscription_info.get("keys", {}).get("p256dh"):
                payload = json.dumps({
                    "title": notification.title,
                    "body": notification.body,
                    "icon": "/icons/icon-192x192.png",
                    "badge": "/icons/icon-72x72.png",
                    "data": notification.data or {}
                })
                
                webpush(
                    subscription_info=subscription_info,
                    data=payload,
                    vapid_private_key=vapid_private_key,
                    vapid_claims={"sub": vapid_contact}
                )
                sent_count += 1
                logging.info(f"Push notification sent to user {user_id}")
        except WebPushException as e:
            logging.error(f"WebPush failed for user {user_id}: {e}")
            if hasattr(e, 'response') and e.response and e.response.status_code == 410:
                await db.push_subscriptions.delete_one({"endpoint": sub.get("endpoint")})
        except Exception as e:
            logging.error(f"Failed to send push notification: {e}")
    
    return sent_count
