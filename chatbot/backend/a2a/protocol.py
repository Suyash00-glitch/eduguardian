"""
A2A Protocol — Agent-to-Agent message envelope schemas.

Defines the standard request/response format used for inter-agent communication.
Aligned with the Google A2A protocol conventions:
  - TaskRequest  — sent TO an agent
  - TaskResponse — returned FROM an agent

Phase 1: agents run in-process as LangGraph nodes; A2A protocol layer
         is defined here for correctness and future Phase 2 extraction.
Phase 2: each agent becomes an independent microservice;
         a2a/client.py sends TaskRequests over HTTP.

Reference: https://google.github.io/A2A
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Part(BaseModel):
    """A single content part within a message (text, data, etc.)."""
    type: str = "text"                    # "text" | "data"
    text: str | None = None               # for type="text"
    data: dict[str, Any] | None = None    # for type="data" (structured payloads)


class A2AMessage(BaseModel):
    """A single message in an A2A task exchange."""
    role: str                             # "user" | "agent"
    parts: list[Part]

    @classmethod
    def text(cls, role: str, content: str) -> "A2AMessage":
        """Convenience constructor for plain text messages."""
        return cls(role=role, parts=[Part(type="text", text=content)])


class TaskRequest(BaseModel):
    """
    Message sent TO an agent service.
    Contains the task ID, agent name to invoke, and input payload.
    """
    task_id: UUID = Field(default_factory=uuid4)
    agent_name: str = Field(description="Target agent: 'student_insight' | 'study_planner' | 'recovery_coach'")
    session_id: UUID | None = None
    messages: list[A2AMessage] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary key-value context (e.g. student_id, graph_state snapshot).",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskArtifact(BaseModel):
    """A structured output artifact produced by an agent."""
    name: str
    content_type: str = "application/json"
    data: dict[str, Any]


class TaskResponse(BaseModel):
    """
    Response returned FROM an agent service.
    Always wraps in this envelope regardless of what the agent produced.
    """
    task_id: UUID
    agent_name: str
    status: TaskStatus
    messages: list[A2AMessage] = Field(default_factory=list)
    artifacts: list[TaskArtifact] = Field(default_factory=list)
    error: str | None = None
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def success(
        cls,
        task_id: UUID,
        agent_name: str,
        text_response: str,
        artifacts: list[TaskArtifact] | None = None,
    ) -> "TaskResponse":
        return cls(
            task_id=task_id,
            agent_name=agent_name,
            status=TaskStatus.COMPLETED,
            messages=[A2AMessage.text(role="agent", content=text_response)],
            artifacts=artifacts or [],
        )

    @classmethod
    def failure(
        cls,
        task_id: UUID,
        agent_name: str,
        error: str,
    ) -> "TaskResponse":
        return cls(
            task_id=task_id,
            agent_name=agent_name,
            status=TaskStatus.FAILED,
            error=error,
        )
