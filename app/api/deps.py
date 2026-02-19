from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from app.services.user_service import get_user_by_id
from app.core.security import decode_access_token

oauth2_scheme = APIKeyHeader(name="Authorization")


def get_current_user(token: str = Depends(oauth2_scheme)):
    if token.lower().startswith("bearer "):
        token = token.split(" ")[1]

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
