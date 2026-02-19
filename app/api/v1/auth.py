from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.user import UserCreate, UserOut, UserLogin, Token
from app.services.user_service import (
    create_user,
    authenticate_user,
    get_user_by_email,
    get_user_by_username,
)
from app.core.security import create_access_token
from app.core.config import settings
from app.db.mongo import contacts_collection, conversations_collection
from app.db.init_db import AI_BOT_ID

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate):
    if get_user_by_email(user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if get_user_by_username(user_in.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    user = create_user(user_in)
    user_id = user["_id"]

    # Auto-add AI bot as contact + create conversation
    bot_id = str(AI_BOT_ID)
    contacts_collection.insert_one({"user_id": user_id, "contact_id": bot_id})
    conversations_collection.insert_one({
        "type": "direct",
        "participants": [user_id, bot_id],
        "group_name": None,
        "admins": [],
        "last_message": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })

    return UserOut(**user)


@router.post("/login", response_model=Token)
def login(user_in: UserLogin):
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
    return Token(access_token=token)


@router.post("/token", response_model=Token)
def login_for_swagger(form_data: OAuth2PasswordRequestForm = Depends()):
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
