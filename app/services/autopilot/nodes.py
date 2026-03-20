"""LangGraph node functions for the autopilot pipeline.

Each node receives the full AutopilotState dict, does its work,
and returns a partial dict of updated fields that LangGraph merges back.

Node execution order (with conditional branches):
  load_context → sanitize → classify
      ├─ urgent + backup → forward_to_backup
      ├─ should_auto_respond → compose_response → send_auto_reply
      └─ all paths → log_activity
"""
from __future__ import annotations
import json
import logging
from typing import Any

from langchain_groq import ChatGroq

from app.core.config import settings
from app.services.autopilot.state import AutopilotState
from app.services.autopilot.security import (
    verify_autopilot_access,
    audit_log_ai_access,
    sanitize_for_ai,
)
from app.services.autopilot.prompts import CLASSIFY_SYSTEM, COMPOSE_SYSTEM
from app.services.autopilot.tools import (
    get_conversation_history,
    get_autopilot_config,
    save_auto_reply,
    forward_urgent_message,
    log_autopilot_activity,
)

logger = logging.getLogger(__name__)

# Shared LLM instance (stateless — safe to reuse across runs)
_llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.AUTOPILOT_MODEL,
    temperature=0.1,
    max_tokens=400,
    max_retries=settings.AUTOPILOT_MAX_RETRIES,
)


# ---------------------------------------------------------------------------
# Node 1: load_context
# ---------------------------------------------------------------------------

def load_context(state: AutopilotState) -> dict:
    """Load autopilot config and conversation history from the database."""
    user_id = state["autopilot_user_id"]
    conversation_id = state["conversation_id"]

    # Security gate — abort early if user is not a participant
    if not verify_autopilot_access(user_id, conversation_id):
        logger.warning(
            "AUTOPILOT_SECURITY: user %s not in conversation %s — aborting",
            user_id, conversation_id,
        )
        return {"aborted": True, "errors": ["Security: participant verification failed"]}

    audit_log_ai_access(user_id, conversation_id, "load_context", state.get("raw_content", ""))

    config = get_autopilot_config.invoke({"user_id": user_id})
    if not config:
        return {"aborted": True, "errors": ["Autopilot config not found or inactive"]}

    history = get_conversation_history.invoke({
        "conversation_id": conversation_id,
        "user_id": user_id,
        "limit": settings.AUTOPILOT_CONTEXT_MESSAGES,
    })

    return {
        "autopilot_config": config,
        "conversation_history": history,
        "errors": [],
        "aborted": False,
    }


# ---------------------------------------------------------------------------
# Node 2: sanitize
# ---------------------------------------------------------------------------

def sanitize(state: AutopilotState) -> dict:
    """Strip PII from message content and history before LLM calls."""
    safe_content = sanitize_for_ai(state.get("raw_content", ""))
    safe_history = [
        {"role": msg["role"], "content": sanitize_for_ai(msg["content"])}
        for msg in state.get("conversation_history", [])
    ]
    return {"safe_content": safe_content, "safe_history": safe_history}


# ---------------------------------------------------------------------------
# Node 3: classify
# ---------------------------------------------------------------------------

def classify(state: AutopilotState) -> dict:
    """Call the LLM to classify the message and decide on auto-response."""
    messages = [
        {"role": "system", "content": CLASSIFY_SYSTEM},
        *state.get("safe_history", []),
        {"role": "user", "content": f"New incoming message: {state['safe_content']}"},
    ]

    try:
        resp = _llm.invoke(messages)
        raw = resp.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        result = json.loads(raw)
        category = result.get("category", "informational")
        if category not in ("urgent", "action_needed", "informational"):
            category = "informational"

        return {
            "category": category,
            "should_auto_respond": bool(result.get("should_auto_respond", False)),
            "auto_response_draft": result.get("auto_response"),
            "deadline": result.get("deadline"),
            "classification_raw": raw,
        }
    except Exception as exc:
        logger.error("Autopilot classify failed: %s", exc)
        return {
            "category": "informational",
            "should_auto_respond": False,
            "auto_response_draft": None,
            "deadline": None,
            "classification_raw": "",
            "errors": state.get("errors", []) + [f"classify error: {exc}"],
        }


# ---------------------------------------------------------------------------
# Node 4: forward_to_backup
# ---------------------------------------------------------------------------

