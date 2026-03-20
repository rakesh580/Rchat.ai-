from app.db.postgres import query, query_one, execute, get_conn, put_conn
import psycopg2.extras


def save_message(conversation_id: str, sender_id: str, content: str, message_type: str = "text") -> dict:
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Insert message
            cur.execute(
                """INSERT INTO messages (conversation_id, sender_id, content, message_type, status, created_at)
                   VALUES (%s, %s, %s, %s, 'sent', NOW())
                   RETURNING *""",
                (conversation_id, sender_id, content, message_type),
            )
            msg = dict(cur.fetchone())

            # Mark as read by sender
            cur.execute(
                "INSERT INTO message_reads (message_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (msg["id"], sender_id),
            )

            # Update conversation's last_message
            cur.execute(
                """UPDATE conversations SET
                       last_message_content = %s,
                       last_message_sender_id = %s,
                       last_message_timestamp = %s,
                       updated_at = %s
                   WHERE id = %s""",
                (content, sender_id, msg["created_at"], msg["created_at"], conversation_id),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)

    msg["_id"] = str(msg.pop("id"))
    msg["conversation_id"] = str(msg["conversation_id"])
    msg["sender_id"] = str(msg["sender_id"])
    msg["read_by"] = [sender_id]
    return msg


def get_messages(conversation_id: str, skip: int = 0, limit: int = 50) -> list[dict]:
    rows = query(
        """SELECT m.*, COALESCE(
               (SELECT array_agg(mr.user_id::text) FROM message_reads mr WHERE mr.message_id = m.id),
               ARRAY[]::text[]
           ) AS read_by
           FROM messages m
           WHERE m.conversation_id = %s
           ORDER BY m.created_at ASC
           OFFSET %s LIMIT %s""",
        (conversation_id, skip, limit),
    )
    for msg in rows:
        msg["_id"] = str(msg.pop("id"))
        msg["conversation_id"] = str(msg["conversation_id"])
        msg["sender_id"] = str(msg["sender_id"])
    return rows


def mark_messages_read(conversation_id: str, reader_id: str) -> int:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Insert read receipts for all unread messages
            cur.execute(
                """INSERT INTO message_reads (message_id, user_id)
                   SELECT m.id, %s FROM messages m
                   WHERE m.conversation_id = %s
                   AND m.sender_id != %s
                   AND NOT EXISTS (
                       SELECT 1 FROM message_reads mr WHERE mr.message_id = m.id AND mr.user_id = %s
                   )
                   ON CONFLICT DO NOTHING""",
                (reader_id, conversation_id, reader_id, reader_id),
            )
            count = cur.rowcount

            # Update message status to 'read'
            cur.execute(
                """UPDATE messages SET status = 'read'
                   WHERE conversation_id = %s AND sender_id != %s AND status != 'read'""",
                (conversation_id, reader_id),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)
    return count


def get_unread_count(conversation_id: str, user_id: str) -> int:
    row = query_one(
        """SELECT COUNT(*) AS cnt FROM messages m
           WHERE m.conversation_id = %s
           AND m.sender_id != %s
           AND NOT EXISTS (
               SELECT 1 FROM message_reads mr WHERE mr.message_id = m.id AND mr.user_id = %s
           )""",
        (conversation_id, user_id, user_id),
    )
    return row["cnt"] if row else 0
