import json
import logging
from groq import Groq
from app.core.config import settings
from app.db.postgres import query, query_one, execute, execute_returning, get_conn, put_conn
from app.services.message_service import save_message
from app.services.conversation_service import get_or_create_direct
import psycopg2.extras

logger = logging.getLogger(__name__)

groq_client = Groq(api_key=settings.GROQ_API_KEY)


# ---------------------------------------------------------------------------
# Settings CRUD
# ---------------------------------------------------------------------------

def get_autopilot_settings(user_id: str) -> dict | None:
    row = query_one(
        "SELECT * FROM autopilot_settings WHERE user_id = %s",
        (user_id,),
    )
    if row:
        row["_id"] = str(row.pop("id"))
        row["user_id"] = str(row["user_id"])
        if row.get("backup_person_id"):
            row["backup_person_id"] = str(row["backup_person_id"])
    return row


def upsert_autopilot_settings(user_id: str, updates: dict) -> dict:
    existing = get_autopilot_settings(user_id)
    was_active = existing["is_active"] if existing else False
    now_active = updates.get("is_active", False)

    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO autopilot_settings
                       (user_id, is_active, away_message, backup_person_id,
                        auto_respond_enabled, expected_return_date,
                        activated_at, deactivated_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s,
                           CASE WHEN %s THEN NOW() ELSE NULL END,
                           NULL, NOW())
                   ON CONFLICT (user_id) DO UPDATE SET
                       is_active = EXCLUDED.is_active,
                       away_message = EXCLUDED.away_message,
                       backup_person_id = EXCLUDED.backup_person_id,
                       auto_respond_enabled = EXCLUDED.auto_respond_enabled,
                       expected_return_date = EXCLUDED.expected_return_date,
                       activated_at = CASE
                           WHEN EXCLUDED.is_active AND NOT autopilot_settings.is_active THEN NOW()
                           WHEN NOT EXCLUDED.is_active THEN autopilot_settings.activated_at
                           ELSE autopilot_settings.activated_at END,
                       deactivated_at = CASE
                           WHEN NOT EXCLUDED.is_active AND autopilot_settings.is_active THEN NOW()
                           ELSE autopilot_settings.deactivated_at END,
                       updated_at = NOW()
                   RETURNING *""",
                (
                    user_id,
                    now_active,
                    updates.get("away_message", ""),
                    updates.get("backup_person_id"),
                    updates.get("auto_respond_enabled", True),
                    updates.get("expected_return_date"),
                    now_active,
                ),
            )
            row = dict(cur.fetchone())

            # Keep users.is_autopilot in sync
            cur.execute(
                "UPDATE users SET is_autopilot = %s WHERE id = %s",
                (now_active, user_id),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)

    row["_id"] = str(row.pop("id"))
    row["user_id"] = str(row["user_id"])
    if row.get("backup_person_id"):
        row["backup_person_id"] = str(row["backup_person_id"])
    return row


def is_user_on_autopilot(user_id: str) -> bool:
    row = query_one(
        "SELECT 1 FROM autopilot_settings WHERE user_id = %s AND is_active = TRUE",
        (user_id,),
    )
    return row is not None


def get_autopilot_config(user_id: str) -> dict | None:
    row = query_one(
        """SELECT a.*, u.display_name AS backup_name
           FROM autopilot_settings a
           LEFT JOIN users u ON u.id = a.backup_person_id
           WHERE a.user_id = %s AND a.is_active = TRUE""",
        (user_id,),
    )
    if row:
        row["_id"] = str(row.pop("id"))
        row["user_id"] = str(row["user_id"])
        if row.get("backup_person_id"):
            row["backup_person_id"] = str(row["backup_person_id"])
    return row


# ---------------------------------------------------------------------------
# AI Classification
# ---------------------------------------------------------------------------

CLASSIFY_SYSTEM = """You are a message classifier for a chat autopilot system.
The recipient is currently away. Classify the incoming message into exactly one category:
- "urgent": Emergencies, time-sensitive requests, blocking issues
- "action_needed": Requires the recipient to do something but not immediately
- "informational": FYI, casual chat, greetings, no action required

Also determine if you can provide a helpful auto-response.
Only auto-respond if the message is a direct question that can be answered helpfully.
Do NOT auto-respond to casual greetings or informational messages.

