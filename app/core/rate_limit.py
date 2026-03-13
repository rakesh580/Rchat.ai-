from slowapi import Limiter
from starlette.requests import Request


def get_real_ip(request: Request) -> str:
    """Extract client IP, handling reverse proxies (HF Spaces, nginx, etc.)."""
    # Check X-Forwarded-For first (set by reverse proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    # Check X-Real-IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    # Fall back to direct client (may be None behind proxy)
    if request.client:
        return request.client.host
    return "127.0.0.1"


limiter = Limiter(key_func=get_real_ip)
