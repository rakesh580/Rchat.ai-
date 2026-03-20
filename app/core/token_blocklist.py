"""
JWT token blocklist for logout invalidation.
Uses database for persistence across restarts, with in-memory cache for performance.
"""
import threading
import time
import logging
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)

_cache: dict[str, float] = {}  # token -> expiry timestamp (in-memory cache)
_lock = threading.Lock()


def blocklist_token(token: str) -> None:
    """Add a token to the blocklist until it naturally expires."""
    payload = decode_access_token(token)
    if not payload or "exp" not in payload:
        return
    expiry = float(payload["exp"])

    # Add to in-memory cache
    with _lock:
        _cache[token] = expiry
        _cleanup_cache()

    # Persist to database (best effort)
    try:
        from app.db.postgres import execute
        execute(
            """INSERT INTO token_blocklist (token_hash, expires_at)
               VALUES (md5(%s), to_timestamp(%s))
               ON CONFLICT DO NOTHING""",
            (token, expiry),
        )
    except Exception as e:
        logger.warning("Failed to persist blocklisted token to DB: %s", e)


def is_token_blocklisted(token: str) -> bool:
    """Check if a token has been blocklisted (logged out)."""
    # Check in-memory cache first (fast path)
    with _lock:
        if token in _cache:
            return True

    # Check database (slow path — for tokens blocklisted by other processes or before restart)
    try:
        from app.db.postgres import query_one
        row = query_one(
            "SELECT 1 FROM token_blocklist WHERE token_hash = md5(%s) AND expires_at > NOW()",
            (token,),
        )
        if row:
            # Warm cache
            payload = decode_access_token(token)
            if payload and "exp" in payload:
                with _lock:
                    _cache[token] = float(payload["exp"])
            return True
    except Exception:
        pass  # Table may not exist yet; fall back to cache-only

    return False


def _cleanup_cache() -> None:
    """Remove expired tokens from the cache."""
    now = time.time()
    expired = [t for t, exp in _cache.items() if exp < now]
    for t in expired:
        del _cache[t]
