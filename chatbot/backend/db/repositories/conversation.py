"""
ConversationRepository — Persistence and Memory Management for Multi-Turn Chat.

Provides CRUD and state-retrieval operations for conversations and message history.
Ensures student-level data isolation, context window bounding, and structured artifact retrieval.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from chatbot.backend.db.models import Conversation, Message
from chatbot.backend.schemas.chat import MessageRole, MessageSchema
from chatbot.backend.schemas.planner import StudyPlan

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Async repository for conversation threads, message histories, and plan artifacts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Conversations ─────────────────────────────────────────────────────────

    async def create_conversation(
        self,
        student_id: str,
        title: str | None = None,
    ) -> Conversation:
        """Starts a new conversation thread for a student."""
        conv = Conversation(
            student_id=student_id,
            title=title,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self._session.add(conv)
        await self._session.flush()
        logger.info("ConversationRepository: Created conversation_id=%s for student_id=%s", conv.id, student_id)
        return conv

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
        student_id: str | None = None,
    ) -> Conversation | None:
        """
        Fetches a conversation by ID, optionally enforcing student isolation.
        """
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        if student_id:
            stmt = stmt.where(Conversation.student_id == student_id)

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_conversations(self, student_id: str) -> list[Conversation]:
        """Returns all conversations for a specific student, sorted by newest first."""
        result = await self._session.execute(
            select(Conversation)
            .where(Conversation.student_id == student_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def delete_conversation(
        self,
        conversation_id: uuid.UUID,
        student_id: str | None = None,
    ) -> bool:
        """Deletes a conversation and all its cascading messages."""
        conv = await self.get_conversation(conversation_id, student_id=student_id)
        if not conv:
            return False
        await self._session.delete(conv)
        await self._session.flush()
        logger.info("ConversationRepository: Deleted conversation_id=%s", conversation_id)
        return True

    async def update_title(
        self,
        conversation_id: uuid.UUID,
        title: str,
    ) -> None:
        """Updates the display title of a conversation."""
        conv = await self.get_conversation(conversation_id)
        if conv:
            conv.title = title
            conv.updated_at = datetime.utcnow()
            await self._session.flush()
            logger.info("ConversationRepository: Renamed conversation_id=%s to '%s'", conversation_id, title)



    # ── Messages ──────────────────────────────────────────────────────────────

    async def save_user_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
    ) -> Message:
        """Persists a student message."""
        msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER.value,
            content=content,
            created_at=datetime.utcnow(),
        )
        self._session.add(msg)
        await self._session.flush()
        return msg

    async def save_assistant_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
        structured_data: dict[str, Any] | None = None,
        agents_used: list[str] | None = None,
    ) -> Message:
        """Persists the chatbot's response, optionally attaching structured artifact data."""
        msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT.value,
            content=content,
            structured_data=structured_data,
            agents_used=agents_used or [],
            created_at=datetime.utcnow(),
        )
        self._session.add(msg)
        await self._session.flush()
        return msg

    async def get_history(
        self,
        conversation_id: uuid.UUID,
        limit: int = 50,
    ) -> list[Message]:
        """
        Returns the most recent `limit` messages in chronological order (oldest to newest).
        """
        result = await self._session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        messages = list(result.scalars().all())
        return messages[-limit:] if limit and len(messages) > limit else messages

    async def get_latest_study_plan(
        self,
        conversation_id: uuid.UUID,
    ) -> StudyPlan | None:
        """
        Retrieves the most recent StudyPlan generated in this conversation thread.
        Enables multi-turn plan revisions (e.g. 'Make Tuesday easier').
        """
        result = await self._session.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.role == MessageRole.ASSISTANT.value,
                Message.structured_data.isnot(None),
            )
            .order_by(Message.created_at.asc())
        )
        messages = list(result.scalars().all())
        for msg in reversed(messages):
            if msg.structured_data and isinstance(msg.structured_data, dict):
                try:
                    return StudyPlan.model_validate(msg.structured_data)
                except Exception as exc:
                    logger.warning("Failed to deserialize StudyPlan from message_id=%s: %s", msg.id, exc)
        return None

    def to_schema(self, msg: Message) -> MessageSchema:
        """Converts an ORM Message model to a Pydantic MessageSchema."""
        return MessageSchema(
            id=msg.id,
            role=MessageRole(msg.role),
            content=msg.content,
            created_at=msg.created_at,
        )
