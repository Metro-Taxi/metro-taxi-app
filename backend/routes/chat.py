"""
Routes API pour le système de chat - Métro-Taxi
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid

from database import db
from models.schemas import ChatMessage, ChatMessageResponse
from services.auth import get_current_user

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat/send")
async def send_chat_message(message: ChatMessage, current_user: dict = Depends(get_current_user)):
    """Send a chat message in a ride"""
    user_id = current_user.get("user_id") or current_user.get("id")
    user_type = current_user.get("role", "user")

    ride = await db.rides.find_one({"id": message.ride_id}, {"_id": 0})
    if not ride:
        raise HTTPException(status_code=404, detail="Trajet non trouvé")

    if user_type == "user" and ride.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas associé à ce trajet")
    if user_type == "driver" and ride.get("driver_id") != user_id:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas le chauffeur de ce trajet")

    if user_type == "user":
        sender = await db.users.find_one({"id": user_id}, {"_id": 0, "first_name": 1, "last_name": 1})
    else:
        sender = await db.drivers.find_one({"id": user_id}, {"_id": 0, "first_name": 1, "last_name": 1})

    sender_name = f"{sender.get('first_name', '')} {sender.get('last_name', '')}" if sender else "Utilisateur"

    msg_doc = {
        "id": str(uuid.uuid4()),
        "ride_id": message.ride_id,
        "sender_id": user_id,
        "sender_type": user_type,
        "sender_name": sender_name.strip(),
        "content": message.content,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read": False
    }
    await db.chat_messages.insert_one(msg_doc)

    # Send via WebSocket if recipient is connected
    recipient_id = ride.get("driver_id") if user_type == "user" else ride.get("user_id")
    if recipient_id:
        try:
            from server import manager
            ws_message = {"type": "chat_message", "data": {k: v for k, v in msg_doc.items() if k != "_id"}}
            await manager.send_personal_message(ws_message, recipient_id)
        except ImportError:
            pass

    return {k: v for k, v in msg_doc.items() if k != "_id"}


@router.get("/chat/{ride_id}")
async def get_chat_messages(ride_id: str, current_user: dict = Depends(get_current_user), limit: int = 50):
    """Get chat messages for a ride"""
    user_id = current_user.get("user_id") or current_user.get("id")
    user_type = current_user.get("role", "user")

    ride = await db.rides.find_one({"id": ride_id}, {"_id": 0})
    if not ride:
        raise HTTPException(status_code=404, detail="Trajet non trouvé")
    if user_type == "user" and ride.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    if user_type == "driver" and ride.get("driver_id") != user_id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    messages = await db.chat_messages.find({"ride_id": ride_id}, {"_id": 0}).sort("created_at", 1).limit(limit).to_list(limit)

    await db.chat_messages.update_many(
        {"ride_id": ride_id, "sender_id": {"$ne": user_id}},
        {"$set": {"read": True}}
    )

    return {"messages": messages, "ride_id": ride_id}


@router.get("/chat/{ride_id}/unread")
async def get_unread_count(ride_id: str, current_user: dict = Depends(get_current_user)):
    """Get unread message count for a ride"""
    user_id = current_user.get("user_id") or current_user.get("id")
    count = await db.chat_messages.count_documents({"ride_id": ride_id, "sender_id": {"$ne": user_id}, "read": False})
    return {"unread_count": count}


@router.put("/chat/{ride_id}/read")
async def mark_chat_read(ride_id: str, current_user: dict = Depends(get_current_user)):
    """Mark all chat messages as read"""
    user_id = current_user.get("user_id") or current_user.get("id")
    result = await db.chat_messages.update_many(
        {"ride_id": ride_id, "sender_id": {"$ne": user_id}},
        {"$set": {"read": True}}
    )
    return {"success": True, "marked_read": result.modified_count}
