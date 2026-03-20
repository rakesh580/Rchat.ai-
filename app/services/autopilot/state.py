"""AutopilotState — shared typed state threaded through every LangGraph node."""
from __future__ import annotations
from typing import Any, TypedDict


class AutopilotState(TypedDict, total=False):
    # ── Inputs (set by caller before graph run) ────────────────────────────
    conversation_id: str
    sender_id: str
    raw_content: str          # original message, never mutated
    autopilot_user_id: str    # the away user whose autopilot is active
    socket_notify_fn: Any     # async callable(event, payload, room) injected at runtime

    # ── Config (loaded in load_context node) ──────────────────────────────
    autopilot_config: dict
    conversation_history: list[dict]   # [{role, content}, …] last N messages

    # ── Sanitised content (set by sanitize node) ──────────────────────────
    safe_content: str
    safe_history: list[dict]

    # ── Classification (set by classify node) ─────────────────────────────
    category: str             # "urgent" | "action_needed" | "informational"
    should_auto_respond: bool
    auto_response_draft: str | None
    deadline: str | None
    classification_raw: str   # raw LLM output for debugging

    # ── Forwarding (set by forward_to_backup node) ─────────────────────────
    forwarded: bool
    forwarded_message_id: str | None

    # ── Auto-reply (set by compose_response / send_auto_reply nodes) ──────
    composed_response: str | None     # final composed text
    auto_reply_message_id: str | None

    # ── Activity log (set by log_activity node) ───────────────────────────
    action_taken: str         # "logged" | "queued" | "forwarded" | "auto_responded"
    log_entry_id: str | None

    # ── Error tracking ────────────────────────────────────────────────────
    errors: list[str]
    aborted: bool             # True if a security check caused early exit
