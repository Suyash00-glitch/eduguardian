"""
A2A Client Layer - Official a2a-sdk Client Wrappers.

Uses the official a2a-sdk Client to communicate with the three independent
agent microservices over the A2A protocol (JSON-RPC 2.0 over HTTP).

The LangGraph orchestrator uses these clients when a2a_use_remote_services=True.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import httpx
from a2a.client import ClientConfig, create_client
from a2a.types import (
    Message,
    Part,
    Role,
    SendMessageRequest,
    SendMessageConfiguration,
)

from chatbot.backend.config import get_settings
from chatbot.backend.schemas.insight import InsightRequest, StudentInsight
from chatbot.backend.schemas.planner import PlanRequest, StudyPlan
from chatbot.backend.schemas.coach import CoachRequest, CoachResponse

logger = logging.getLogger(__name__)


def _build_request(payload: dict) -> SendMessageRequest:
    """Builds a valid official a2a-sdk SendMessageRequest with required message_id."""
    return SendMessageRequest(
        message=Message(
            message_id=str(uuid.uuid4()),
            role=Role.ROLE_USER,
            parts=[Part(text=json.dumps(payload))],
        )
    )


async def _send_and_extract(base_url: str, payload: dict) -> str:
    """
    Creates an official a2a-sdk client from the agent URL, sends the request
    over JSON-RPC 2.0 HTTP, and extracts the resulting text response.
    """
    settings = get_settings()
    timeout = settings.a2a_timeout_seconds
    url = base_url.rstrip("/")

    logger.info("A2A official SDK client: connecting to %s", url)
    custom_http = httpx.AsyncClient(timeout=timeout)
    client_config = ClientConfig(httpx_client=custom_http)
    client = await create_client(
        url,
        client_config=client_config,
        resolver_http_kwargs={"timeout": timeout},
    )
    request = _build_request(payload)

    try:
        async for response in client.send_message(request):
            if response.HasField("message"):
                for part in response.message.parts:
                    if part.HasField("text") and part.text:
                        logger.info("A2A official SDK: response received from %s (length=%d)", url, len(part.text))
                        return part.text
            elif response.HasField("status_update"):
                logger.debug("A2A official SDK: status update from %s: %s", url, response.status_update)
    finally:
        if hasattr(client, "close"):
            await client.close()

    raise RuntimeError(f"A2A official SDK client: no text response received from {url}")


class StudentInsightA2AClient:
    """Official a2a-sdk client for the Student Insight Agent (:8001)."""

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = (settings.student_insight_agent_url or "http://localhost:8001").rstrip("/")

    async def analyze(self, request: InsightRequest) -> StudentInsight:
        payload = request.model_dump(mode="json")
        raw = await _send_and_extract(self._base_url, payload)
        data = json.loads(raw)
        if "error" in data:
            raise RuntimeError(f"StudentInsight remote agent error: {data['error']}")
        return StudentInsight.model_validate(data)


class StudyPlannerA2AClient:
    """Official a2a-sdk client for the Study Planner Agent (:8002)."""

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = (settings.study_planner_agent_url or "http://localhost:8002").rstrip("/")

    async def create_plan(self, request: PlanRequest) -> StudyPlan:
        payload = request.model_dump(mode="json")
        raw = await _send_and_extract(self._base_url, payload)
        data = json.loads(raw)
        if "error" in data:
            raise RuntimeError(f"StudyPlanner remote agent error: {data['error']}")
        return StudyPlan.model_validate(data)


class RecoveryCoachA2AClient:
    """Official a2a-sdk client for the Recovery Coach Agent (:8003)."""

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = (settings.recovery_coach_agent_url or "http://localhost:8003").rstrip("/")

    async def generate_response(self, request: CoachRequest) -> CoachResponse:
        payload = request.model_dump(mode="json")
        raw = await _send_and_extract(self._base_url, payload)
        data = json.loads(raw)
        if "error" in data:
            raise RuntimeError(f"RecoveryCoach remote agent error: {data['error']}")
        return CoachResponse.model_validate(data)
