"""
SQLAlchemy ORM models for the chatbot component.

Tables owned by this component:
  - conversations  (one per chat session)
  - messages       (one per turn in the conversation)

The StudentContext lives in the teammate's data source.
We store only the student_id FK reference here.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from chatbot.backend.db.session import Base


class Conversation(Base):
    """
    Represents a single chat session between a student and the chatbot.
    One student can have multiple conversations over time.
    """
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True,
        comment="FK reference to the student — resolved via auth teammate's JWT."
    )
    title: Mapped[str | None] = mapped_column(
        String(256), nullable=True,
        comment="Auto-generated summary title."
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list[Message]] = relationship(
        "Message", back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    """
    A single message turn in a conversation.
    role: 'user' | 'assistant'
    """
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(16), nullable=False,
        comment="'user' or 'assistant'"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Structured data (e.g. study plan JSON) returned alongside a message
    structured_data: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
        comment="Stores StudyPlanSchema or other structured payloads."
    )
    # Which LangGraph agent nodes were invoked for this turn (debug/analytics)
    agents_used: Mapped[list | None] = mapped_column(
        JSON, nullable=True,
        comment="List of agent node names that produced this message."
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, server_default=func.now()
    )

    conversation: Mapped[Conversation] = relationship(
        "Conversation", back_populates="messages"
    )
