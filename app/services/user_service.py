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


# Explicit mapping of allowed columns to prevent SQL injection
_ALLOWED_COLUMN_MAP = {
    "display_name": "display_name",
    "bio": "bio",
    "avatar_url": "avatar_url",
}


def update_user_profile(user_id: str, updates: dict) -> dict | None:
    clean = {_ALLOWED_COLUMN_MAP[k]: v for k, v in updates.items()
             if v is not None and k in _ALLOWED_COLUMN_MAP}
    if not clean:
        return get_user_by_id(user_id)

    from psycopg2 import sql
    set_parts = [sql.SQL("{} = %s").format(sql.Identifier(col)) for col in clean]
    set_clause = sql.SQL(", ").join(set_parts)
    query_sql = sql.SQL("UPDATE users SET {} WHERE id = %s").format(set_clause)

    values = list(clean.values()) + [user_id]
    from app.db.postgres import get_conn, put_conn
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(query_sql, tuple(values))
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)
    return get_user_by_id(user_id)
