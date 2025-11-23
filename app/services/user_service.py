# app/services/user_service.py
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password


def create_user(db: Session, user_in: UserCreate) -> User:
    """
    Inserts a new user into the database with a hashed password.
    """
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_username_or_email(db: Session, username_or_email: str) -> User | None:
    return (
        db.query(User)
        .filter(
            (User.email == username_or_email)
            | (User.username == username_or_email)
        )
        .first()
    )


def authenticate_user(db, username_or_email, password):
    user = get_user_by_username_or_email(db, username_or_email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

    if not verify_password(password, user.hashed_password):
        return None

    return user