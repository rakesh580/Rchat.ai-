"""LangChain @tool wrappers for autopilot DB operations.

These tools are bound to the LLM so it can optionally call them,
and are also called directly by graph nodes for deterministic operations.
"""
from __future__ import annotations
import logging
from typing import Optional

from langchain_core.tools import tool

from app.db.postgres import query, query_one, execute_returning
from app.services.message_service import save_message
from app.services.conversation_service import get_or_create_direct
from app.services.autopilot.security import verify_autopilot_access, audit_log_ai_access

logger = logging.getLogger(__name__)


@tool
def get_conversation_history(conversation_id: str, user_id: str, limit: int = 10) -> list[dict]:
    """Fetch the last N messages from a conversation for context.

    Args:
        conversation_id: UUID of the conversation
        user_id: UUID of the autopilot user (for role assignment)
        limit: number of messages to retrieve (default 10)

    Returns:
        List of {role, content} dicts ordered oldest-first
    """
    rows = query(
        """SELECT sender_id, content FROM messages
           WHERE conversation_id = %s
           ORDER BY created_at DESC LIMIT %s""",
        (conversation_id, limit),
    )
    history = []
    for r in rows:
        role = "assistant" if str(r["sender_id"]) == user_id else "user"
        history.append({"role": role, "content": r["content"]})
    history.reverse()
    return history


@tool
def get_autopilot_config(user_id: str) -> Optional[dict]:
    """Fetch the active autopilot configuration for a user.

    Args:
        user_id: UUID of the user

    Returns:
        Dict with autopilot settings or None if not active
    """
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


@tool
def save_auto_reply(conversation_id: str, autopilot_user_id: str, content: str) -> dict:
    """Save an auto-reply message to the database.

    Args:
        conversation_id: UUID of the conversation
        autopilot_user_id: UUID of the user whose autopilot is responding
        content: The auto-reply text

    Returns:
        Saved message dict with _id, created_at, etc.
    """
    prefixed = f"[Auto-reply via Autopilot] {content}"
    return save_message(conversation_id, autopilot_user_id, prefixed)


@tool
def forward_urgent_message(
    autopilot_user_id: str,
    backup_person_id: str,
    original_sender_id: str,
    conversation_id: str,
    content: str,
) -> dict:
    """Forward an urgent message to the backup person.

    Includes security checks: autopilot user must be in the conversation,
    and backup person must be in the autopilot user's contacts.

    Args:
        autopilot_user_id: UUID of the away user
        backup_person_id: UUID of the person to forward to
        original_sender_id: UUID of who sent the urgent message
        conversation_id: UUID of the original conversation
        content: Message content to forward (will be truncated)

    Returns:
        Saved forward message dict or empty dict if denied
    """
    # Security: Verify autopilot user is a participant
    if not verify_autopilot_access(autopilot_user_id, conversation_id):
        logger.warning(
            "AUTOPILOT_SECURITY: forward denied — user %s not in conversation %s",
            autopilot_user_id, conversation_id,
        )
        return {}

    # Security: Verify backup person is a contact
    contact = query_one(
        "SELECT 1 FROM contacts WHERE user_id = %s AND contact_id = %s",
        (autopilot_user_id, backup_person_id),
    )
    if not contact:
        logger.warning(
            "AUTOPILOT_SECURITY: forward denied — backup %s not in contacts of %s",
            backup_person_id, autopilot_user_id,
        )
        return {}

    audit_log_ai_access(autopilot_user_id, conversation_id, "forward_to_backup", content)

    sender = query_one("SELECT display_name, username FROM users WHERE id = %s", (original_sender_id,))
    sender_name = (sender.get("display_name") or sender.get("username", "Someone")) if sender else "Someone"

    convo = get_or_create_direct(autopilot_user_id, backup_person_id)
    fwd_content = f"[Forwarded - Urgent] From {sender_name}: {content[:500]}"
    return save_message(convo["_id"], autopilot_user_id, fwd_content)


@tool
def log_autopilot_activity(
    user_id: str,
    conversation_id: str,
    message_id: str,
    sender_id: str,
    category: str,
    action_taken: str,
    auto_response_content: Optional[str] = None,
    deadline: Optional[str] = None,
) -> dict:
    """Log an autopilot action to the activity log table.

    Args:
        user_id: UUID of the autopilot user
        conversation_id: UUID of the conversation
        message_id: UUID of the triggering message
        sender_id: UUID of the message sender
        category: "urgent" | "action_needed" | "informational"
        action_taken: "logged" | "queued" | "forwarded" | "auto_responded"
        auto_response_content: Text of auto-reply if sent
        deadline: ISO date string if action_needed

    Returns:
        Created log entry dict
    """
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
    return row or {}
