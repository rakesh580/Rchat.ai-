import socketio
import asyncio
from app.core.security import decode_access_token
from app.services.user_service import get_user_by_id
from app.db.mongo import users_collection, conversations_collection
from bson import ObjectId
from datetime import datetime

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
)

# Track connected users: user_id -> set of session IDs
connected_users: dict[str, set[str]] = {}


async def authenticate(token: str) -> dict | None:
    """Validate JWT and return user dict."""
    if token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1]

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = await asyncio.to_thread(get_user_by_id, user_id)
    return user


@sio.event
async def connect(sid, environ, auth):
    if not auth or "token" not in auth:
        raise socketio.exceptions.ConnectionRefusedError("No token provided")

    user = await authenticate(auth["token"])
    if not user:
        raise socketio.exceptions.ConnectionRefusedError("Invalid token")

    user_id = str(user["_id"])

    # Save user_id in session
    await sio.save_session(sid, {"user_id": user_id})

    # Track connection
    if user_id not in connected_users:
        connected_users[user_id] = set()
    connected_users[user_id].add(sid)

    # Set user online in DB
    await asyncio.to_thread(
        users_collection.update_one,
        {"_id": ObjectId(user_id)},
        {"$set": {"is_online": True}},
    )

    # Join all conversation rooms
    convos = await asyncio.to_thread(
        lambda: list(conversations_collection.find({"participants": user_id}))
    )
    for convo in convos:
        room = f"conv:{convo['_id']}"
        await sio.enter_room(sid, room)

    # Broadcast online status
    await sio.emit("user:online", {"user_id": user_id})


@sio.event
async def disconnect(sid):
    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None

    if user_id and user_id in connected_users:
        connected_users[user_id].discard(sid)
        if not connected_users[user_id]:
            # No more connections for this user
            del connected_users[user_id]

            now = datetime.utcnow()
            await asyncio.to_thread(
                users_collection.update_one,
                {"_id": ObjectId(user_id)},
                {"$set": {"is_online": False, "last_seen": now}},
            )
            await sio.emit("user:offline", {"user_id": user_id, "last_seen": now.isoformat()})
