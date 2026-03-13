import asyncio
import logging
import time
from collections import defaultdict
from app.sockets.server import sio, connected_users

logger = logging.getLogger(__name__)
from app.services.message_service import save_message, mark_messages_read
from app.services.conversation_service import get_conversation_by_id
from app.db.init_db import AI_BOT_ID

BOT_USER_ID = str(AI_BOT_ID)

MAX_MESSAGE_LENGTH = 5000

# Per-user socket rate limiting: max 30 messages per 60 seconds
_MSG_RATE_LIMIT = 30
_MSG_RATE_WINDOW = 60
_msg_timestamps: dict[str, list[float]] = defaultdict(list)


def _is_rate_limited(user_id: str) -> bool:
    """Check if a user has exceeded the socket message rate limit."""
    now = time.time()
    window_start = now - _MSG_RATE_WINDOW
    # Clean old entries
    _msg_timestamps[user_id] = [t for t in _msg_timestamps[user_id] if t > window_start]
    if len(_msg_timestamps[user_id]) >= _MSG_RATE_LIMIT:
        return True
    _msg_timestamps[user_id].append(now)
    return False


@sio.event
async def message_send(sid, data):
    """Client sends a message. Save it, broadcast to room, trigger AI if needed."""
    if not isinstance(data, dict):
        return

    session = await sio.get_session(sid)
    user_id = session.get("user_id")
    if not user_id:
        return

    # Socket-level rate limiting
    if _is_rate_limited(user_id):
        await sio.emit("error", {"detail": "Rate limit exceeded. Slow down."}, to=sid)
        return

    conversation_id = data.get("conversation_id")
    content = data.get("content", "")
    temp_id = data.get("temp_id")

    if not isinstance(conversation_id, str) or not isinstance(content, str):
        return

    content = content.strip()[:MAX_MESSAGE_LENGTH]
    if not conversation_id or not content:
        return

    # Verify user is a participant
    convo = await asyncio.to_thread(get_conversation_by_id, conversation_id)
    if not convo or user_id not in convo["participants"]:
        return

    # Save message to MongoDB
    msg = await asyncio.to_thread(save_message, conversation_id, user_id, content)

    # Confirm to sender
    await sio.emit("message:sent", {
        "temp_id": temp_id,
        "message_id": msg["_id"],
        "created_at": msg["created_at"].isoformat(),
    }, to=sid)

    # Broadcast to room
    room = f"conv:{conversation_id}"
    msg_payload = {
        "_id": msg["_id"],
        "conversation_id": msg["conversation_id"],
        "sender_id": msg["sender_id"],
        "content": msg["content"],
        "message_type": msg["message_type"],
        "status": msg["status"],
        "read_by": msg["read_by"],
        "created_at": msg["created_at"].isoformat(),
    }
    await sio.emit("message:new", msg_payload, room=room, skip_sid=sid)

    # Check autopilot for participants (skip auto-reply messages to prevent loops)
    if not content.startswith("[Auto-reply via Autopilot]") and not content.startswith("[Forwarded - Urgent]"):
        try:
            await handle_autopilot_check(conversation_id, user_id, msg, room, convo)
        except Exception:
            pass  # Graceful if autopilot tables don't exist yet

    # Check if conversation involves the AI bot
    if BOT_USER_ID in convo["participants"]:
        await handle_ai_response(conversation_id, content, user_id, room)


async def handle_ai_response(conversation_id: str, user_content: str, user_id: str, room: str):
    """Generate AI response and emit to room."""
    # Emit typing indicator
    await sio.emit("ai:typing", {"conversation_id": conversation_id}, room=room)

    try:
        from app.services.ai_service import get_ai_reply
        ai_msg = await asyncio.to_thread(get_ai_reply, conversation_id, user_content)

        ai_payload = {
            "_id": ai_msg["_id"],
            "conversation_id": ai_msg["conversation_id"],
            "sender_id": ai_msg["sender_id"],
            "content": ai_msg["content"],
            "message_type": ai_msg["message_type"],
            "status": ai_msg["status"],
            "read_by": ai_msg["read_by"],
            "created_at": ai_msg["created_at"].isoformat(),
        }
        await sio.emit("message:new", ai_payload, room=room)
    except Exception as exc:
        logger.error("AI response failed for conversation %s: %s", conversation_id, exc)
        await sio.emit("message:new", {
            "_id": "",
            "conversation_id": conversation_id,
            "sender_id": BOT_USER_ID,
            "content": "Sorry, I'm having trouble responding right now. Please try again later.",
            "message_type": "text",
            "status": "sent",
            "read_by": [],
            "created_at": "",
        }, room=room)


