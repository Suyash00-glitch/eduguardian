"""
BaseLLMClient — Abstract LLM Service Interface.

Every agent interacts with this unified interface.
Decouples agent logic from specific LLM providers (OmniRoute, Gemini, OpenAI, Mock).
"""
from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, TypeVar
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_JSON_BLOCK_REGEX = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


@dataclass
class LLMMessage:
    """A single message in a chat completion request."""
    role: str   # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    """Standardized response from an LLM completion call."""
    content: str
    model: str
    usage: dict[str, Any] | None = None


class LLMError(Exception):
    """Base exception for LLM operations."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when an LLM request exceeds configured timeout."""
    pass


class LLMAuthError(LLMError):
    """Raised on authentication or authorization failure with LLM gateway."""
    pass


class LLMValidationError(LLMError):
    """Raised when model response fails schema validation."""
    pass


class BaseLLMClient(ABC):
    """
    Abstract LLM client interface.

    Agents invoke complete(), complete_simple(), or complete_structured()
    without knowledge of underlying transport or provider specifics.
    """

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """
        Send chat messages and return the model's response.

        Args:
            messages: Conversation history + current prompt.
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
            max_tokens: Maximum response length.

        Returns:
            LLMResponse with content, model name, and token usage.
        """
        ...

    async def complete_simple(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Convenience wrapper taking system + user prompt and returning text.
        """
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]
        response = await self.complete(messages, temperature=temperature, max_tokens=max_tokens)
        return response.content

    async def complete_structured(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> T:
        """
        Requests model output and parses/validates it into a Pydantic schema.

        Args:
            messages: Chat messages.
            response_model: Target Pydantic BaseModel subclass.
            temperature: Low temperature for reliable structured generation.
            max_tokens: Max output tokens.

        Returns:
            An instance of response_model.

        Raises:
            LLMValidationError: If response cannot be parsed or validated.
        """
        # Ensure schema structure instruction is appended
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        system_addon = (
            f"\n\nIMPORTANT: You must respond ONLY with valid JSON conforming to this schema:\n"
            f"{schema_json}\nDo not include any conversational preamble or outro outside the JSON."
        )

        enhanced_messages = list(messages)
        if enhanced_messages and enhanced_messages[0].role == "system":
            enhanced_messages[0] = LLMMessage(
                role="system",
                content=enhanced_messages[0].content + system_addon,
            )
        else:
            enhanced_messages.insert(0, LLMMessage(role="system", content=system_addon))

        response = await self.complete(
            enhanced_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        raw_text = response.content.strip()

        # Extract JSON from markdown code block if present
        match = _JSON_BLOCK_REGEX.search(raw_text)
        if match:
            json_str = match.group(1).strip()
        else:
            json_str = raw_text

        try:
            parsed_dict = json.loads(json_str)
            return response_model.model_validate(parsed_dict)
        except Exception as exc:
            logger.error("LLM Structured Validation Failed: %s | Raw response: %r", exc, raw_text[:200])
            raise LLMValidationError(f"Model output failed {response_model.__name__} validation: {exc}") from exc
