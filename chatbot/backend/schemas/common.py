"""
Common API response and error schemas.
Ensures consistent JSON response format across the entire backend.
"""
from __future__ import annotations

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Structured error payload returned inside ErrorResponse."""
    code: str = Field(description="Machine-readable error code, e.g. 'NOT_FOUND', 'VALIDATION_ERROR'")
    message: str = Field(description="Human-readable safe error message")
    details: Any | None = Field(default=None, description="Optional extra error context (e.g. field errors)")


class ErrorResponse(BaseModel):
    """Standardized error envelope."""
    success: bool = False
    error: ErrorDetail


class ApiResponse(BaseModel, Generic[T]):
    """Standardized success response envelope."""
    success: bool = True
    data: T | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
