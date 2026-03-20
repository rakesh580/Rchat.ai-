from app.db.postgres import query_one

AI_BOT_ID = "00000000-0000-0000-0000-000000000001"


def init_db() -> None:
    """Verify database connection and AI bot user exists."""
    # Test connection
    row = query_one("SELECT 1 AS ok")
    if not row:
        raise RuntimeError("Database connection failed")

    # Verify AI bot exists
    bot = query_one("SELECT id FROM users WHERE id = %s", (AI_BOT_ID,))
    if not bot:
        from app.db.postgres import execute
        execute(
            """INSERT INTO users (id, email, username, display_name, hashed_password, is_online, is_bot, created_at)
               VALUES (%s, 'ai@rchat.ai', 'rchat_ai', 'Rchat.ai Bot', '', TRUE, TRUE, NOW())
               ON CONFLICT (id) DO NOTHING""",
            (AI_BOT_ID,),
        )
