from app.db.postgres import query_one, execute_returning, execute
from app.core.security import hash_password, verify_password
from app.schemas.user import UserCreate


def get_user_by_id(user_id: str) -> dict | None:
    row = query_one("SELECT * FROM users WHERE id = %s", (user_id,))
    if row:
        row["_id"] = str(row.pop("id"))
    return row


def get_user_by_email(email: str) -> dict | None:
    row = query_one("SELECT * FROM users WHERE email = %s", (email,))
    if row:
        row["_id"] = str(row.pop("id"))
    return row


def get_user_by_username(username: str) -> dict | None:
    row = query_one("SELECT * FROM users WHERE username = %s", (username,))
    if row:
        row["_id"] = str(row.pop("id"))
    return row


def create_user(user_in: UserCreate) -> dict:
    hashed_pw = hash_password(user_in.password)
    row = execute_returning(
        """INSERT INTO users (email, username, hashed_password, display_name, bio, is_online, is_bot, created_at)
           VALUES (%s, %s, %s, %s, '', FALSE, FALSE, NOW())
           RETURNING *""",
        (user_in.email, user_in.username, hashed_pw, user_in.username),
    )
    row["_id"] = str(row.pop("id"))
    return row


def authenticate_user(username_or_email: str, password: str) -> dict | None:
    user = get_user_by_email(username_or_email) or get_user_by_username(username_or_email)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


ALLOWED_PROFILE_COLUMNS = {"display_name", "bio", "avatar_url"}


def update_user_profile(user_id: str, updates: dict) -> dict | None:
    clean = {k: v for k, v in updates.items() if v is not None and k in ALLOWED_PROFILE_COLUMNS}
    if not clean:
        return get_user_by_id(user_id)

    set_clauses = ", ".join(f"{k} = %s" for k in clean)
    values = list(clean.values()) + [user_id]
    execute(
        f"UPDATE users SET {set_clauses} WHERE id = %s",
        tuple(values),
    )
    return get_user_by_id(user_id)
