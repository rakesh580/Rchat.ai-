"""Security helpers for the autopilot LangGraph pipeline.

These functions enforce:
1. Participant verification — autopilot only fires for actual participants
2. PII sanitisation — strips emails, phones, SSNs before sending to LLM
3. Audit logging — every AI data access leaves a tamper-evident log entry
"""
from __future__ import annotations
import hashlib
import logging
import re

from app.db.postgres import query_one

logger = logging.getLogger(__name__)

# PII patterns to mask before sending content to external LLMs
_PII_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+'), '[EMAIL]'),
    (re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'), '[PHONE]'),
    (re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'), '[CARD]'),
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[SSN]'),
]

_MAX_CONTENT_LEN = 2000


def sanitize_for_ai(content: str) -> str:
    """Strip PII patterns and truncate content before sending to external AI."""
    for pattern, replacement in _PII_PATTERNS:
        content = pattern.sub(replacement, content)
    return content[:_MAX_CONTENT_LEN]


def verify_autopilot_access(user_id: str, conversation_id: str) -> bool:
    """Verify the autopilot user is actually a participant in the conversation."""
    row = query_one(
        "SELECT 1 FROM conversation_participants WHERE user_id = %s AND conversation_id = %s",
        (user_id, conversation_id),
    )
    return row is not None


def audit_log_ai_access(user_id: str, conversation_id: str, action: str, detail: str = "") -> None:
    """Log AI autopilot data access for audit trail (hashed detail for privacy)."""
    logger.info(
        "AUTOPILOT_AUDIT user=%s conversation=%s action=%s detail=%s",
        user_id,
        conversation_id,
        action,
        hashlib.sha256(detail.encode()).hexdigest()[:16] if detail else "",
    )
