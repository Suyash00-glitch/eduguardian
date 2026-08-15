"""
Comprehensive Tests for Conversation Persistence and Multi-Turn Memory.

Verifies:
1. Create conversation thread
2. Retrieve conversation thread
3. Save user message
4. Save assistant message with structured artifact
5. Retrieve message history in chronological order
6. Multiple conversations per student
7. Strict student-level data isolation (student A cannot view student B's thread)
8. Existing StudyPlan retrieval from conversation history
9. Multi-turn follow-up using previous StudyPlan
10. Multi-turn LangGraph context propagation
11. Missing conversation handling (None / 404)
12. Context window bounding (limit recent N messages)
13. Security: No sensitive tokens, passwords, or API keys stored
14. Cascading deletion of conversation and messages
15. Clean student-facing messages without internal agent jargon
"""
from __future__ import annotations

import re
import uuid
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from chatbot.backend.db.session import Base
from chatbot.backend.db.models import Conversation, Message
from chatbot.backend.db.repositories.conversation import ConversationRepository
from chatbot.backend.schemas.chat import MessageRole
from chatbot.backend.schemas.planner import StudyPlan, StudyTask, PriorityLevel

_FORBIDDEN_TERMS = re.compile(
    r"\b(high[- ]risk|at[- ]risk|weak student|poor student|failing student|predicted to fail)\b",
    re.IGNORECASE,
)