def forward_to_backup(state: AutopilotState) -> dict:
    """Forward an urgent message to the configured backup person."""
    config = state.get("autopilot_config", {})
    backup_id = config.get("backup_person_id")

    if not backup_id:
        return {"forwarded": False, "forwarded_message_id": None}

    result = forward_urgent_message.invoke({
        "autopilot_user_id": state["autopilot_user_id"],
        "backup_person_id": backup_id,
        "original_sender_id": state["sender_id"],
        "conversation_id": state["conversation_id"],
        "content": state.get("raw_content", ""),
    })

    forwarded = bool(result and result.get("_id"))
    return {
        "forwarded": forwarded,
        "forwarded_message_id": result.get("_id") if forwarded else None,
        "action_taken": "forwarded" if forwarded else "logged",
    }


# ---------------------------------------------------------------------------
# Node 5: compose_response
# ---------------------------------------------------------------------------

def compose_response(state: AutopilotState) -> dict:
    """Use the LLM to compose a polished auto-reply from the draft."""
    draft = state.get("auto_response_draft") or ""
    config = state.get("autopilot_config", {})
    away_msg = config.get("away_message", "")

    prompt = (
        f"The user is away. Their away message: '{away_msg}'\n"
        f"Draft auto-response to refine: '{draft}'\n"
        f"Original message received: '{state.get('safe_content', '')}'"
    )

    try:
        resp = _llm.invoke([
            {"role": "system", "content": COMPOSE_SYSTEM},
            {"role": "user", "content": prompt},
        ])
        composed = resp.content.strip()
        return {"composed_response": composed}
    except Exception as exc:
        logger.error("Autopilot compose failed: %s", exc)
        # Fall back to the draft
        return {
            "composed_response": draft or away_msg or "I am currently away. I'll get back to you soon.",
            "errors": state.get("errors", []) + [f"compose error: {exc}"],
        }


# ---------------------------------------------------------------------------
# Node 6: send_auto_reply
# ---------------------------------------------------------------------------

def send_auto_reply(state: AutopilotState) -> dict:
    """Save the composed reply to DB and emit it via Socket.IO."""
    composed = state.get("composed_response") or state.get("auto_response_draft")
    if not composed:
        return {"auto_reply_message_id": None, "action_taken": "logged"}

    saved = save_auto_reply.invoke({
        "conversation_id": state["conversation_id"],
        "autopilot_user_id": state["autopilot_user_id"],
        "content": composed,
    })

    msg_id = saved.get("_id") if saved else None

    # Emit via the injected socket notify function
    notify_fn = state.get("socket_notify_fn")
    if notify_fn and saved:
        import asyncio
        room = f"conv:{state['conversation_id']}"
        payload = {
            "_id": saved["_id"],
            "conversation_id": saved["conversation_id"],
            "sender_id": saved["sender_id"],
            "content": saved["content"],
            "message_type": saved.get("message_type", "text"),
            "status": saved.get("status", "sent"),
            "read_by": saved.get("read_by", []),
            "created_at": saved["created_at"].isoformat() if hasattr(saved.get("created_at"), "isoformat") else str(saved.get("created_at", "")),
            "is_autopilot_reply": True,
        }
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(notify_fn("message:new", payload, room))
            else:
                loop.run_until_complete(notify_fn("message:new", payload, room))
        except Exception as exc:
            logger.error("Autopilot socket emit failed: %s", exc)

    return {
        "auto_reply_message_id": msg_id,
        "action_taken": "auto_responded" if msg_id else "logged",
    }


# ---------------------------------------------------------------------------
# Node 7: log_activity
# ---------------------------------------------------------------------------

def log_activity(state: AutopilotState) -> dict:
    """Write the final action to the autopilot_activity_log table."""
    # Determine final action_taken
    action = state.get("action_taken", "logged")
    if action == "logged" and state.get("category") == "action_needed":
        action = "queued"

    entry = log_autopilot_activity.invoke({
        "user_id": state["autopilot_user_id"],
        "conversation_id": state["conversation_id"],
        "message_id": state.get("_message_id", ""),
        "sender_id": state["sender_id"],
        "category": state.get("category", "informational"),
        "action_taken": action,
        "auto_response_content": state.get("composed_response") or state.get("auto_response_draft"),
        "deadline": state.get("deadline"),
    })

    return {
        "action_taken": action,
        "log_entry_id": entry.get("_id") if entry else None,
    }
