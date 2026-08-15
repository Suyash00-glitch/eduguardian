"""
Unit Tests for User Fact Extraction and Disambiguation Engine.
Tests all 9 specific user facts scenarios:
1. 'My name is Ajmal.' -> fact: name = 'Ajmal'
2. 'What is my name?' -> answers 'Ajmal'
3. 'Where am I from?' (hometown unknown) -> 'I don't have your hometown information yet.', NO 'Hi From!'
4. 'I am asking where I am from.' -> NO name extraction ('Asking'), NO 'Hi Asking!'
5. 'My name is Ajmal and I am from Mangalore.' -> facts: name = 'Ajmal', hometown = 'Mangalore'
6. 'Where am I from?' (hometown known) -> 'Mangalore.' or 'You're from Mangalore.'
7. 'Why are you asking?' -> NO name extraction
8. 'Tell me about people from Bangalore.' -> NO user location fact
9. 'Where are you from?' -> AI identity answer
"""
import pytest
from chatbot.backend.core.memory import (
    extract_name,
    extract_hometown,
    extract_location,
    is_name_query,
    is_hometown_query,
    is_ai_origin_query,
    resolve_user_facts,
)
from chatbot.backend.agents.recovery_coach.agent import RecoveryCoachAgent
from chatbot.backend.schemas.coach import CoachRequest, CoachMessageItem
from chatbot.backend.schemas.student import StudentContext


class TestUserFactsMemory:
    """Test suite for fact extraction, query disambiguation, and memory resolution."""

    def test_1_explicit_name_declaration(self):
        facts = resolve_user_facts([], "My name is Ajmal.")
        assert facts.name == "Ajmal"
        assert facts.hometown is None

    def test_2_name_query_preserves_name_fact(self):
        history = [CoachMessageItem(role="user", content="My name is Ajmal.")]
        facts = resolve_user_facts(history, "What is my name?")
        assert facts.name == "Ajmal"
        assert is_name_query("What is my name?") is True

    def test_3_unknown_hometown_query(self):
        history = [CoachMessageItem(role="user", content="My name is Ajmal.")]
        facts = resolve_user_facts(history, "Where am I from?")
        assert facts.name == "Ajmal"
        assert facts.hometown is None
        assert is_hometown_query("Where am I from?") is True
        assert extract_name("Where am I from?") is None

    def test_4_i_am_asking_no_name_extraction(self):
        history = [CoachMessageItem(role="user", content="My name is Ajmal.")]
        facts = resolve_user_facts(history, "I am asking where I am from.")
        assert facts.name == "Ajmal"
        assert facts.hometown is None
        assert extract_name("I am asking where I am from.") is None
        assert is_hometown_query("I am asking where I am from.") is True

    def test_5_combined_name_and_hometown_declaration(self):
        facts = resolve_user_facts([], "My name is Ajmal and I am from Mangalore.")
        assert facts.name == "Ajmal"
        assert facts.hometown == "Mangalore"

    def test_6_known_hometown_query(self):
        history = [CoachMessageItem(role="user", content="My name is Ajmal and I am from Mangalore.")]
        facts = resolve_user_facts(history, "Where am I from?")
        assert facts.name == "Ajmal"
        assert facts.hometown == "Mangalore"

    def test_7_why_are_you_asking_no_name_extraction(self):
        assert extract_name("Why are you asking?") is None

    def test_8_third_party_place_no_fact_extraction(self):
        assert extract_hometown("Tell me about people from Bangalore.") is None
        assert extract_hometown("My friend is from Mangalore.") is None

    def test_9_where_are_you_from_ai_query(self):
        assert is_hometown_query("Where are you from?") is False
        assert is_ai_origin_query("Where are you from?") is True


@pytest.mark.asyncio
class TestUserFactsRecoveryCoachIntegration:
    """Tests RecoveryCoachAgent output for the 9 scenarios."""

    async def test_unknown_hometown_response_no_hi_from(self):
        agent = RecoveryCoachAgent()
        req = CoachRequest(
            student_id="student_001",
            user_message="Where am I from?",
            conversation_history=[
                CoachMessageItem(role="user", content="My name is Ajmal."),
                CoachMessageItem(role="assistant", content="Ajmal."),
            ],
        )
        resp = await agent.generate_response(req)
        text = resp.response_text
        assert "Hi From" not in text
        assert "From!" not in text
        assert "don't have your hometown" in text.lower() or "not have" in text.lower()

    async def test_i_am_asking_response_no_hi_asking(self):
        agent = RecoveryCoachAgent()
        req = CoachRequest(
            student_id="student_001",
            user_message="I am asking where I am from.",
            conversation_history=[
                CoachMessageItem(role="user", content="My name is Ajmal."),
                CoachMessageItem(role="assistant", content="Ajmal."),
            ],
        )
        resp = await agent.generate_response(req)
        text = resp.response_text
        assert "Hi Asking" not in text
        assert "Asking!" not in text

    async def test_known_hometown_response(self):
        agent = RecoveryCoachAgent()
        req = CoachRequest(
            student_id="student_001",
            user_message="Where am I from?",
            conversation_history=[
                CoachMessageItem(role="user", content="My name is Ajmal and I am from Mangalore."),
                CoachMessageItem(role="assistant", content="Ajmal."),
            ],
        )
        resp = await agent.generate_response(req)
        assert "Mangalore" in resp.response_text

    async def test_where_are_you_from_ai_response(self):
        agent = RecoveryCoachAgent()
        req = CoachRequest(
            student_id="student_001",
            user_message="Where are you from?",
        )
        resp = await agent.generate_response(req)
        assert "EduGuardian" in resp.response_text or "AI" in resp.response_text
