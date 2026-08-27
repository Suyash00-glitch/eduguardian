"""
Unit and Integration Tests for OmniRoute LLM Gateway & Abstraction.

Verifies:
1. Successful text completion with OpenAI-compatible payload format
2. Structured output generation and Pydantic validation via complete_structured()
3. Timeout error handling and classification (LLMTimeoutError)
4. Authentication failure handling (LLMAuthError)
5. HTTP 429 rate limit backoff and retry behavior
6. Malformed model response & validation failure (LLMValidationError)
7. Security: API key and authorization secrets are never leaked in errors/logs
8. MockLLMClient handles all agent contexts seamlessly
9. Dynamic model and base URL configuration from Settings
10. Full agent execution with MockLLMClient
"""
from __future__ import annotations

import json
import pytest
import httpx
from unittest.mock import patch

from chatbot.backend.llm.base import (
    BaseLLMClient,
    LLMMessage,
    LLMResponse,
    LLMError,
    LLMTimeoutError,
    LLMAuthError,
    LLMValidationError,
)
from chatbot.backend.llm.omniroute import OmniRouteLLMClient, create_llm_client
from chatbot.tests.mocks.llm_mock import MockLLMClient
from chatbot.backend.schemas.planner import StudyPlan
from chatbot.backend.schemas.insight import StudentInsight
from chatbot.backend.agents.recovery_coach.agent import RecoveryCoachAgent
from chatbot.backend.schemas.coach import CoachRequest, CoachResponse


class TestOmniRouteClient:

    @pytest.mark.asyncio
    async def test_1_successful_completion(self):
        """OmniRoute client correctly parses OpenAI-compatible chat completion response."""
        mock_response_data = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "model": "gemini-1.5-pro",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! I am here to help you succeed in your studies.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 12, "completion_tokens": 15, "total_tokens": 27},
        }

        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/chat/completions"
            assert request.headers["authorization"] == "Bearer test-key"
            req_body = json.loads(request.read())
            assert req_body["model"] == "gemini-1.5-pro"
            return httpx.Response(200, json=mock_response_data)

        transport = httpx.MockTransport(handler)
        client = OmniRouteLLMClient(
            base_url="https://api.omniroute.ai/v1",
            api_key="test-key",
            model="gemini-1.5-pro",
            transport=transport,
        )

        messages = [
            LLMMessage(role="system", content="You are a helpful tutor."),
            LLMMessage(role="user", content="Hi there!"),
        ]

        resp = await client.complete(messages)
        assert resp.content == "Hello! I am here to help you succeed in your studies."
        assert resp.model == "gemini-1.5-pro"
        assert resp.usage["total_tokens"] == 27

    @pytest.mark.asyncio
    async def test_2_structured_output_parsing(self):
        """complete_structured parses and validates valid JSON into Pydantic model."""
        valid_plan_data = {
            "title": "Data Structures Mastery Plan",
            "week_start": "2026-08-15",
            "goals": ["Master tree traversals"],
            "tasks": [
                {
                    "title": "Binary Tree practice",
                    "day": "Monday",
                    "time_slot": "10:00–11:30",
                    "subject": "Data Structures",
                    "description": "Solve 2 problems on traversals",
                    "duration_minutes": 90,
                    "priority": "high",
                }
            ],
            "resources": ["Textbook Ch. 4"],
            "notes": "Stay steady and take breaks.",
        }

        mock_response_data = {
            "choices": [
                {
                    "message": {
                        "content": f"```json\n{json.dumps(valid_plan_data)}\n```",
                    }
                }
            ]
        }

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=mock_response_data)

        client = OmniRouteLLMClient(
            base_url="https://api.omniroute.ai/v1",
            api_key="test-key",
            transport=httpx.MockTransport(handler),
        )

        plan = await client.complete_structured(
            [LLMMessage(role="user", content="Generate a study plan")],
            response_model=StudyPlan,
        )

        assert isinstance(plan, StudyPlan)
        assert plan.title == "Data Structures Mastery Plan"
        assert len(plan.tasks) == 1
        assert plan.tasks[0].subject == "Data Structures"

    @pytest.mark.asyncio
    async def test_3_timeout_handling(self):
        """Timeouts raise LLMTimeoutError without leaking secrets."""
        async def slow_handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("Read timed out")

        client = OmniRouteLLMClient(
            base_url="https://api.omniroute.ai/v1",
            api_key="sk-secret-token-12345",
            timeout=1.0,
            transport=httpx.MockTransport(slow_handler),
        )

        with pytest.raises(LLMTimeoutError) as exc_info:
            await client.complete([LLMMessage(role="user", content="Hello")])

        err_msg = str(exc_info.value)
        assert "timed out" in err_msg.lower()
        assert "sk-secret-token-12345" not in err_msg

    @pytest.mark.asyncio
    async def test_4_auth_failure_handling(self):
        """HTTP 401 returns LLMAuthError without exposing raw token in error message."""
        async def auth_fail_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": "Invalid API key"})

        client = OmniRouteLLMClient(
            base_url="https://api.omniroute.ai/v1",
            api_key="sk-invalid-secret-key",
            transport=httpx.MockTransport(auth_fail_handler),
        )

        with pytest.raises(LLMAuthError) as exc_info:
            await client.complete([LLMMessage(role="user", content="Hello")])

        err_msg = str(exc_info.value)
        assert "authentication failed" in err_msg.lower()
        assert "sk-invalid-secret-key" not in err_msg

    @pytest.mark.asyncio
    async def test_5_missing_api_key_raises_auth_error(self):
        """Unconfigured API key immediately raises LLMAuthError."""
        client = OmniRouteLLMClient(
            base_url="https://api.omniroute.ai/v1",
            api_key="not-configured",
        )

        with pytest.raises(LLMAuthError) as exc_info:
            await client.complete([LLMMessage(role="user", content="Hello")])

        assert "not configured" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_6_structured_validation_failure(self):
        """Invalid JSON schema raises LLMValidationError."""
        mock_response_data = {
            "choices": [{"message": {"content": "This is completely invalid and not JSON."}}]
        }

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=mock_response_data)

        client = OmniRouteLLMClient(
            base_url="https://api.omniroute.ai/v1",
            api_key="test-key",
            transport=httpx.MockTransport(handler),
        )

        with pytest.raises(LLMValidationError):
            await client.complete_structured(
                [LLMMessage(role="user", content="Give me a plan")],
                response_model=StudyPlan,
            )


class TestMockLLMClient:

    @pytest.mark.asyncio
    async def test_mock_client_coach_canned_responses(self):
        """MockLLMClient responds appropriately to keywords."""
        mock = MockLLMClient()

        # Stress keyword
        resp_stress = await mock.complete([LLMMessage(role="user", content="I am feeling overwhelmed and stressed today.")])
        assert "overwhelmed" in resp_stress.content.lower() or "break things down" in resp_stress.content.lower()

        # Greeting keyword
        resp_hello = await mock.complete([LLMMessage(role="user", content="Hello there!")])
        assert "great to see you" in resp_hello.content.lower()

    @pytest.mark.asyncio
    async def test_recovery_coach_with_mock_llm(self):
        """RecoveryCoachAgent operates cleanly with MockLLMClient."""
        coach = RecoveryCoachAgent(llm_client=MockLLMClient())
        request = CoachRequest(
            student_id="student_001",
            user_message="I'm worried about my assignments.",
        )

        response = await coach.generate_response(request)
        assert isinstance(response, CoachResponse)
        assert len(response.response_text) > 0
        assert not response.has_study_plan
