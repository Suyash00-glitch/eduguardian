"""
FastAPI dependency providers.

JWT stub:
  get_current_student_id() reads a Bearer token from the Authorization header.
  It validates the token's structure (decode with the shared JWT secret).
  The actual token is ISSUED by the auth teammate's service — we only VERIFY it.

  When the auth teammate is ready:
    1. They share the JWT_SECRET_KEY (or provide a JWKS URL for RS256).
    2. Update the token_data extraction to match their claims structure.
    3. No other changes needed in the chatbot component.
"""
from __future__ import annotations

from typing import AsyncGenerator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from chatbot.backend.config import get_settings
from chatbot.backend.db.session import AsyncSessionLocal
from chatbot.backend.db.repositories.conversation import ConversationRepository
from chatbot.backend.db.repositories.student_context import StudentContextRepository
from chatbot.backend.services.chat_service import ChatService

settings = get_settings()
_bearer_scheme = HTTPBearer(auto_error=False)


# ── Database ──────────────────────────────────────────────────────────────────

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: provides a managed async DB session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_conversation_repo(
    session: AsyncSession = Depends(get_db_session),
) -> ConversationRepository:
    return ConversationRepository(session)


_context_repo_singleton: StudentContextRepository | None = None


def get_student_context_repo() -> StudentContextRepository:
    """Provides a shared singleton StudentContextRepository with server-side TTL caching."""
    global _context_repo_singleton
    if _context_repo_singleton is None:
        settings = get_settings()
        _context_repo_singleton = StudentContextRepository(
            ttl_seconds=settings.student_context_cache_ttl_seconds
        )
    return _context_repo_singleton


def get_chat_service(
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
    context_repo: StudentContextRepository = Depends(get_student_context_repo),
) -> ChatService:
    return ChatService(conv_repo=conv_repo, context_repo=context_repo)


# ── JWT Authentication stub ───────────────────────────────────────────────────

async def get_current_student_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    """
    Dependency that extracts and validates the student's JWT Bearer token.

    Expects header: Authorization: Bearer <token>

    The token must be a valid JWT signed with JWT_SECRET_KEY (HS256).
    The payload must contain a 'sub' claim with the student_id.

    ╔══════════════════════════════════════════════════════════════════╗
    ║  AUTH TEAMMATE INTEGRATION POINT                                ║
    ║                                                                  ║
    ║  The auth teammate issues the JWT. This code only VERIFIES it.  ║
    ║                                                                  ║
    ║  If the token format changes (e.g. RS256 with JWKS, or a        ║
    ║  different claim name for student_id), update only this function.║
    ║  No other chatbot code needs to change.                         ║
    ╚══════════════════════════════════════════════════════════════════╝

    Raises:
        401 Unauthorized: if token is expired or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        if settings.app_env == "development":
            return "student_001"
        raise credentials_exception

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        student_id: str | None = payload.get("sub")
        if not student_id:
            raise credentials_exception
        return student_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception
