"""
Recovery Coach Agent - Official a2a-sdk Microservice (Port 8003).
"""
from __future__ import annotations
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.protobuf.json_format import MessageToDict
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
    create_rest_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill, AgentInterface
from chatbot.backend.a2a.executors import RecoveryCoachExecutor

import os
from chatbot.backend.config import get_settings

logger = logging.getLogger(__name__)


def get_coach_card() -> AgentCard:
    """Generates the Recovery Coach AgentCard with dynamic Docker/environment URL resolution."""
    settings = get_settings()
    base_url = (
        os.getenv("A2A_AGENT_URL")
        or os.getenv("RECOVERY_COACH_AGENT_URL")
        or settings.recovery_coach_agent_url
        or "http://localhost:8003"
    ).rstrip("/")
    return AgentCard(
        name="Recovery Coach Agent",
        description=(
            "Provides supportive, personalized student-facing academic guidance. "
            "Converts internal insights into encouraging conversational responses. "
            "Never exposes risk labels, scores, or judgmental language to students."
        ),
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=False),
        supported_interfaces=[
            AgentInterface(url=f"{base_url}/", protocol_binding="JSONRPC"),
            AgentInterface(url=f"{base_url}/", protocol_binding="HTTP+JSON"),
        ],
        skills=[
            AgentSkill(
                id="supportive_dialogue",
                name="Supportive Dialogue",
                description="Non-judgmental, encouraging conversational guidance for students",
            ),
            AgentSkill(
                id="present_study_plan",
                name="Present Study Plan",
                description="Introduces structured plans naturally in friendly language",
            ),
            AgentSkill(
                id="motivation_coaching",
                name="Motivation Coaching",
                description="Helps students overcome academic stress and build confidence",
            ),
        ],
    )


COACH_CARD = get_coach_card()


def create_coach_service_app() -> FastAPI:
    card = get_coach_card()
    app = FastAPI(
        title="Recovery Coach Agent Service",
        description="Official a2a-sdk microservice - EduGuardian AI (Port 8003)",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict:
        return {
            "status": "healthy",
            "service": "recovery_coach",
            "version": "1.0.0",
            "sdk": "a2a-sdk==1.1.2",
        }

    @app.get("/a2a/card")
    @app.get("/.well-known/agent.json")
    async def get_card_legacy() -> dict:
        return MessageToDict(card)

    handler = DefaultRequestHandler(
        agent_executor=RecoveryCoachExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(card),
        jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/"),
        rest_routes=create_rest_routes(handler),
    )
    return app


app = create_coach_service_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "chatbot.backend.services.coach_service:app",
        host="0.0.0.0",
        port=8003,
        reload=False,
    )
