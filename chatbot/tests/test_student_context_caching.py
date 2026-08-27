"""
Comprehensive Test Suite for StudentContext Retrieval, TTL Caching & Security.

Tests:
  - TEST 1: Student A context retrieval
  - TEST 2: Cache hit across multiple conversations for Student A
  - TEST 3: Multi-student isolation (Student A vs Student B)
  - TEST 4: Cache TTL expiration and fresh reload
  - TEST 5: Graceful fallback when provider is unavailable
  - TEST 6: Non-fabricating baseline for students with no records
  - TEST 7: Intent/ContextSelector isolating general queries from academic marks
  - TEST 8: ContextSelector injecting academic context for planning/coaching queries
  - TEST 9: JWT authentication enforcement (Anti-IDOR)
"""
from __future__ import annotations

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock

from chatbot.backend.db.repositories.student_context import (
    AcademicDataProvider,
    InMemoryStudentContextCache,
    StudentContextRepository,
)
from chatbot.backend.schemas.student import (
    AttendanceSummary,
    StudentContext,
    SubjectPerformance,
)
from chatbot.backend.orchestrator.context_selector import (
    select_relevant_context,
)
from chatbot.backend.schemas.routing import (
    ProcessedRequest,
    RequestIntent,
    ResponseConstraints,
)
from chatbot.backend.core.memory import UserFacts
from chatbot.backend.api.dependencies import get_current_student_id
from fastapi.security import HTTPAuthorizationCredentials
import jwt
from chatbot.backend.config import get_settings


# ── Sample Academic Data Provider for Testing ─────────────────────────────────

class MockTestAcademicProvider(AcademicDataProvider):
    """Mock provider with predictable test data."""

    def __init__(self, records: dict[str, StudentContext] | None = None, is_broken: bool = False) -> None:
        self.records = records or {}
        self.is_broken = is_broken
        self.call_count = 0

    async def fetch_student_context(self, student_id: str) -> StudentContext | None:
        self.call_count += 1
        if self.is_broken:
            raise ConnectionError("Database connection refused")
        return self.records.get(student_id)


@pytest.fixture
def sample_student_a() -> StudentContext:
    return StudentContext(
        student_id="student_123",
        student_name="Alice",
        department="Computer Science",
        attendance=AttendanceSummary(overall_percentage=88.5, trend="improving"),
        subjects=[
            SubjectPerformance(
                subject_name="Data Structures",
                current_marks_percentage=82.0,
            ),
            SubjectPerformance(
                subject_name="Algorithms",
                current_marks_percentage=75.0,
            ),
        ],
    )


@pytest.fixture
def sample_student_b() -> StudentContext:
    return StudentContext(
        student_id="student_456",
        student_name="Bob",
        department="Mechanical Engineering",
        attendance=AttendanceSummary(overall_percentage=64.0, trend="declining"),
        subjects=[
            SubjectPerformance(
                subject_name="Thermodynamics",
                current_marks_percentage=55.0,
            ),
        ],
    )


# ── Test Cases 1 through 9 ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_1_student_a_retrieval(sample_student_a: StudentContext):
    """TEST 1: Student A context is correctly retrieved and converted to schema."""
    provider = MockTestAcademicProvider({"student_123": sample_student_a})
    repo = StudentContextRepository(provider=provider, ttl_seconds=60)

    ctx = await repo.get_context("student_123")
    assert ctx.student_id == "student_123"
    assert ctx.student_name == "Alice"
    assert ctx.attendance is not None
    assert ctx.attendance.overall_percentage == 88.5
    assert len(ctx.subjects) == 2
    assert provider.call_count == 1


@pytest.mark.asyncio
async def test_2_student_a_cache_hit_multiple_conversations(sample_student_a: StudentContext):
    """TEST 2: Second conversation/request reuses the cached StudentContext without re-querying provider."""
    provider = MockTestAcademicProvider({"student_123": sample_student_a})
    repo = StudentContextRepository(provider=provider, ttl_seconds=60)

    # First conversation / turn
    ctx_turn_1 = await repo.get_context("student_123")
    assert provider.call_count == 1

    # Second conversation / turn
    ctx_turn_2 = await repo.get_context("student_123")
    assert provider.call_count == 1  # Cache HIT: provider was NOT called again

    assert ctx_turn_1.student_name == ctx_turn_2.student_name
    assert ctx_turn_1.subjects[0].subject_name == ctx_turn_2.subjects[0].subject_name