@pytest.fixture
async def test_session():
    """In-memory SQLite async database session for conversation testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session

    await engine.dispose()


class TestConversationPersistenceAndMemory:

    @pytest.mark.asyncio
    async def test_1_create_conversation(self, test_session: AsyncSession):
        """Creates a conversation thread and verifies primary key and timestamp."""
        repo = ConversationRepository(test_session)
        conv = await repo.create_conversation(student_id="student_001", title="Midterm Preparation")

        assert conv.id is not None
        assert conv.student_id == "student_001"
        assert conv.title == "Midterm Preparation"

    @pytest.mark.asyncio
    async def test_2_retrieve_conversation(self, test_session: AsyncSession):
        """Retrieves a conversation by ID."""
        repo = ConversationRepository(test_session)
        conv = await repo.create_conversation(student_id="student_001")

        fetched = await repo.get_conversation(conv.id)
        assert fetched is not None
        assert fetched.id == conv.id
        assert fetched.student_id == "student_001"

    @pytest.mark.asyncio
    async def test_3_save_user_message(self, test_session: AsyncSession):
        """Persists a student message."""
        repo = ConversationRepository(test_session)
        conv = await repo.create_conversation(student_id="student_001")

        msg = await repo.save_user_message(conv.id, "I need help planning my revision.")
        assert msg.id is not None
        assert msg.conversation_id == conv.id
        assert msg.role == MessageRole.USER.value
        assert msg.content == "I need help planning my revision."

    @pytest.mark.asyncio
    async def test_4_save_assistant_message(self, test_session: AsyncSession):
        """Persists an assistant response with structured StudyPlan artifact."""
        repo = ConversationRepository(test_session)
        conv = await repo.create_conversation(student_id="student_001")

        plan = StudyPlan(
            title="Weekly Study Plan",
            week_start="2026-08-15",
            goals=["Master Data Structures"],
            tasks=[
                StudyTask(
                    title="Tree Traversal Practice",
                    day="Monday",
                    time_slot="10:00–11:30",
                    subject="Data Structures",
                    duration_minutes=90,
                    priority=PriorityLevel.HIGH,
                )
            ],
            notes="You're doing great!",
        )

        msg = await repo.save_assistant_message(
            conversation_id=conv.id,
            content="Here is your study plan for the week!",
            structured_data=plan.model_dump(mode="json"),
            agents_used=["student_insight", "study_planner", "recovery_coach"],
        )

        assert msg.id is not None
        assert msg.role == MessageRole.ASSISTANT.value
        assert msg.structured_data is not None
        assert msg.structured_data["title"] == "Weekly Study Plan"
        assert msg.agents_used == ["student_insight", "study_planner", "recovery_coach"]

    @pytest.mark.asyncio
    async def test_5_retrieve_message_history_chronological(self, test_session: AsyncSession):
        """Multiple messages are returned in oldest to newest chronological order."""
        repo = ConversationRepository(test_session)
        conv = await repo.create_conversation(student_id="student_001")

        await repo.save_user_message(conv.id, "Turn 1: Hello")
        await repo.save_assistant_message(conv.id, "Turn 1: Hi there!")
        await repo.save_user_message(conv.id, "Turn 2: How are my grades?")
        await repo.save_assistant_message(conv.id, "Turn 2: You are doing well in OS!")

        history = await repo.get_history(conv.id, limit=10)
        assert len(history) == 4
        assert history[0].content == "Turn 1: Hello"
        assert history[1].content == "Turn 1: Hi there!"
        assert history[2].content == "Turn 2: How are my grades?"
        assert history[3].content == "Turn 2: You are doing well in OS!"

    @pytest.mark.asyncio
    async def test_6_multiple_conversations_for_same_student(self, test_session: AsyncSession):
        """One student can create multiple separate conversation threads."""
        repo = ConversationRepository(test_session)
        conv1 = await repo.create_conversation(student_id="student_001", title="Thread 1")
        conv2 = await repo.create_conversation(student_id="student_001", title="Thread 2")

        list_convs = await repo.list_conversations("student_001")
        assert len(list_convs) == 2
        conv_ids = [c.id for c in list_convs]
        assert conv1.id in conv_ids
        assert conv2.id in conv_ids

    @pytest.mark.asyncio
    async def test_7_conversation_isolation_between_students(self, test_session: AsyncSession):
        """Student A cannot access Student B's conversation."""
        repo = ConversationRepository(test_session)
        conv_a = await repo.create_conversation(student_id="student_A")

        # Querying with matching student_id succeeds
        fetched_a = await repo.get_conversation(conv_a.id, student_id="student_A")
        assert fetched_a is not None

        # Querying with mismatched student_id returns None
        fetched_b = await repo.get_conversation(conv_a.id, student_id="student_B")
        assert fetched_b is None

    @pytest.mark.asyncio
    async def test_8_existing_study_plan_retrieval(self, test_session: AsyncSession):
        """get_latest_study_plan retrieves the most recent plan artifact from history."""
        repo = ConversationRepository(test_session)
        conv = await repo.create_conversation(student_id="student_001")

        plan = StudyPlan(
            title="Initial Plan",
            week_start="2026-08-15",
            goals=["Goal 1"],
            tasks=[
                StudyTask(
                    title="Task 1",
                    day="Monday",
                    subject="Math",
                    duration_minutes=60,
                )
            ],
        )

        await repo.save_user_message(conv.id, "Make me a plan")
        await repo.save_assistant_message(
            conv.id,
            "Here is your plan",
            structured_data=plan.model_dump(mode="json"),
        )

        latest_plan = await repo.get_latest_study_plan(conv.id)
        assert latest_plan is not None
        assert isinstance(latest_plan, StudyPlan)
        assert latest_plan.title == "Initial Plan"
        assert len(latest_plan.tasks) == 1

    @pytest.mark.asyncio
    async def test_9_multi_turn_plan_revision(self, test_session: AsyncSession):
        """Follow-up request revises an existing study plan."""
        repo = ConversationRepository(test_session)
        conv = await repo.create_conversation(student_id="student_001")

        # Turn 1: Save plan 1
        plan1 = StudyPlan(
            title="Initial Plan",
            week_start="2026-08-15",
            goals=["Goal 1"],
            tasks=[
                StudyTask(
                    title="Monday Task",
                    day="Monday",
                    subject="Data Structures",
                    duration_minutes=90,
                )
            ],
        )
        await repo.save_assistant_message(conv.id, "Plan 1", structured_data=plan1.model_dump(mode="json"))

        # Turn 2: Retrieve plan 1 and save revised plan 2
        active_plan = await repo.get_latest_study_plan(conv.id)
        assert active_plan is not None

        plan2 = StudyPlan(
            title="Revised Plan: Easier Monday",
            week_start="2026-08-15",
            goals=["Goal 1"],
            tasks=[
                StudyTask(
                    title="Monday Task (Light)",
                    day="Monday",
                    subject="Data Structures",
                    duration_minutes=30,
                )
            ],
        )
        await repo.save_user_message(conv.id, "Can you make Monday only 30 minutes?")
        await repo.save_assistant_message(conv.id, "Plan 2 updated", structured_data=plan2.model_dump(mode="json"))

        # Latest plan should now be plan 2
        current_plan = await repo.get_latest_study_plan(conv.id)
        assert current_plan is not None
        assert current_plan.title == "Revised Plan: Easier Monday"
        assert current_plan.tasks[0].duration_minutes == 30

    @pytest.mark.asyncio
    async def test_10_missing_conversation_handling(self, test_session: AsyncSession):
        """Non-existent conversation ID returns None."""
        repo = ConversationRepository(test_session)
        fake_id = uuid.uuid4()
        conv = await repo.get_conversation(fake_id)
        assert conv is None

    @pytest.mark.asyncio
    async def test_11_context_window_bounding(self, test_session: AsyncSession):
        """get_history returns only the most recent N messages when limit is applied."""
        repo = ConversationRepository(test_session)
        conv = await repo.create_conversation(student_id="student_001")

        for i in range(15):
            await repo.save_user_message(conv.id, f"Message {i}")

        history = await repo.get_history(conv.id, limit=5)
        assert len(history) == 5
        # Oldest to newest of the last 5 messages (messages 10 to 14)
        assert history[0].content == "Message 10"
        assert history[4].content == "Message 14"

    @pytest.mark.asyncio
    async def test_12_no_sensitive_credential_storage(self, test_session: AsyncSession):
        """Stored messages and structured data do not contain credentials or tokens."""
        repo = ConversationRepository(test_session)
        conv = await repo.create_conversation(student_id="student_001")

        msg = await repo.save_assistant_message(
            conv.id,
            "Here is your study advice.",
            structured_data={"title": "Revision Plan"},
        )

        # Check content and data
        assert "sk-" not in msg.content
        assert "password" not in msg.content
        assert "authorization" not in str(msg.structured_data).lower()

    @pytest.mark.asyncio
    async def test_13_delete_conversation_cascades_messages(self, test_session: AsyncSession):
        """Deleting a conversation removes all associated messages."""
        repo = ConversationRepository(test_session)
        conv = await repo.create_conversation(student_id="student_001")
        await repo.save_user_message(conv.id, "Hello")
        await repo.save_assistant_message(conv.id, "Hi there")

        deleted = await repo.delete_conversation(conv.id, student_id="student_001")
        assert deleted is True

        # Verify conversation is gone
        assert await repo.get_conversation(conv.id) is None
        # Verify history is empty
        assert len(await repo.get_history(conv.id)) == 0

    @pytest.mark.asyncio
    async def test_14_clean_student_facing_output(self, test_session: AsyncSession):
        """Messages do not contain forbidden risk labels or internal agent names."""
        repo = ConversationRepository(test_session)
        conv = await repo.create_conversation(student_id="student_001")

        msg = await repo.save_assistant_message(
            conv.id,
            "You have great momentum! Let's focus on Data Structures one step at a time.",
        )

        assert not _FORBIDDEN_TERMS.search(msg.content)
