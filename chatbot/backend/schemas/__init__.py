"""
Shared Data Contracts & Schemas Index.

Exports all data contracts for the EduGuardian AI Chatbot system:
- Student Context & Academic Records
- Student Insight Agent Contracts
- Study Planner Agent Contracts
- Recovery Coach Agent Contracts
- Chat & Conversation Contracts
- Intent & Routing Contracts
- LangGraph ChatState Contracts
- A2A Inter-Agent Contracts
- Frontend Client Contracts
- Common API & Error Envelopes
"""
from __future__ import annotations

from chatbot.backend.schemas.common import (
    ApiResponse,
    ErrorDetail,
    ErrorResponse,
)
from chatbot.backend.schemas.student import (
    AssessmentSummary,
    AssignmentSummary,
    AttendanceSummary,
    AttendanceTrend,
    EngagementSummary,
    InterventionHistory,
    StudentContext,
    SubjectPerformance,
    TrendInformation,
)
from chatbot.backend.schemas.insight import (
    InsightRequest,
    StudentInsight,
    SubjectInsight,
)
from chatbot.backend.schemas.planner import (
    PlanMilestone,
    PlanRequest,
    PriorityLevel,
    StudyPlan,
    StudyTask,
)
from chatbot.backend.schemas.coach import (
    CoachMessageItem,
    CoachRequest,
    CoachResponse,
)
from chatbot.backend.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ConversationHistory,
    ConversationHistoryResponse,
    MessageRole,
    MessageSchema,
)
from chatbot.backend.schemas.routing import (
    IntentClassification,
    IntentType,
)
from chatbot.backend.schemas.state import (
    ChatState,
    ChatStateModel,
)
from chatbot.backend.schemas.a2a import (
    A2AAgentRole,
    A2AResultEnvelope,
    A2ATaskEnvelope,
    A2ATaskType,
    CoachTaskPayload,
    InsightTaskPayload,
    PlannerTaskPayload,
)
from chatbot.backend.schemas.frontend import (
    FrontendChatResponse,
    FrontendMessage,
)

__all__ = [
    # Common
    "ApiResponse",
    "ErrorDetail",
    "ErrorResponse",
    # Student Context
    "AttendanceTrend",
    "AttendanceSummary",
    "SubjectPerformance",
    "AssignmentSummary",
    "AssessmentSummary",
    "EngagementSummary",
    "TrendInformation",
    "InterventionHistory",
    "StudentContext",
    # Student Insight
    "SubjectInsight",
    "InsightRequest",
    "StudentInsight",
    # Study Planner
    "PriorityLevel",
    "StudyTask",
    "PlanMilestone",
    "PlanRequest",
    "StudyPlan",
    # Recovery Coach
    "CoachMessageItem",
    "CoachRequest",
    "CoachResponse",
    # Chat & API
    "MessageRole",
    "ChatMessage",
    "ConversationHistory",
    "ChatRequest",
    "MessageSchema",
    "ChatResponse",
    "ConversationHistoryResponse",
    # Intent & Routing
    "IntentType",
    "IntentClassification",
    # LangGraph State
    "ChatState",
    "ChatStateModel",
    # A2A
    "A2AAgentRole",
    "A2ATaskType",
    "InsightTaskPayload",
    "PlannerTaskPayload",
    "CoachTaskPayload",
    "A2ATaskEnvelope",
    "A2AResultEnvelope",
    # Frontend
    "FrontendMessage",
    "FrontendChatResponse",
]
