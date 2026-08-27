"""
Student Insight Agent - Official a2a-sdk Microservice (Port 8001).
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
from chatbot.backend.a2a.executors import StudentInsightExecutor

import os
from chatbot.backend.config import get_settings

logger = logging.getLogger(__name__)


def get_insight_card() -> AgentCard:
    """Generates the Student Insight AgentCard with dynamic Docker/environment URL resolution."""
    settings = get_settings()
    base_url = (
        os.getenv("A2A_AGENT_URL")
        or os.getenv("STUDENT_INSIGHT_AGENT_URL")
        or settings.student_insight_agent_url
        or "http://localhost:8001"
    ).rstrip("/")
    return AgentCard(
        name="Student Insight Agent",
        description=(
            "Analyzes student academic context internally and produces evidence-based insights "
            "about strengths and focus areas. Results are internal-only; never exposed directly to students."
        ),
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=False),
        supported_interfaces=[
            AgentInterface(url=f"{base_url}/", protocol_binding="JSONRPC"),
            AgentInterface(url=f"{base_url}/", protocol_binding="HTTP+JSON"),
        ],
        skills=[
            AgentSkill(
                id="analyze_academic_context",
                name="Analyze Academic Context",
                description="Evaluates course marks, attendance, and submission trends",
            ),
            AgentSkill(
                id="identify_strengths",
                name="Identify Strengths",
                description="Recognizes subject areas where the student excels",
            ),
            AgentSkill(
                id="identify_focus_areas",
                name="Identify Focus Areas",
                description="Identifies courses and topics needing attention",
            ),
        ],
    )


INSIGHT_CARD = get_insight_card()


def create_insight_service_app() -> FastAPI:
    card = get_insight_card()
    app = FastAPI(
        title="Student Insight Agent Service",
        description="Official a2a-sdk microservice - EduGuardian AI (Port 8001)",
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
            "service": "student_insight",
            "version": "1.0.0",
            "sdk": "a2a-sdk==1.1.2",
        }

    @app.get("/a2a/card")
    @app.get("/.well-known/agent.json")
    async def get_card_legacy() -> dict:
        return MessageToDict(card)

    handler = DefaultRequestHandler(
        agent_executor=StudentInsightExecutor(),
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


app = create_insight_service_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "chatbot.backend.services.insight_service:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
    )
