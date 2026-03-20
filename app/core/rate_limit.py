import os
from slowapi import Limiter
from starlette.requests import Request


# Only trust proxy headers when explicitly configured (e.g., behind nginx/HF Spaces)
_TRUST_PROXY = os.getenv("TRUST_PROXY", "").lower() in ("1", "true", "yes")


def get_real_ip(request: Request) -> str:
    """Extract client IP — only trusts proxy headers when TRUST_PROXY is set."""
    if _TRUST_PROXY:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the rightmost IP added by the trusted proxy, not the leftmost (client-supplied)
            parts = [p.strip() for p in forwarded.split(",")]
            if len(parts) >= 2:
                return parts[-2]  # IP added by the last trusted proxy
            return parts[0]
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"


limiter = Limiter(key_func=get_real_ip)
