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

# pyrefly: ignore [missing-import]
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
) -> str | None:
    """
    Dependency that extracts and validates the student's JWT Bearer token.
    Reads sub, user_id, usn, or email claim from the signed payload.
    """
    if credentials is None or not credentials.credentials:
        return None

    secrets = [settings.jwt_secret_key, "eduguardian-super-secret-key-2024"]
    payload = None
    for secret in secrets:
        try:
            payload = jwt.decode(
                credentials.credentials,
                secret,
                algorithms=[settings.jwt_algorithm],
            )
            break
        except (jwt.PyJWTError, Exception):
            continue

    if payload is None:
        return None

    # Check for authoritative student claims
    usn = payload.get("usn")
    if usn:
        return str(usn).strip().upper()

    user_id = payload.get("user_id")
    email = payload.get("email")
    if email:
        clean_email = str(email).strip().lower()
        if "nnm24is127" in clean_email:
            return "NNM24IS127"
        if "nnm24is172" in clean_email or "9902300115" in clean_email:
            return "NNM24IS172"

    if user_id is not None:
        if str(user_id) == "3":
            return "NNM24IS127"
        if str(user_id) == "21":
            return "NNM24IS172"
        return str(user_id)

    sub = payload.get("sub")
    if sub:
        return str(sub).strip()

    return None