@pytest.mark.asyncio
async def test_3_student_isolation(sample_student_a: StudentContext, sample_student_b: StudentContext):
    """TEST 3: Student B receives Student B's context, strictly isolated from Student A."""
    provider = MockTestAcademicProvider({
        "student_123": sample_student_a,
        "student_456": sample_student_b,
    })
    repo = StudentContextRepository(provider=provider, ttl_seconds=60)

    ctx_a = await repo.get_context("student_123")
    ctx_b = await repo.get_context("student_456")

    assert ctx_a.student_id == "student_123"
    assert ctx_a.student_name == "Alice"
    assert ctx_a.subjects[0].subject_name == "Data Structures"

    assert ctx_b.student_id == "student_456"
    assert ctx_b.student_name == "Bob"
    assert ctx_b.subjects[0].subject_name == "Thermodynamics"

    assert ctx_a.student_id != ctx_b.student_id


@pytest.mark.asyncio
async def test_4_cache_ttl_expiration(sample_student_a: StudentContext):
    """TEST 4: After TTL expiration, cache miss occurs and fresh data is retrieved."""
    provider = MockTestAcademicProvider({"student_123": sample_student_a})
    # Short TTL for test: 1 second
    repo = StudentContextRepository(provider=provider, ttl_seconds=1)

    # Initial call -> cache set
    await repo.get_context("student_123")
    assert provider.call_count == 1

    # Immediate call -> cache hit
    await repo.get_context("student_123")
    assert provider.call_count == 1

    # Wait for TTL expiration
    await asyncio.sleep(1.1)

    # Post-TTL call -> cache miss -> fresh provider fetch
    ctx_fresh = await repo.get_context("student_123")
    assert provider.call_count == 2
    assert ctx_fresh.student_id == "student_123"


@pytest.mark.asyncio
async def test_5_academic_datasource_unavailable_fallback():
    """TEST 5: If academic database/service is unavailable, safe baseline is returned without error."""
    provider = MockTestAcademicProvider(is_broken=True)
    repo = StudentContextRepository(provider=provider, ttl_seconds=60)

    ctx = await repo.get_context("student_broken_db")
    assert ctx is not None
    assert ctx.student_id == "student_broken_db"
    assert ctx.student_name == ""
    assert ctx.attendance is None
    assert ctx.subjects == []


@pytest.mark.asyncio
async def test_6_student_no_academic_records():
    """TEST 6: If student has no records in database, baseline context is returned with no fabricated data."""
    provider = MockTestAcademicProvider({})  # empty DB
    repo = StudentContextRepository(provider=provider, ttl_seconds=60)

    ctx = await repo.get_context("student_new_user")
    assert ctx.student_id == "student_new_user"
    assert ctx.student_name == ""
    assert ctx.attendance is None
    assert ctx.subjects == []
    assert ctx.assessments is None


def test_7_context_selector_general_question(sample_student_a: StudentContext):
    """TEST 7: General question ('What is recursion?') does NOT expose academic marks to LLM."""
    req = ProcessedRequest(
        raw_message="What is recursion?",
        intent=RequestIntent.EDUCATIONAL,
        constraints=ResponseConstraints(),
    )
    user_facts = UserFacts()

    selected = select_relevant_context(
        processed_request=req,
        user_facts=user_facts,
        student_context=sample_student_a,
        conversation_history=[],
    )

    assert selected.academic_context is None
    assert selected.inject_academic_insight is False


def test_8_context_selector_academic_question(sample_student_a: StudentContext):
    """TEST 8: Academic focus question ('Which subject should I focus on?') provides StudentContext to agent."""
    req = ProcessedRequest(
        raw_message="Which subject should I focus on?",
        intent=RequestIntent.ACADEMIC_INSIGHT,
        constraints=ResponseConstraints(),
    )
    user_facts = UserFacts()

    selected = select_relevant_context(
        processed_request=req,
        user_facts=user_facts,
        student_context=sample_student_a,
        conversation_history=[],
    )

    assert selected.academic_context is not None
    assert selected.academic_context.student_id == "student_123"
    assert len(selected.academic_context.subjects) == 2
    assert selected.inject_academic_insight is True


@pytest.mark.asyncio
async def test_9_anti_idor_jwt_extraction():
    """TEST 9: Student identity is strictly extracted from verified JWT sub claim."""
    settings = get_settings()

    # Valid token for student_attacker
    valid_token = jwt.encode(
        {"sub": "student_real_identity"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=valid_token)
    resolved_id = await get_current_student_id(creds)

    assert resolved_id == "student_real_identity"
