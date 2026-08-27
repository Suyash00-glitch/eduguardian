"""
Health check routes — GET /health and GET /health/guardrails

Liveness and readiness check for EduGuardian AI Chatbot Backend.
Used by load balancers, container orchestrators, and monitoring services.

Phase 8.3 addition: /health/guardrails exposes ONLY aggregate guardrail
counters — never raw user messages, StudentContext, or secrets.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel

from chatbot.backend.config import get_settings
from chatbot.backend.db.session import engine

router = APIRouter(tags=["health"])
settings = get_settings()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str


class GuardrailHealthResponse(BaseModel):
    """
    Internal guardrail observability snapshot.

    Contains ONLY aggregate counters.
    No user messages, StudentContext, or secrets are included.
    """
    status: str
    checks: int
    allowed: int
    blocked: int
    rewritten: int
    flagged: int
    categories: dict[str, Any]
    reason_codes: dict[str, int]


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """
    GET /health
    Returns service health, service name, version, and running environment.
    No authentication is required.
    """
    return HealthResponse(
        status="healthy",
        service="eduguardian-chatbot-backend",
        version=settings.app_version,
        environment=settings.app_env,
    )


@router.get(
    "/health/guardrails",
    response_model=GuardrailHealthResponse,
    status_code=status.HTTP_200_OK,
)
async def guardrail_health() -> GuardrailHealthResponse:
    """
    GET /health/guardrails

    Returns aggregate guardrail metrics for internal observability.

    SECURITY: This endpoint exposes ONLY counters and category breakdowns.
    It never returns user messages, StudentContext data, LearningHistory,
    secrets, API keys, or any personally-identifiable information.
    """
    # Import here to avoid circular imports at module load time
    from chatbot.backend.guardrails.metrics import GuardrailMetrics

    snap = GuardrailMetrics.snapshot()
    return GuardrailHealthResponse(
        status="healthy",
        checks=snap["total_checks"],
        allowed=snap["allowed"],
        blocked=snap["blocked"],
        rewritten=snap["rewritten"],
        flagged=snap["flagged"],
        categories=snap["by_category"],
        reason_codes=snap["by_reason_code"],
    )
