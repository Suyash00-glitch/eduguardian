"""
Official a2a-sdk Agent Executors for EduGuardian AI Chatbot.

Each executor wraps the existing agent business logic class and adapts it
to the official a2a-sdk AgentExecutor interface.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    Message,
    Part,
    Role,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)

logger = logging.getLogger(__name__)


def _extract_payload(context: RequestContext) -> dict | None:
    if context.metadata:
        p = context.metadata.get("payload")
        if p:
            return p
    if context.message and context.message.parts:
        for part in context.message.parts:
            if part.HasField("text") and part.text:
                try:
                    return json.loads(part.text)
                except (json.JSONDecodeError, ValueError):
                    pass
    return None


async def _reply_message(event_queue: EventQueue, json_str: str) -> None:
    """Enqueues a single response Message event into the official SDK event queue."""
    msg = Message(
        message_id=str(uuid.uuid4()),
        role=Role.ROLE_AGENT,
        parts=[Part(text=json_str)],
    )
    await event_queue.enqueue_event(msg)


class StudentInsightExecutor(AgentExecutor):
    """Official a2a-sdk executor for Student Insight Agent."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        from chatbot.backend.agents.student_insight.agent import StudentInsightAgent
        from chatbot.backend.schemas.insight import InsightRequest

        logger.info("StudentInsightExecutor: handling task_id=%s context_id=%s", context.task_id, context.context_id)
        try:
            raw = _extract_payload(context)
            if not raw:
                raise ValueError("Missing InsightRequest payload")
            req = InsightRequest.model_validate(raw)
            result = await StudentInsightAgent().analyze_async(req)
            await _reply_message(event_queue, result.model_dump_json())
        except Exception as exc:
            logger.error("StudentInsightExecutor failed: %s", exc, exc_info=True)
            err_msg = Message(
                message_id=str(uuid.uuid4()),
                role=Role.ROLE_AGENT,
                parts=[Part(text=json.dumps({"error": str(exc)}))],
            )
            await event_queue.enqueue_event(err_msg)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass


class StudyPlannerExecutor(AgentExecutor):
    """Official a2a-sdk executor for Study Planner Agent."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        from chatbot.backend.agents.study_planner.agent import StudyPlannerAgent
        from chatbot.backend.schemas.planner import PlanRequest

        logger.info("StudyPlannerExecutor: handling task_id=%s context_id=%s", context.task_id, context.context_id)
        try:
            raw = _extract_payload(context)
            if not raw:
                raise ValueError("Missing PlanRequest payload")
            req = PlanRequest.model_validate(raw)
            result = await StudyPlannerAgent().create_plan_async(req)
            await _reply_message(event_queue, result.model_dump_json())
        except Exception as exc:
            logger.error("StudyPlannerExecutor failed: %s", exc, exc_info=True)
            err_msg = Message(
                message_id=str(uuid.uuid4()),
                role=Role.ROLE_AGENT,
                parts=[Part(text=json.dumps({"error": str(exc)}))],
            )
            await event_queue.enqueue_event(err_msg)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass


class RecoveryCoachExecutor(AgentExecutor):
    """Official a2a-sdk executor for Recovery Coach Agent."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        from chatbot.backend.agents.recovery_coach.agent import RecoveryCoachAgent
        from chatbot.backend.schemas.coach import CoachRequest

        logger.info("RecoveryCoachExecutor: handling task_id=%s context_id=%s", context.task_id, context.context_id)
        try:
            raw = _extract_payload(context)
            if not raw:
                msg_text = ""
                if context.message and context.message.parts:
                    for part in context.message.parts:
                        if part.HasField("text") and part.text:
                            msg_text = part.text
                            break
                sid = (context.metadata or {}).get("student_id", "student_001")
                raw = {"student_id": sid, "user_message": msg_text or "Hello"}
            req = CoachRequest.model_validate(raw)
            result = await RecoveryCoachAgent().generate_response(req)
            await _reply_message(event_queue, result.model_dump_json())
        except Exception as exc:
            logger.error("RecoveryCoachExecutor failed: %s", exc, exc_info=True)
            err_msg = Message(
                message_id=str(uuid.uuid4()),
                role=Role.ROLE_AGENT,
                parts=[Part(text=json.dumps({"error": str(exc)}))],
            )
            await event_queue.enqueue_event(err_msg)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass
