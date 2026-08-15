"""
Application exception hierarchy for EduGuardian AI Chatbot.
"""
from __future__ import annotations

from typing import Any


class AppException(Exception):
    """Base application exception."""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", details: Any | None = None) -> None:
        super().__init__(message=message, code="NOT_FOUND", status_code=404, details=details)


class ValidationError(AppException):
    def __init__(self, message: str = "Validation failed", details: Any | None = None) -> None:
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422, details=details)


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication required or invalid", details: Any | None = None) -> None:
        super().__init__(message=message, code="UNAUTHORIZED", status_code=401, details=details)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Access forbidden", details: Any | None = None) -> None:
        super().__init__(message=message, code="FORBIDDEN", status_code=403, details=details)


class DatabaseError(AppException):
    def __init__(self, message: str = "Database operation failed", details: Any | None = None) -> None:
        super().__init__(message=message, code="DATABASE_ERROR", status_code=500, details=details)


class ServiceUnavailableError(AppException):
    def __init__(self, message: str = "External service is currently unavailable", details: Any | None = None) -> None:
        super().__init__(message=message, code="SERVICE_UNAVAILABLE", status_code=503, details=details)
