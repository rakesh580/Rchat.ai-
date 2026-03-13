import socketio
import asyncio
from app.core.security import decode_access_token
from app.services.user_service import get_user_by_id
from app.db.postgres import execute, query
from datetime import datetime, timezone

from app.core.config import settings as app_settings

_cors_origins = [o.strip() for o in app_settings.CORS_ORIGINS.split(",") if o.strip()]

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=_cors_origins,
    max_http_buffer_size=1 * 1024 * 1024,  # 1MB max payload
    ping_timeout=20,
    ping_interval=25,
)

# Track connected users: user_id -> set of session IDs
connected_users: dict[str, set[str]] = {}


async def authenticate(token: str) -> dict | None:
    """Validate JWT and return user dict."""
    if token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1]

    # Check blocklist
    from app.core.token_blocklist import is_token_blocklisted
    if is_token_blocklisted(token):
        return None

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
        execute,
        "UPDATE users SET is_online = TRUE WHERE id = %s",
        (user_id,),
    )

    # Join all conversation rooms
    convos = await asyncio.to_thread(
        query,
        "SELECT conversation_id FROM conversation_participants WHERE user_id = %s",
        (user_id,),
    )
    for convo in convos:
        room = f"conv:{convo['conversation_id']}"
        await sio.enter_room(sid, room)

    # Broadcast online status
    await sio.emit("user:online", {"user_id": user_id})

    # Check if user has pending autopilot briefing (graceful if tables don't exist yet)
    try:
        from app.services.autopilot_service import has_unresolved_activity
        has_briefing = await asyncio.to_thread(has_unresolved_activity, user_id)
        if has_briefing:
            await sio.emit("autopilot:briefing_ready", {}, to=sid)
    except Exception:
        pass


@sio.event
async def disconnect(sid):
    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None

    if user_id and user_id in connected_users:
        connected_users[user_id].discard(sid)
        if not connected_users[user_id]:
            # No more connections for this user
            del connected_users[user_id]

            now = datetime.now(timezone.utc)
            await asyncio.to_thread(
                execute,
                "UPDATE users SET is_online = FALSE, last_seen = %s WHERE id = %s",
                (now, user_id),
            )
            await sio.emit("user:offline", {"user_id": user_id, "last_seen": now.isoformat()})
