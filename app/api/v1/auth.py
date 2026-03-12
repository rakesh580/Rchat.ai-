from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.api.deps import get_current_user
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.user import UserCreate, UserOut, UserLogin, Token
from app.core.rate_limit import limiter
from app.services.user_service import (
    create_user,
    authenticate_user,
    get_user_by_email,
    get_user_by_username,
)
from app.core.security import create_access_token
from app.core.config import settings
from app.db.postgres import execute, execute_returning
from app.db.init_db import AI_BOT_ID

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut)
@limiter.limit("5/minute")
def register(request: Request, user_in: UserCreate):
    if get_user_by_email(user_in.email) or get_user_by_username(user_in.username):
        raise HTTPException(status_code=400, detail="Registration failed — email or username unavailable")

    user = create_user(user_in)
    user_id = user["_id"]

    # Auto-add AI bot as contact + create conversation
    bot_id = str(AI_BOT_ID)
    execute(
        "INSERT INTO contacts (user_id, contact_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (user_id, bot_id),
    )
    conv = execute_returning(
        """INSERT INTO conversations (type, created_by, created_at, updated_at)
           VALUES ('direct', %s, NOW(), NOW()) RETURNING id""",
        (user_id,),
    )
    if conv:
        conv_id = str(conv["id"])
        execute(
            "INSERT INTO conversation_participants (conversation_id, user_id) VALUES (%s, %s), (%s, %s)",
            (conv_id, user_id, conv_id, bot_id),
        )

    return UserOut(**user)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, user_in: UserLogin):
    user = authenticate_user(user_in.username_or_email, user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
        )

    token = create_access_token(
        data={"sub": str(user["_id"])},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    response = JSONResponse(content={"access_token": token, "token_type": "bearer"})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response


@router.post("/token", response_model=Token)
@limiter.limit("10/minute")
def login_for_swagger(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token(
        data={"sub": str(user["_id"])},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=token)


@router.post("/logout")
def logout(request: Request, current_user=Depends(get_current_user)):
    # Extract current token for blocklist
    token = request.headers.get("Authorization", "")
    if token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1]
    else:
        token = request.cookies.get("access_token", "")

    if token:
        from app.core.token_blocklist import blocklist_token
        blocklist_token(token)

    response = JSONResponse(content={"msg": "Logged out"})
    response.delete_cookie("access_token", path="/")
    return response
