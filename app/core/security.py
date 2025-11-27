from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------
# Password Hashing Utilities
# ---------------------------
def hash_password(password: str) -> str:
    if len(password) > 72:
        raise ValueError("Password too long — max 72 characters allowed.")
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ---------------------------
# Token Utilities
# ---------------------------
def create_access_token(data: dict, expires_delta=None):
    to_encode = data.copy()

    if isinstance(expires_delta, timedelta):
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=expires_delta or settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,    # <-- FIXED
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None