Respond ONLY with valid JSON (no markdown):
{"category": "urgent|action_needed|informational", "should_auto_respond": true/false, "auto_response": "response text or null", "deadline": "ISO date if action_needed or null"}"""


def classify_message(conversation_id: str, sender_id: str, content: str, user_id: str) -> dict:
    # Get recent messages for context
    rows = query(
        """SELECT sender_id, content FROM messages
           WHERE conversation_id = %s
           ORDER BY created_at DESC LIMIT 10""",
        (conversation_id,),
    )
    past = []
    for r in rows:
        role = "assistant" if str(r["sender_id"]) == user_id else "user"
        past.append({"role": role, "content": r["content"]})
    past.reverse()

    messages = [
        {"role": "system", "content": CLASSIFY_SYSTEM},
        *past,
        {"role": "user", "content": f"New incoming message from another user: {content}"},
    ]

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=300,
            temperature=0.1,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
        result = json.loads(raw)
        # Validate category
        if result.get("category") not in ("urgent", "action_needed", "informational"):
            result["category"] = "informational"
        return result
    except Exception as exc:
        logger.error("Autopilot classify failed: %s", exc)
        return {
            "category": "informational",
            "should_auto_respond": False,
            "auto_response": None,
            "deadline": None,
        }


# ---------------------------------------------------------------------------
# Activity Log
# ---------------------------------------------------------------------------

def log_activity(
    user_id: str,
    conversation_id: str,
    message_id: str,
    sender_id: str,
    category: str,
    action_taken: str,
    auto_response_content: str | None = None,
    deadline: str | None = None,
) -> dict:
    row = execute_returning(
        """INSERT INTO autopilot_activity_log
               (user_id, conversation_id, message_id, sender_id,
                category, action_taken, auto_response_content, deadline)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING *""",
        (user_id, conversation_id, message_id, sender_id,
         category, action_taken, auto_response_content, deadline),
    )
    if row:
        row["_id"] = str(row.pop("id"))
    return row


def get_briefing(user_id: str) -> dict:
    rows = query(
        """SELECT a.*, u.display_name AS sender_name, u.username AS sender_username
           FROM autopilot_activity_log a
           JOIN users u ON u.id = a.sender_id
           WHERE a.user_id = %s AND a.is_resolved = FALSE
           ORDER BY a.created_at ASC""",
        (user_id,),
    )

    briefing = {"urgent": [], "action_needed": [], "informational": []}
    auto_count = 0
    fwd_count = 0

    for r in rows:
        r["_id"] = str(r.pop("id"))
        r["conversation_id"] = str(r["conversation_id"])
        r["message_id"] = str(r["message_id"])
        r["sender_id"] = str(r["sender_id"])
        r["user_id"] = str(r["user_id"])
        r["sender_name"] = r.get("sender_name") or r.get("sender_username", "Unknown")
        r.pop("sender_username", None)

        cat = r["category"]
        if cat in briefing:
            briefing[cat].append(r)

        if r["action_taken"] == "auto_responded":
            auto_count += 1
        elif r["action_taken"] == "forwarded":
            fwd_count += 1

    return {
        **briefing,
        "total_messages": len(rows),
        "auto_responses_sent": auto_count,
        "messages_forwarded": fwd_count,
    }


def has_unresolved_activity(user_id: str) -> bool:
    row = query_one(
        "SELECT 1 FROM autopilot_activity_log WHERE user_id = %s AND is_resolved = FALSE LIMIT 1",
        (user_id,),
    )
    return row is not None


def mark_briefing_resolved(user_id: str) -> int:
    return execute(
        "UPDATE autopilot_activity_log SET is_resolved = TRUE WHERE user_id = %s AND is_resolved = FALSE",
        (user_id,),
    )


# ---------------------------------------------------------------------------
# Forward to Backup
# ---------------------------------------------------------------------------

def forward_to_backup(
    autopilot_user_id: str,
    backup_person_id: str,
    original_sender_id: str,
    conversation_id: str,
    content: str,
) -> dict:
    # Get sender name for context
    sender = query_one("SELECT display_name, username FROM users WHERE id = %s", (original_sender_id,))
    sender_name = (sender.get("display_name") or sender.get("username", "Someone")) if sender else "Someone"

    # Get or create direct conversation between autopilot user and backup
    convo = get_or_create_direct(autopilot_user_id, backup_person_id)

    fwd_content = f"[Forwarded - Urgent] From {sender_name}: {content}"
    return save_message(convo["_id"], autopilot_user_id, fwd_content)
