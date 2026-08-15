"""
Official a2a-sdk integration package for EduGuardian AI Chatbot.
"""
from chatbot.backend.a2a.executors import (
    StudentInsightExecutor,
    StudyPlannerExecutor,
    RecoveryCoachExecutor,
)
from chatbot.backend.a2a.client import (
    StudentInsightA2AClient,
    StudyPlannerA2AClient,
    RecoveryCoachA2AClient,
)

__all__ = [
    "StudentInsightExecutor",
    "StudyPlannerExecutor",
    "RecoveryCoachExecutor",
    "StudentInsightA2AClient",
    "StudyPlannerA2AClient",
    "RecoveryCoachA2AClient",
]
