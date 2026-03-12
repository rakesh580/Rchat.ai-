from app.db.postgres import query, query_one, execute_returning, execute, get_conn, put_conn
import psycopg2.extras


def get_or_create_direct(user_id: str, other_user_id: str) -> dict:
    """Find existing direct conversation or create one."""
    # Find existing
    row = query_one(
        """SELECT c.* FROM conversations c
           JOIN conversation_participants cp1 ON c.id = cp1.conversation_id AND cp1.user_id = %s
           JOIN conversation_participants cp2 ON c.id = cp2.conversation_id AND cp2.user_id = %s
           WHERE c.type = 'direct'""",
        (user_id, other_user_id),
    )
    if row:
        row["_id"] = str(row.pop("id"))
        row["participants"] = [user_id, other_user_id]
        return row

    # Create new
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO conversations (type, created_at, updated_at)
                   VALUES ('direct', NOW(), NOW()) RETURNING *""",
            )
            convo = dict(cur.fetchone())
            conv_id = convo["id"]
            cur.execute(
                "INSERT INTO conversation_participants (conversation_id, user_id) VALUES (%s, %s), (%s, %s)",
                (conv_id, user_id, conv_id, other_user_id),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)

    convo["_id"] = str(convo.pop("id"))
    convo["participants"] = [user_id, other_user_id]
    convo["admins"] = []
    return convo


def create_group(creator_id: str, participant_ids: list[str], group_name: str) -> dict:
    all_participants = list(set([creator_id] + participant_ids))

    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO conversations (type, group_name, created_by, created_at, updated_at)
                   VALUES ('group', %s, %s, NOW(), NOW()) RETURNING *""",
                (group_name, creator_id),
            )
            convo = dict(cur.fetchone())
            conv_id = convo["id"]

            for pid in all_participants:
                is_admin = pid == creator_id
                cur.execute(
                    "INSERT INTO conversation_participants (conversation_id, user_id, is_admin) VALUES (%s, %s, %s)",
                    (conv_id, pid, is_admin),
                )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)

    convo["_id"] = str(convo.pop("id"))
    convo["participants"] = all_participants
    convo["admins"] = [creator_id]
    return convo


def get_user_conversations(user_id: str) -> list[dict]:
    rows = query(
        """SELECT c.*, cp.user_id AS my_id
           FROM conversations c
           JOIN conversation_participants cp ON c.id = cp.conversation_id AND cp.user_id = %s
           ORDER BY c.updated_at DESC""",
        (user_id,),
    )

    conversations = []
    for convo in rows:
        conv_id = convo["id"]
        convo["_id"] = str(convo.pop("id"))
        convo.pop("my_id", None)

        # Get participants with profiles
        participants = query(
            """SELECT u.id, u.username, u.display_name, u.avatar_url, u.is_online, u.last_seen, u.is_bot
               FROM users u
               JOIN conversation_participants cp ON u.id = cp.conversation_id
               WHERE cp.conversation_id = %s""",
            (conv_id,),
        )
        # Fix: that join was wrong, let me use a proper query
        participants = query(
            """SELECT u.id AS _id, u.username, u.display_name, u.avatar_url, u.is_online, u.last_seen, u.is_bot
               FROM conversation_participants cp
               JOIN users u ON u.id = cp.user_id
               WHERE cp.conversation_id = %s""",
            (conv_id,),
        )
        for p in participants:
            p["_id"] = str(p["_id"])

        convo["participants"] = participants

        # Get admins
        admins = query(
            "SELECT user_id FROM conversation_participants WHERE conversation_id = %s AND is_admin = TRUE",
            (conv_id,),
        )
        convo["admins"] = [str(a["user_id"]) for a in admins]

        # Unread count
        unread_row = query_one(
            """SELECT COUNT(*) AS cnt FROM messages m
               WHERE m.conversation_id = %s
               AND m.sender_id != %s
               AND NOT EXISTS (
                   SELECT 1 FROM message_reads mr WHERE mr.message_id = m.id AND mr.user_id = %s
               )""",
            (conv_id, user_id, user_id),
        )
        convo["unread_count"] = unread_row["cnt"] if unread_row else 0

        # Build last_message from columns
        if convo.get("last_message_content"):
            convo["last_message"] = {
                "content": convo["last_message_content"],
                "sender_id": str(convo["last_message_sender_id"]) if convo.get("last_message_sender_id") else None,
                "timestamp": convo["last_message_timestamp"],
            }
        else:
            convo["last_message"] = None

        # Clean up flat last_message columns
        convo.pop("last_message_content", None)
        convo.pop("last_message_sender_id", None)
        convo.pop("last_message_timestamp", None)
        convo.pop("created_by", None)

        conversations.append(convo)

    return conversations


def get_conversation_by_id(conversation_id: str) -> dict | None:
    convo = query_one("SELECT * FROM conversations WHERE id = %s", (conversation_id,))
    if not convo:
        return None
    conv_id = convo["id"]
    convo["_id"] = str(convo.pop("id"))

    # Get participant IDs (as strings)
    parts = query(
        "SELECT user_id FROM conversation_participants WHERE conversation_id = %s",
        (conv_id,),
    )
    convo["participants"] = [str(p["user_id"]) for p in parts]

    admins = query(
        "SELECT user_id FROM conversation_participants WHERE conversation_id = %s AND is_admin = TRUE",
        (conv_id,),
    )
    convo["admins"] = [str(a["user_id"]) for a in admins]

    return convo


def get_conversation_with_profiles(conversation_id: str) -> dict | None:
    convo = query_one("SELECT * FROM conversations WHERE id = %s", (conversation_id,))
    if not convo:
        return None
    conv_id = convo["id"]
    convo["_id"] = str(convo.pop("id"))

    participants = query(
        """SELECT u.id AS _id, u.username, u.display_name, u.avatar_url, u.is_online, u.last_seen, u.is_bot
           FROM conversation_participants cp
           JOIN users u ON u.id = cp.user_id
           WHERE cp.conversation_id = %s""",
        (conv_id,),
    )
    for p in participants:
        p["_id"] = str(p["_id"])
    convo["participants"] = participants

    admins = query(
        "SELECT user_id FROM conversation_participants WHERE conversation_id = %s AND is_admin = TRUE",
        (conv_id,),
    )
    convo["admins"] = [str(a["user_id"]) for a in admins]

    return convo


def add_member_to_group(conversation_id: str, user_id: str) -> bool:
    try:
        rowcount = execute(
            "INSERT INTO conversation_participants (conversation_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (conversation_id, user_id),
        )
        return rowcount > 0
    except Exception:
        return False


def remove_member_from_group(conversation_id: str, user_id: str) -> bool:
    rowcount = execute(
        "DELETE FROM conversation_participants WHERE conversation_id = %s AND user_id = %s",
        (conversation_id, user_id),
    )
    return rowcount > 0
