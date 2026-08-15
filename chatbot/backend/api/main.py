"""
FastAPI application factory.

Chatbot backend entrypoint.
Run with: uvicorn chatbot.backend.api.main:app --reload --port 8000
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chatbot.backend.api.error_handlers import register_error_handlers
from chatbot.backend.api.routes.chat import router as chat_router
from chatbot.backend.api.routes.health import router as health_router
from chatbot.backend.config import get_settings
from chatbot.backend.core.logging import setup_logging
from chatbot.backend.db.session import engine, init_db
from chatbot.backend.db.models import *  # noqa: F401,F403 — ensures models are registered

settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


# ── Lifespan context manager ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s in [%s] mode...", settings.app_name, settings.app_version, settings.app_env)
    await init_db()
    yield
    logger.info("Shutting down %s...", settings.app_name)
    await engine.dispose()


# ── App factory ───────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    application = FastAPI(
        title="EduGuardian AI — Chatbot API",
        description=(
            "AI-powered student support chatbot backend. "
            "Provides academic coaching through internal agents: "
            "Student Insight, Study Planner, and Recovery Coach."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS Middleware ───────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
        allow_headers=["*"],
    )

    # ── Global Error Handlers ─────────────────────────────────────────────────
    register_error_handlers(application)

    # ── Route Registration ────────────────────────────────────────────────────
    application.include_router(health_router)
    application.include_router(chat_router, prefix="/api")
    application.include_router(chat_router, prefix="/api/v1")

    return application


app = create_app()
