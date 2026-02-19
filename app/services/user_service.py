from datetime import datetime
from bson import ObjectId
from app.db.mongo import users_collection
from app.core.security import hash_password, verify_password
from app.schemas.user import UserCreate


def get_user_by_id(user_id: str):
    return users_collection.find_one({"_id": ObjectId(user_id)})


def get_user_by_email(email: str):
    return users_collection.find_one({"email": email})


def get_user_by_username(username: str):
    return users_collection.find_one({"username": username})


def create_user(user_in: UserCreate) -> dict:
    hashed_pw = hash_password(user_in.password)
    doc = {
        "email": user_in.email,
        "username": user_in.username,
        "hashed_password": hashed_pw,
        "display_name": user_in.username,
        "avatar_url": "",
        "bio": "",
        "is_online": False,
        "last_seen": datetime.utcnow(),
        "is_bot": False,
        "created_at": datetime.utcnow(),
    }
    result = users_collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


def authenticate_user(username_or_email: str, password: str):
    user = get_user_by_email(username_or_email) or get_user_by_username(username_or_email)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def update_user_profile(user_id: str, updates: dict) -> dict | None:
    """Update user profile fields (display_name, bio, avatar_url)."""
    clean = {k: v for k, v in updates.items() if v is not None}
    if not clean:
        return get_user_by_id(user_id)
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": clean},
    )
    return get_user_by_id(user_id)
