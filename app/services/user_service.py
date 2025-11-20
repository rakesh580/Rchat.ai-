from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import verify_password


def create_user(db: Session, user_in: UserCreate):
    """
    Inserts a new user into the database.
    """

    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=user_in.password  # hashing will be added in Feature 5
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user_by_username_or_email(db: Session, username_or_email: str):
    """Fetch user by username OR email."""
    return (
        db.query(User)
        .filter(
            (User.email == username_or_email) |
            (User.username == username_or_email)
        )
        .first()
    )


def authenticate_user(db: Session, username_or_email: str, password: str):
    """
    Validate user credentials.
    """
    user = get_user_by_username_or_email(db, username_or_email)

    if not user:
        return None

    # Compare password input with stored hash
    if not verify_password(password, user.hashed_password):
        return None

    return user