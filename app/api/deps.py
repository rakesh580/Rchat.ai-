from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader

from app.services.user_service import get_user_by_id
from app.core.security import decode_access_token

oauth2_scheme = APIKeyHeader(name="Authorization", auto_error=False)


def get_current_user(request: Request, token: str | None = Depends(oauth2_scheme)):
    # Try Authorization header first, then fall back to httpOnly cookie
    if token:
        if token.lower().startswith("bearer "):
            token = token.split(" ", 1)[1]
    else:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Check if token has been blocklisted (logged out)
    from app.core.token_blocklist import is_token_blocklisted
    if is_token_blocklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        user = get_user_by_id(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
