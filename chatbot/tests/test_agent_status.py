import pytest
import json
from chatbot.backend.orchestrator.agent_status import (
    AGENT_STATUS_REGISTRY,
    get_agent_metadata,
    create_agent_status_event,
    FALLBACK_STATUS,
)
from chatbot.backend.orchestrator.graph import run_graph_with_events
from chatbot.backend.orchestrator.state import GraphState


def test_agent_status_registry_mappings():
    """Verify that all orchestrator nodes map to safe, student-friendly descriptions."""
    expected_nodes = [
        "prepare_context",
        "request_processor",
        "student_insight",
        "study_planner",
        "recovery_coach",
        "response_validator",
    ]
    for node in expected_nodes:
        meta = get_agent_metadata(node)
        assert "display_name" in meta
        assert "message" in meta
        assert "icon" in meta
        assert "agent" in meta
        # Ensure no private/chain-of-thought leaked
        assert "thought" not in meta["message"].lower()
        assert "prompt" not in meta["message"].lower()
        assert "tool" not in meta["message"].lower()


def test_create_agent_status_event_working():
    """Verify working event generation."""
    event = create_agent_status_event("student_insight", status="working")
    assert event["type"] == "agent_status"
    assert event["agent"] == "performance_analyst"
    assert event["display_name"] == "Performance Analyst"
    assert event["status"] == "working"
    assert "Analyzing" in event["message"]
    assert event["icon"] == "📊"


def test_create_agent_status_event_complete():
    """Verify complete event generation."""
    event = create_agent_status_event("student_insight", status="complete")
    assert event["type"] == "agent_status"
    assert event["agent"] == "performance_analyst"
    assert event["status"] == "complete"


def test_fallback_status_for_unknown_node():
    """Verify fallback behavior for unknown or unmapped nodes."""
    event = create_agent_status_event("unknown_custom_node", status="working")
    assert event["type"] == "agent_status"
    assert event["agent"] == "general_assistant"
    assert event["display_name"] == "EduGuardian"
    assert event["message"] == "EduGuardian is preparing your response..."


@pytest.mark.asyncio
async def test_run_graph_with_events_yields_real_agent_lifecycle():
    """
    Verify that run_graph_with_events yields status events for actual agents
    executed during a study plan turn.
    """
    state: GraphState = {
        "student_id": "NNM24IS127",
        "user_message": "Make me a study plan for data structures",
        "conversation_id": "test-conv-1",
        "student_context": None,
        "conversation_history": [],
        "teaching_state": None,
        "quiz_state": None,
        "learning_history": None,
        "insight_response": None,
        "plan_response": None,
        "final_response": None,
        "agents_used": [],
        "intent": "general_support",
        "response_mode": None,
        "conversational_name": None,
        "user_facts": None,
        "processed_request": None,
        "constraints": None,
    }

    events = []
    final_state = None
    async for kind, payload in run_graph_with_events(state):
        if kind == "status":
            events.append(payload)
        elif kind == "final_state":
            final_state = payload

    assert len(events) >= 3, f"Expected at least 3 agent status events, got {len(events)}"
    agents_reported = [e["agent"] for e in events]
    
    # Must contain real agents used
    assert "academic_advisor" in agents_reported
    assert "recovery_coach" in agents_reported
    assert final_state is not None
    assert final_state.get("final_response") is not None
