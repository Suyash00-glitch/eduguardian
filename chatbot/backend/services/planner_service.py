"""
Study Planner Agent - Official a2a-sdk Microservice (Port 8002).
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
from chatbot.backend.a2a.executors import StudyPlannerExecutor

import os
from chatbot.backend.config import get_settings

logger = logging.getLogger(__name__)


def get_planner_card() -> AgentCard:
    """Generates the Study Planner AgentCard with dynamic Docker/environment URL resolution."""
    settings = get_settings()
    base_url = (
        os.getenv("A2A_AGENT_URL")
        or os.getenv("STUDY_PLANNER_AGENT_URL")
        or settings.study_planner_agent_url
        or "http://localhost:8002"
    ).rstrip("/")
    return AgentCard(
        name="Study Planner Agent",
        description=(
            "Creates personalized, structured study schedules from student context, "
            "academic insights, and planning requests."
        ),
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=False),
        supported_interfaces=[
            AgentInterface(url=f"{base_url}/", protocol_binding="JSONRPC"),
            AgentInterface(url=f"{base_url}/", protocol_binding="HTTP+JSON"),
        ],
        skills=[
            AgentSkill(
                id="create_weekly_plan",
                name="Create Weekly Plan",
                description="Schedules actionable study tasks across days of the week",
            ),
            AgentSkill(
                id="prioritize_deadlines",
                name="Prioritize Deadlines",
                description="Prioritizes upcoming submissions and assessments by urgency",
            ),
            AgentSkill(
                id="time_budgeting",
                name="Time Budgeting",
                description="Respects the student daily available study time",
            ),
        ],
    )


PLANNER_CARD = get_planner_card()


def create_planner_service_app() -> FastAPI:
    card = get_planner_card()
    app = FastAPI(
        title="Study Planner Agent Service",
        description="Official a2a-sdk microservice - EduGuardian AI (Port 8002)",
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
            "service": "study_planner",
            "version": "1.0.0",
            "sdk": "a2a-sdk==1.1.2",
        }

    @app.get("/a2a/card")
    @app.get("/.well-known/agent.json")
    async def get_card_legacy() -> dict:
        return MessageToDict(card)

    handler = DefaultRequestHandler(
        agent_executor=StudyPlannerExecutor(),
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


app = create_planner_service_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "chatbot.backend.services.planner_service:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
    )
