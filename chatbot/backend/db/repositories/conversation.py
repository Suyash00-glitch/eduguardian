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
from chatbot.backend.schemas.planner import StudyPlan, StudyPlanIntakeState
from chatbot.backend.schemas.teaching import TeachingState
from chatbot.backend.schemas.quiz import QuizState
from chatbot.backend.schemas.learning_history import LearningHistory, TopicQuizRecord

logger = logging.getLogger(__name__)


def normalize_topic_name(topic_raw: Any) -> str:
    """Normalizes topic name cleanly while preserving uppercase acronyms (e.g. DBMS, SQL, OS, OOP, DSA, API)."""
    if not topic_raw:
        return ""
    text = str(topic_raw).strip()
    if not text:
        return ""
    if text.isupper() and len(text) <= 5:
        return text
    words = text.split()
    normalized_words = []
    for w in words:
        if w.upper() in {"DBMS", "SQL", "OS", "OOP", "DSA", "API", "HTML", "CSS", "AI", "ML", "UI", "UX", "REST", "JSON", "JWT"}:
            normalized_words.append(w.upper())
        else:
            normalized_words.append(w.capitalize())
    return " ".join(normalized_words)


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
            clean_sid = (student_id or "").strip()
            candidates = {clean_sid, clean_sid.upper(), clean_sid.lower()}
            if clean_sid == "3" or clean_sid == "NNM24IS127" or "nnm24is127" in clean_sid.lower():
                candidates.update({"3", "NNM24IS127", "nnm24is127@eduguardian.ai"})
            elif clean_sid == "21" or clean_sid == "NNM24IS172" or "nnm24is172" in clean_sid.lower() or "9902300115" in clean_sid:
                candidates.update({"21", "NNM24IS172", "9902300115@studentportal.universitysolutions.in"})
            stmt = stmt.where(Conversation.student_id.in_(candidates))

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_conversations(self, student_id: str) -> list[Conversation]:
        """Returns all conversations for a specific student, sorted by newest first."""
        clean_sid = (student_id or "").strip()
        candidates = {clean_sid, clean_sid.upper(), clean_sid.lower()}
        if clean_sid == "3" or clean_sid == "NNM24IS127" or "nnm24is127" in clean_sid.lower():
            candidates.update({"3", "NNM24IS127", "nnm24is127@eduguardian.ai"})
        elif clean_sid == "21" or clean_sid == "NNM24IS172" or "nnm24is172" in clean_sid.lower() or "9902300115" in clean_sid:
            candidates.update({"21", "NNM24IS172", "9902300115@studentportal.universitysolutions.in"})

        result = await self._session.execute(
            select(Conversation)
            .where(Conversation.student_id.in_(candidates))
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

    async def update_student_id(
        self,
        conversation_id: uuid.UUID,
        student_id: str,
    ) -> None:
        """Transfers or updates ownership of a conversation to a resolved student identity."""
        conv = await self.get_conversation(conversation_id)
        if conv:
            conv.student_id = student_id
            conv.updated_at = datetime.utcnow()
            await self._session.flush()
            logger.info("ConversationRepository: Updated conversation_id=%s student_id to %s", conversation_id, student_id)



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
                # Type discrimination: Identify if structured_data contains a genuine StudyPlan
                plan_data = None
                if "study_plan" in msg.structured_data and isinstance(msg.structured_data["study_plan"], dict):
                    plan_data = msg.structured_data["study_plan"]
                elif msg.structured_data.get("type") == "study_plan":
                    plan_data = msg.structured_data
                elif ("tasks" in msg.structured_data or "goals" in msg.structured_data) and "teaching_state" not in msg.structured_data:
                    plan_data = msg.structured_data
                elif ("tasks" in msg.structured_data or "goals" in msg.structured_data) and ("title" in msg.structured_data or "plan_title" in msg.structured_data):
                    plan_data = msg.structured_data

                # If this message was solely teaching_state or other structured artifact, skip it cleanly!
                if plan_data and isinstance(plan_data, dict):
                    # Normalization: ensure title exists if plan_title was used
                    if not plan_data.get("title") and plan_data.get("plan_title"):
                        plan_data = {**plan_data, "title": plan_data["plan_title"]}
                    try:
                        return StudyPlan.model_validate(plan_data)
                    except Exception as exc:
                        logger.warning("Failed to deserialize StudyPlan from message_id=%s: %s", msg.id, exc)
        return None

    async def get_latest_study_plan_intake(
        self,
        conversation_id: uuid.UUID,
    ) -> StudyPlanIntakeState | None:
        """
        Retrieves the most recent active StudyPlanIntakeState for this conversation.

        Scans assistant messages in reverse chronological order for structured_data["intake_state"].
        Returns None if no active (incomplete) intake session is found.
        Follows the same pattern as get_latest_teaching_state().
        """
        result = await self._session.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.role == MessageRole.ASSISTANT.value,
                Message.structured_data.isnot(None),
            )
            .order_by(Message.created_at.desc())
            .limit(20)
        )
        messages = list(result.scalars().all())
        for msg in messages:
            if msg.structured_data and isinstance(msg.structured_data, dict):
                intake_data = msg.structured_data.get("intake_state")
                if intake_data and isinstance(intake_data, dict):
                    try:
                        intake = StudyPlanIntakeState.model_validate(intake_data)
                        # Only return if the intake session is still active (not yet complete)
                        if intake.active and intake.step != "complete":
                            return intake
                    except Exception as exc:
                        logger.debug(
                            "ConversationRepository: Skipped malformed intake_state in message_id=%s (%s)",
                            msg.id, exc
                        )
        return None

    async def get_latest_teaching_state(
        self,
        conversation_id: uuid.UUID,
    ) -> TeachingState | None:
        """
        Retrieves the most recent TeachingState generated in this conversation thread.
        Enables multi-turn tutoring lessons, question evaluation, and concept adaptation.
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
                t_data = msg.structured_data.get(
                    "teaching_state",
                    msg.structured_data if ("topic" in msg.structured_data and "difficulty" in msg.structured_data) else None,
                )
                if t_data and isinstance(t_data, dict) and "topic" in t_data:
                    try:
                        return TeachingState.model_validate(t_data)
                    except Exception as exc:
                        logger.warning("Failed to deserialize TeachingState from message_id=%s: %s", msg.id, exc)
        return None

    async def get_latest_quiz_state(
        self,
        conversation_id: uuid.UUID,
    ) -> QuizState | None:
        """
        Retrieves the most recent QuizState generated in this conversation thread.
        Enables multi-turn interactive quizzes, question answer evaluation, and scoring.
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
                q_data = msg.structured_data.get(
                    "quiz_state",
                    msg.structured_data if ("topic" in msg.structured_data and "total_questions" in msg.structured_data) else None,
                )
                if q_data and isinstance(q_data, dict) and "topic" in q_data:
                    try:
                        return QuizState.model_validate(q_data)
                    except Exception as exc:
                        logger.warning("Failed to deserialize QuizState from message_id=%s: %s", msg.id, exc)
        return None

    async def get_learning_history(self, student_id: str) -> LearningHistory:
        """
        Aggregates interaction-derived LearningHistory across all conversations for a student.
        Derives quiz performance, topic mastery, and practice needs from existing PostgreSQL
        structured_data without duplicating StudentContext.
        """
        result = await self._session.execute(
            select(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                Conversation.student_id == student_id,
                Message.role == MessageRole.ASSISTANT.value,
                Message.structured_data.isnot(None),
            )
            .order_by(Message.created_at.asc())
        )
        messages = list(result.scalars().all())

        topic_stats: dict[str, dict[str, Any]] = {}
        total_quizzes = 0
        explicit_preferences: dict[str, str] = {}

        for msg in messages:
            try:
                if not msg.structured_data or not isinstance(msg.structured_data, dict):
                    continue

                # Check for explicit learning preference actions (in chronological order)
                pref_action = msg.structured_data.get("preference_action")
                if pref_action and isinstance(pref_action, dict):
                    action_type = pref_action.get("action")
                    pref_key = pref_action.get("key")
                    pref_val = pref_action.get("value")
                    if action_type == "set" and pref_key and pref_val:
                        explicit_preferences[str(pref_key)] = str(pref_val)
                    elif action_type == "remove" and pref_key:
                        if pref_key == "all":
                            explicit_preferences.clear()
                        else:
                            explicit_preferences.pop(str(pref_key), None)

                direct_prefs = msg.structured_data.get("explicit_preferences")
                if direct_prefs and isinstance(direct_prefs, dict):
                    for k, v in direct_prefs.items():
                        if v is None:
                            explicit_preferences.pop(str(k), None)
                        else:
                            explicit_preferences[str(k)] = str(v)

                # Discrimination: Only inspect completed quiz_session artifacts
                q_data = None
                if msg.structured_data.get("type") == "quiz_session" and "quiz_state" in msg.structured_data:
                    q_data = msg.structured_data["quiz_state"]
                elif "quiz_state" in msg.structured_data and isinstance(msg.structured_data["quiz_state"], dict):
                    q_data = msg.structured_data["quiz_state"]
                elif "total_questions" in msg.structured_data and "score" in msg.structured_data and "tasks" not in msg.structured_data and "teaching_state" not in msg.structured_data:
                    q_data = msg.structured_data

                if not q_data or not isinstance(q_data, dict):
                    continue

                # Check if quiz was completed (ignore active / in-progress sessions)
                is_completed = (q_data.get("step") == "completed") or (q_data.get("active") is False and q_data.get("total_questions", 0) > 0)
                if not is_completed:
                    continue

                topic_raw = q_data.get("topic")
                if not topic_raw or not str(topic_raw).strip():
                    continue

                topic = normalize_topic_name(topic_raw)
                if not topic:
                    continue
                score = float(q_data.get("score", 0.0))
                total_q = int(q_data.get("total_questions", 0))

                if total_q <= 0:
                    continue

                total_quizzes += 1

                if topic not in topic_stats:
                    topic_stats[topic] = {
                        "topic": topic,
                        "attempts": 0,
                        "total_score": 0.0,
                        "total_possible": 0,
                        "latest_score": 0.0,
                        "latest_total": 0,
                        "history": [],
                    }

                topic_stats[topic]["attempts"] += 1
                topic_stats[topic]["total_score"] += score
                topic_stats[topic]["total_possible"] += total_q
                topic_stats[topic]["latest_score"] = score
                topic_stats[topic]["latest_total"] = total_q
                topic_stats[topic]["history"].append(score / total_q)
            except Exception as exc:
                logger.debug("ConversationRepository: Skipped malformed quiz structured_data in message_id=%s (%s)", getattr(msg, "id", "unknown"), exc)
                continue

        # Build TopicQuizRecords and derive mastery / practice needs based on solid evidence
        topic_records: dict[str, TopicQuizRecord] = {}
        quiz_mastery: dict[str, float] = {}
        mastered_topics: list[str] = []
        needs_practice_topics: list[str] = []

        for topic, stat in topic_stats.items():
            tot_possible = stat["total_possible"]
            tot_score = stat["total_score"]
            avg_acc = tot_score / tot_possible if tot_possible > 0 else 0.0
            avg_acc = round(avg_acc, 2)
            quiz_mastery[topic] = avg_acc

            latest_acc = stat["latest_score"] / stat["latest_total"] if stat["latest_total"] > 0 else 0.0
            recent_attempts = stat["history"][-2:] if len(stat["history"]) >= 2 else stat["history"]
            recent_acc = sum(recent_attempts) / len(recent_attempts) if recent_attempts else latest_acc

            record = TopicQuizRecord(
                topic=topic,
                attempts=stat["attempts"],
                total_score=round(tot_score, 1),
                total_possible=tot_possible,
                latest_score=stat["latest_score"],
                latest_total=stat["latest_total"],
                average_accuracy=avg_acc,
            )
            topic_records[topic] = record

            # Correctness Criteria:
            # - Mastered: Repeated strong performance (attempts >= 2, recent_acc >= 0.75, latest_acc >= 0.70)
            #   OR a solid perfect multi-question quiz (attempts == 1, total >= 3, score == total)
            is_mastered = False
            if (stat["attempts"] >= 2 and recent_acc >= 0.75 and latest_acc >= 0.70) or (stat["attempts"] == 1 and stat["latest_total"] >= 3 and stat["latest_score"] == stat["latest_total"]):
                is_mastered = True

            # - Needs Practice: Repeated low performance (attempts >= 2, recent_acc < 0.60, latest_acc < 0.65)
            #   OR a severely struggling multi-question quiz (attempts == 1, total >= 3, latest_acc <= 0.35)
            is_needs_practice = False
            if not is_mastered:
                if (stat["attempts"] >= 2 and recent_acc < 0.60 and latest_acc < 0.65) or (stat["attempts"] == 1 and stat["latest_total"] >= 3 and latest_acc <= 0.35):
                    is_needs_practice = True

            if is_mastered:
                mastered_topics.append(topic)
            elif is_needs_practice:
                needs_practice_topics.append(topic)

        return LearningHistory(
            student_id=student_id,
            quiz_mastery=quiz_mastery,
            topic_records=topic_records,
            mastered_topics=mastered_topics,
            needs_practice_topics=needs_practice_topics,
            explicit_preferences=explicit_preferences,
            total_quizzes_completed=total_quizzes,
        )

    def to_schema(self, msg: Message) -> MessageSchema:
        """Converts an ORM Message model to a Pydantic MessageSchema."""
        return MessageSchema(
            id=msg.id,
            role=MessageRole(msg.role),
            content=msg.content,
            created_at=msg.created_at,
        )
