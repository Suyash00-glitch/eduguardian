"""
Application-level settings loaded from environment variables.
Uses pydantic-settings so all configuration is validated at startup.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Union
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "chatbot/backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    app_name: str = "EduGuardian AI Chatbot Backend"
    app_version: str = "1.0.0"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    cors_origins: Union[list[str], str] = ["http://localhost:5173", "http://localhost:3000"]

    @property
    def allowed_cors_origins(self) -> list[str]:
        if isinstance(self.cors_origins, list):
            return self.cors_origins
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    # ── Database ─────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eduguardian_chatbot"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    # ── LLM Gateway & Direct Groq Configuration ──────────────
    llm_provider: str = "auto"  # "auto" | "groq" | "omniroute"
    omniroute_base_url: str = "http://localhost:20128/v1"
    omniroute_api_key: str = "not-configured"
    omniroute_model: str = "groq/llama-3.3-70b-versatile"
    omniroute_timeout_seconds: float = 3.0

    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"
    groq_timeout_seconds: float = 10.0

    # ── A2A Protocol Endpoints (Independent Agent Services) ───
    student_insight_agent_url: str = "http://localhost:8001"
    study_planner_agent_url: str = "http://localhost:8002"
    recovery_coach_agent_url: str = "http://localhost:8003"
    a2a_timeout_seconds: float = 30.0
    a2a_use_remote_services: bool = True  # Official a2a-sdk HTTP client to agent microservices

    # ── JWT Verification (Auth teammate issues tokens) ───────
    jwt_secret_key: str = "replace-with-shared-jwt-secret"
    jwt_algorithm: str = "HS256"

    # ── Student Context Caching ──────────────────────────────
    student_context_cache_ttl_seconds: int = 3600


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached singleton Settings instance.
    Import and call this wherever you need configuration.
    """
    return Settings()
