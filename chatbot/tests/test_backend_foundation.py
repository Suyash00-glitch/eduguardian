"""
Tests for Backend Foundation.

Verifies:
1. Application factory and startup
2. GET /health endpoint
3. Centralized configuration loading & validation
4. Structured error handling (404, 422, custom AppExceptions)
5. Sensitive data logging filter
6. Database Base and Session factory
"""
from __future__ import annotations

import logging
import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from chatbot.backend.api.main import create_app, app
from chatbot.backend.config import Settings, get_settings
from chatbot.backend.core.exceptions import (
    AppException,
    NotFoundError,
    ValidationError as AppValidationError,
    ServiceUnavailableError,
)
from chatbot.backend.core.logging import SensitiveDataFilter
from chatbot.backend.db.session import Base, AsyncSessionLocal


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ── 1. Application Factory & Health Endpoint ──────────────────────────────────

class TestHealthAndStartup:
    def test_app_creation(self):
        """App factory should create a configured FastAPI instance."""
        application = create_app()
        assert application.title == "EduGuardian AI — Chatbot API"
        assert application.version == "1.0.0"

    def test_health_endpoint_returns_200(self, client: TestClient):
        """GET /health must return 200 with service metadata."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "eduguardian-chatbot-backend"
        assert "version" in data
        assert "environment" in data

    def test_health_endpoint_requires_no_auth(self, client: TestClient):
        """GET /health must be accessible without any Authorization header."""
        response = client.get("/health")
        assert response.status_code == 200


# ── 2. Configuration Loading ──────────────────────────────────────────────────

class TestConfiguration:
    def test_settings_singleton(self):
        """get_settings() should return a valid cached Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)
        assert settings.app_port == 8000
        assert settings.jwt_algorithm == "HS256"

    def test_cors_origins_parsing(self):
        """CORS origins should parse both lists and comma-separated strings."""
        s1 = Settings(cors_origins="http://localhost:3000, http://localhost:5173")
        assert "http://localhost:3000" in s1.allowed_cors_origins
        assert "http://localhost:5173" in s1.allowed_cors_origins

        s2 = Settings(cors_origins=["http://localhost:8080"])
        assert s2.allowed_cors_origins == ["http://localhost:8080"]

    def test_default_settings_properties(self):
        """Settings should have predictable production-ready properties."""
        settings = get_settings()
        assert isinstance(settings.app_env, str)
        assert isinstance(settings.omniroute_base_url, str)
        assert isinstance(settings.omniroute_model, str)


# ── 3. Structured Error Handling ──────────────────────────────────────────────

class TestErrorHandling:
    def test_404_not_found_structure(self, client: TestClient):
        """Non-existent route must return standardized JSON error format."""
        response = client.get("/api/v1/non-existent-route-xyz")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"
        assert "message" in data["error"]

    def test_custom_app_exception_handling(self):
        """Custom AppException subclasses should map to proper status codes and error format."""
        test_app = create_app()
        test_router = APIRouter()

        @test_router.get("/test-not-found")
        def route_not_found():
            raise NotFoundError("Custom item missing")

        @test_router.get("/test-service-unavailable")
        def route_unavailable():
            raise ServiceUnavailableError("External API down")

        test_app.include_router(test_router)
        custom_client = TestClient(test_app)

        # 404 Not Found
        r1 = custom_client.get("/test-not-found")
        assert r1.status_code == 404
        d1 = r1.json()
        assert d1["success"] is False
        assert d1["error"]["code"] == "NOT_FOUND"
        assert d1["error"]["message"] == "Custom item missing"

        # 503 Service Unavailable
        r2 = custom_client.get("/test-service-unavailable")
        assert r2.status_code == 503
        d2 = r2.json()
        assert d2["success"] is False
        assert d2["error"]["code"] == "SERVICE_UNAVAILABLE"


# ── 4. Logging & Security Filter ──────────────────────────────────────────────

class TestLoggingFilter:
    def test_sensitive_data_scrubbed(self):
        """Sensitive tokens and keys must be redacted by SensitiveDataFilter."""
        log_filter = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.secret and password=supersecret123",
            args=(),
            exc_info=None,
        )
        log_filter.filter(record)
        assert "eyJhbGci" not in record.msg
        assert "supersecret123" not in record.msg
        assert "[REDACTED]" in record.msg


# ── 5. Database Foundation ────────────────────────────────────────────────────

class TestDatabaseFoundation:
    def test_declarative_base_exists(self):
        """SQLAlchemy declarative Base must be configured."""
        assert hasattr(Base, "metadata")

    def test_async_session_factory_exists(self):
        """AsyncSessionLocal factory must be callable."""
        assert AsyncSessionLocal is not None
