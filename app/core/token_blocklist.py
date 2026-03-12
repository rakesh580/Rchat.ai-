"""
In-memory JWT token blocklist for logout invalidation.
Tokens are stored with their expiry time and cleaned up periodically.
For production at scale, replace with Redis.
"""
import threading
import time
from app.core.security import decode_access_token

_blocklist: dict[str, float] = {}  # token -> expiry timestamp
_lock = threading.Lock()


def blocklist_token(token: str) -> None:
    """Add a token to the blocklist until it naturally expires."""
    payload = decode_access_token(token)
    if not payload or "exp" not in payload:
        return
    with _lock:
        _blocklist[token] = float(payload["exp"])
        _cleanup()


def is_token_blocklisted(token: str) -> bool:
    """Check if a token has been blocklisted (logged out)."""
    with _lock:
        return token in _blocklist


def _cleanup() -> None:
    """Remove expired tokens from the blocklist (they're invalid anyway)."""
    now = time.time()
    expired = [t for t, exp in _blocklist.items() if exp < now]
    for t in expired:
        del _blocklist[t]
