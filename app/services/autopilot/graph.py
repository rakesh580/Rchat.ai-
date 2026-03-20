"""LangGraph StateGraph for the autopilot pipeline.

Graph topology:
                    ┌─────────────────┐
                    │  load_context   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    sanitize     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    classify     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
   [urgent+backup]  [should_auto_respond]  [else]
   forward_to_backup  compose_response      │
              │              │              │
              │     send_auto_reply◄────────┘(only if composed)
              │              │
              └──────┬───────┘
                     ▼
                log_activity
                     │
                    END
"""
from __future__ import annotations
from typing import Any, Callable

from langgraph.graph import StateGraph, END

from app.services.autopilot.state import AutopilotState
from app.services.autopilot.nodes import (
    load_context,
    sanitize,
    classify,
    forward_to_backup,
    compose_response,
    send_auto_reply,
    log_activity,
)


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------

def _after_load_context(state: AutopilotState) -> str:
    """Skip pipeline if security check failed."""
    if state.get("aborted"):
        return "log_activity"
    return "sanitize"


def _after_classify(state: AutopilotState) -> str:
    """Route based on classification result."""
    category = state.get("category", "informational")
    config = state.get("autopilot_config", {})

    # Urgent with backup → forward
    if category == "urgent" and config.get("backup_person_id"):
        return "forward_to_backup"

    # LLM says auto-respond and feature is enabled → compose
    if state.get("should_auto_respond") and config.get("auto_respond_enabled", True):
        return "compose_response"

    # Otherwise just log
    return "log_activity"


def _after_forward(state: AutopilotState) -> str:
    """After forwarding, also check if we should auto-respond."""
    config = state.get("autopilot_config", {})
    if state.get("should_auto_respond") and config.get("auto_respond_enabled", True):
        return "compose_response"
    return "log_activity"


def _after_compose(state: AutopilotState) -> str:
    """Always send if we composed a response."""
    return "send_auto_reply"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_autopilot_graph(socket_notify_fn: Callable | None = None):
    """Build and compile the autopilot StateGraph.

    Args:
        socket_notify_fn: async callable(event, payload, room) that emits
                          Socket.IO events. Injected at build time so nodes
                          can emit without importing the sockets module
                          (avoids circular imports).

    Returns:
        Compiled LangGraph graph ready for .invoke() calls.
    """

    # Wrap nodes that need the socket function via closure
    def _send_auto_reply_with_socket(state: AutopilotState) -> dict:
        if socket_notify_fn is not None:
            state = dict(state)
            state["socket_notify_fn"] = socket_notify_fn
        return send_auto_reply(state)

    # Build the graph
    builder = StateGraph(AutopilotState)

    builder.add_node("load_context", load_context)
    builder.add_node("sanitize", sanitize)
    builder.add_node("classify", classify)
    builder.add_node("forward_to_backup", forward_to_backup)
    builder.add_node("compose_response", compose_response)
    builder.add_node("send_auto_reply", _send_auto_reply_with_socket)
    builder.add_node("log_activity", log_activity)

    # Entry point
    builder.set_entry_point("load_context")

    # Conditional edges
    builder.add_conditional_edges(
        "load_context",
        _after_load_context,
        {"sanitize": "sanitize", "log_activity": "log_activity"},
    )
    builder.add_edge("sanitize", "classify")
    builder.add_conditional_edges(
        "classify",
        _after_classify,
        {
            "forward_to_backup": "forward_to_backup",
            "compose_response": "compose_response",
            "log_activity": "log_activity",
        },
    )
    builder.add_conditional_edges(
        "forward_to_backup",
        _after_forward,
        {
            "compose_response": "compose_response",
            "log_activity": "log_activity",
        },
    )
    builder.add_conditional_edges(
        "compose_response",
        _after_compose,
        {"send_auto_reply": "send_auto_reply"},
    )
    builder.add_edge("send_auto_reply", "log_activity")
    builder.add_edge("log_activity", END)

    return builder.compile()