async def handle_autopilot_check(conversation_id: str, sender_id: str, msg: dict, room: str, convo: dict):
    """Check if any recipient has autopilot enabled and process accordingly."""
    from app.services.autopilot_service import (
        is_user_on_autopilot, get_autopilot_config, classify_message,
        log_activity, forward_to_backup,
    )

    for participant_id in convo["participants"]:
        if participant_id == sender_id:
            continue

        is_on = await asyncio.to_thread(is_user_on_autopilot, participant_id)
        if not is_on:
            continue

        config = await asyncio.to_thread(get_autopilot_config, participant_id)
        if not config:
            continue

        try:
            classification = await asyncio.to_thread(
                classify_message, conversation_id, sender_id, msg["content"], participant_id
            )

            category = classification["category"]
            action_taken = "logged"

            # Urgent: forward to backup person
            if category == "urgent" and config.get("backup_person_id"):
                await asyncio.to_thread(
                    forward_to_backup,
                    participant_id,
                    config["backup_person_id"],
                    sender_id,
                    conversation_id,
                    msg["content"],
                )
                action_taken = "forwarded"
                backup_id = config["backup_person_id"]
                if backup_id in connected_users:
                    for backup_sid in connected_users[backup_id]:
                        await sio.emit("autopilot:forwarded", {
                            "original_sender_id": sender_id,
                            "content": msg["content"],
                            "conversation_id": conversation_id,
                        }, to=backup_sid)

            # Auto-respond if enabled
            if (classification.get("should_auto_respond")
                    and config.get("auto_respond_enabled")
                    and classification.get("auto_response")):
                auto_content = f"[Auto-reply via Autopilot] {classification['auto_response']}"
                auto_msg = await asyncio.to_thread(
                    save_message, conversation_id, participant_id, auto_content
                )
                auto_payload = {
                    "_id": auto_msg["_id"],
                    "conversation_id": auto_msg["conversation_id"],
                    "sender_id": auto_msg["sender_id"],
                    "content": auto_msg["content"],
                    "message_type": auto_msg["message_type"],
                    "status": auto_msg["status"],
                    "read_by": auto_msg["read_by"],
                    "created_at": auto_msg["created_at"].isoformat(),
                    "is_autopilot_reply": True,
                }
                await sio.emit("message:new", auto_payload, room=room)
                action_taken = "auto_responded"
            elif category == "action_needed":
                action_taken = "queued"

            # Log activity
            await asyncio.to_thread(
                log_activity,
                participant_id, conversation_id, msg["_id"], sender_id,
                category, action_taken,
                classification.get("auto_response"),
                classification.get("deadline"),
            )

        except Exception as exc:
            logger.error("Autopilot processing failed for user %s: %s", participant_id, exc)


@sio.event
async def message_delivered(sid, data):
    """Client acknowledges message delivery."""
    if not isinstance(data, dict):
        return

    session = await sio.get_session(sid)
    user_id = session.get("user_id")
    if not user_id:
        return

    message_id = data.get("message_id")
    conversation_id = data.get("conversation_id")
    if not isinstance(message_id, str) or not isinstance(conversation_id, str):
        return
    if not message_id or not conversation_id:
        return

    # Notify sender
    room = f"conv:{conversation_id}"
    await sio.emit("message:status", {
        "message_id": message_id,
        "status": "delivered",
    }, room=room, skip_sid=sid)


@sio.event
async def message_read(sid, data):
    """Client marks all messages in a conversation as read."""
    if not isinstance(data, dict):
        return

    session = await sio.get_session(sid)
    user_id = session.get("user_id")
    if not user_id:
        return

    conversation_id = data.get("conversation_id")
    if not isinstance(conversation_id, str) or not conversation_id:
        return

    await asyncio.to_thread(mark_messages_read, conversation_id, user_id)

    room = f"conv:{conversation_id}"
    await sio.emit("message:read_receipt", {
        "conversation_id": conversation_id,
        "reader_id": user_id,
    }, room=room, skip_sid=sid)


@sio.event
async def group_created(sid, data):
    """After creating a group, notify members so it appears in their sidebar."""
    if not isinstance(data, dict):
        return

    session = await sio.get_session(sid)
    user_id = session.get("user_id")
    if not user_id:
        return

    conversation_id = data.get("conversation_id")
    if not isinstance(conversation_id, str) or not conversation_id:
        return

    convo = await asyncio.to_thread(get_conversation_by_id, conversation_id)
    if not convo or convo["type"] != "group":
        return

    # Add all connected participants to the room
    room = f"conv:{conversation_id}"
    for pid in convo["participants"]:
        if pid in connected_users:
            for member_sid in connected_users[pid]:
                await sio.enter_room(member_sid, room)

    # Notify room about the new group
    await sio.emit("conversation:new", {"conversation_id": conversation_id}, room=room)


@sio.event
async def typing_start(sid, data):
    """User started typing."""
    if not isinstance(data, dict):
        return

    session = await sio.get_session(sid)
    user_id = session.get("user_id")
    if not user_id:
        return

    conversation_id = data.get("conversation_id")
    if not isinstance(conversation_id, str) or not conversation_id:
        return

    room = f"conv:{conversation_id}"
    await sio.emit("typing:indicator", {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "is_typing": True,
    }, room=room, skip_sid=sid)


@sio.event
async def typing_stop(sid, data):
    """User stopped typing."""
    if not isinstance(data, dict):
        return

    session = await sio.get_session(sid)
    user_id = session.get("user_id")
    if not user_id:
        return

    conversation_id = data.get("conversation_id")
    if not isinstance(conversation_id, str) or not conversation_id:
        return

    room = f"conv:{conversation_id}"
    await sio.emit("typing:indicator", {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "is_typing": False,
    }, room=room, skip_sid=sid)
