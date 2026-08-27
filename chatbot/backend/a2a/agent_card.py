"""
AgentCard — A2A Capability & Metadata Declaration.

Describes each agent's identity, supported capabilities, endpoints, and input/output contracts.
Exposed via `GET /.well-known/agent.json` and `GET /a2a/card`.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from chatbot.backend.config import get_settings


class AgentCapability(BaseModel):
    """A named skill/capability exposed by an agent."""
    name: str = Field(description="Unique capability name")
    description: str = Field(description="Description of what this capability does")


class AgentCard(BaseModel):
    """
    Standard A2A Agent Card model.

    Describes an agent's identity, endpoints, protocol capabilities, and input/output schemas.
    """
    agent_id: str = Field(description="Unique identifier for the agent (e.g. 'student_insight')")
    display_name: str = Field(description="Human-readable title")
    description: str = Field(description="Comprehensive explanation of agent role")
    version: str = Field(default="1.0.0", description="Semantic version string")
    endpoint_url: str = Field(description="A2A HTTP task endpoint URL (e.g. 'http://localhost:8001/a2a/task')")
    health_url: str = Field(default="", description="Health check endpoint URL")
    capabilities: list[AgentCapability] = Field(default_factory=list)
    input_schema: str = Field(description="Pydantic contract for input task payload")
    output_schema: str = Field(description="Pydantic contract for output task payload")
    student_facing: bool = Field(default=False, description="True if agent directly interacts with students")
    metadata: dict[str, Any] = Field(default_factory=dict)


def get_agent_card(agent_id: str) -> AgentCard:
    """Returns the AgentCard for a given agent_id with dynamic URL resolution from config."""
    settings = get_settings()

    if agent_id == "student_insight":
        base_url = settings.student_insight_agent_url or "http://localhost:8001"
        return AgentCard(
            agent_id="student_insight",
            display_name="Student Insight Agent",
            description="Analyzes structured student academic context and produces internal academic insights.",
            version="1.0.0",
            endpoint_url=f"{base_url.rstrip('/')}/a2a/task",
            health_url=f"{base_url.rstrip('/')}/health",
            capabilities=[
                AgentCapability(name="analyze_academic_context", description="Evaluates course marks, attendance, and submission trends"),
                AgentCapability(name="identify_strengths", description="Recognizes areas where student excels"),
                AgentCapability(name="identify_focus_areas", description="Identifies courses and topics needing practice"),
            ],
            input_schema="InsightRequest",
            output_schema="StudentInsight",
            student_facing=False,
        )
    elif agent_id == "study_planner":
        base_url = settings.study_planner_agent_url or "http://localhost:8002"
        return AgentCard(
            agent_id="study_planner",
            display_name="Study Planner Agent",
            description="Creates personalized study plans from student context, insights and planning requests.",
            version="1.0.0",
            endpoint_url=f"{base_url.rstrip('/')}/a2a/task",
            health_url=f"{base_url.rstrip('/')}/health",
            capabilities=[
                AgentCapability(name="create_weekly_plan", description="Schedules actionable study tasks across days"),
                AgentCapability(name="prioritize_deadlines", description="Prioritizes urgent submissions and assignments"),
                AgentCapability(name="time_budgeting", description="Respects daily student time limits"),
            ],
            input_schema="PlanRequest",
            output_schema="StudyPlan",
            student_facing=False,
        )
    elif agent_id == "recovery_coach":
        base_url = settings.recovery_coach_agent_url or "http://localhost:8003"
        return AgentCard(
            agent_id="recovery_coach",
            display_name="Recovery Coach Agent",
            description="Provides supportive student-facing academic guidance using available context, insights and study plans.",
            version="1.0.0",
            endpoint_url=f"{base_url.rstrip('/')}/a2a/task",
            health_url=f"{base_url.rstrip('/')}/health",
            capabilities=[
                AgentCapability(name="supportive_dialogue", description="Employs non-judgmental, encouraging conversational guidance"),
                AgentCapability(name="present_study_plan", description="Introduces structured plans naturally in friendly language"),
                AgentCapability(name="motivation_coaching", description="Helps students overcome academic stress"),
            ],
            input_schema="CoachRequest",
            output_schema="CoachResponse",
            student_facing=True,
        )
    else:
        raise ValueError(f"Unknown agent_id '{agent_id}'")


STUDENT_INSIGHT_CARD = get_agent_card("student_insight")
STUDY_PLANNER_CARD = get_agent_card("study_planner")
RECOVERY_COACH_CARD = get_agent_card("recovery_coach")

AGENT_REGISTRY: dict[str, AgentCard] = {
    "student_insight": STUDENT_INSIGHT_CARD,
    "study_planner": STUDY_PLANNER_CARD,
    "recovery_coach": RECOVERY_COACH_CARD,
}
