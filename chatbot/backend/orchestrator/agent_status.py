"""
Agent Status Registry & Safe Event Dispatcher
==============================================
Provides centralized mapping between internal orchestrator nodes / agents
and safe, high-level, student-friendly status descriptions.

Guarantees:
- NEVER exposes private reasoning, chain-of-thought, internal prompts, or tool arguments.
- Exposes only the active agent identity, display name, user-friendly activity message, and status.
"""
from __future__ import annotations

from typing import Any, Dict


AGENT_STATUS_REGISTRY: Dict[str, Dict[str, str]] = {
    "prepare_context": {
        "agent": "academic_advisor",
        "display_name": "Academic Advisor",
        "message": "Reviewing your academic profile...",
        "icon": "🎓",
    },
    "request_processor": {
        "agent": "academic_advisor",
        "display_name": "Academic Advisor",
        "message": "Understanding your academic request...",
        "icon": "🎓",
    },
    "student_insight": {
        "agent": "performance_analyst",
        "display_name": "Performance Analyst",
        "message": "Analyzing your academic performance & records...",
        "icon": "📊",
    },
    "study_planner": {
        "agent": "study_planner",
        "display_name": "Study Planner",
        "message": "Creating a personalized study plan & schedule...",
        "icon": "📚",
    },
    "recovery_coach": {
        "agent": "recovery_coach",
        "display_name": "Academic Coach",
        "message": "Preparing your personalized guidance...",
        "icon": "✨",
    },
    "response_validator": {
        "agent": "general_assistant",
        "display_name": "EduGuardian",
        "message": "Finalizing your response...",
        "icon": "🛡️",
    },
}

FALLBACK_STATUS: Dict[str, str] = {
    "agent": "general_assistant",
    "display_name": "EduGuardian",
    "message": "EduGuardian is preparing your response...",
    "icon": "✨",
}


def get_agent_metadata(node_name: str) -> Dict[str, str]:
    """Retrieves safe metadata for an orchestrator node or agent name."""
    return AGENT_STATUS_REGISTRY.get(node_name, FALLBACK_STATUS)


def create_agent_status_event(
    node_name: str,
    status: str = "working",
    custom_message: str | None = None,
) -> Dict[str, Any]:
    """
    Constructs a safe, high-level agent status event payload.
    
    Example payload:
    {
        "type": "agent_status",
        "agent": "performance_analyst",
        "display_name": "Performance Analyst",
        "status": "working",
        "message": "Analyzing your academic performance & records...",
        "icon": "📊"
    }
    """
    meta = get_agent_metadata(node_name)
    event = {
        "type": "agent_status",
        "agent": meta["agent"],
        "display_name": meta["display_name"],
        "status": status,
        "icon": meta.get("icon", "✨"),
    }
    if status == "working":
        event["message"] = custom_message or meta["message"]
    return event
