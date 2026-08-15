"""
Health check route — GET /health

Liveness and readiness check for EduGuardian AI Chatbot Backend.
Used by load balancers, container orchestrators, and monitoring services.
"""
from __future__ import annotations

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
