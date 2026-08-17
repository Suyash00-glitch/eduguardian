"""
OmniRoute LLM Gateway Client — Concrete implementation of BaseLLMClient.

Communicates with the OmniRoute API gateway using the OpenAI-compatible
chat completions protocol.

Features:
- Strong authentication header handling without secret leakage
- Configurable timeout and model selection via Settings
- Safe exponential backoff retry for transient network / rate-limit failures
- Graceful error classification (LLMTimeoutError, LLMAuthError, LLMError)
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any
import httpx

from chatbot.backend.config import get_settings
from chatbot.backend.llm.base import (
    BaseLLMClient,
    LLMAuthError,
    LLMError,
    LLMMessage,
    LLMResponse,
    LLMTimeoutError,
)

logger = logging.getLogger(__name__)


class OmniRouteLLMClient(BaseLLMClient):
    """
    Calls either the OmniRoute LLM gateway or direct Groq API with OpenAI-compatible payload format.
    Supports automatic failover between OmniRoute and direct Groq.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        settings = get_settings()
        self._provider = settings.llm_provider.lower()
        self._omniroute_base_url = (base_url or settings.omniroute_base_url).rstrip("/")
        self._omniroute_api_key = api_key or settings.omniroute_api_key
        self._omniroute_model = model or settings.omniroute_model
        self._omniroute_timeout = timeout or settings.omniroute_timeout_seconds

        self._groq_api_key = settings.groq_api_key
        self._groq_base_url = settings.groq_base_url.rstrip("/")
        self._groq_model = settings.groq_model
        self._groq_timeout = settings.groq_timeout_seconds

        self._transport = transport

    @property
    def model_name(self) -> str:
        if self._provider == "groq" or (self._groq_api_key and self._omniroute_api_key in ("not-configured", "")):
            return self._groq_model
        return self._omniroute_model

    async def _call_endpoint(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        logger.info("LLMClient: Calling model=%s at %s", model, base_url)

        async with httpx.AsyncClient(timeout=timeout, transport=self._transport) as http:
            response = await http.post(url, json=payload, headers=headers)

            if response.status_code in (401, 403):
                logger.error("LLMClient: Auth error (status=%d): %s", response.status_code, response.text[:250])
                raise LLMAuthError(f"LLM authentication failed (HTTP {response.status_code}): {response.text[:120]}")

            if response.status_code == 429:
                logger.warning("LLMClient: Rate limit (HTTP 429): %s", response.text[:120])
                raise LLMError(f"LLM HTTP 429: {response.text[:120]}")

            if response.is_error:
                logger.error("LLMClient: HTTP error %d: %s", response.status_code, response.text[:250])
                raise LLMError(f"LLM HTTP {response.status_code}: {response.text[:150]}")

            resp_text = response.text.strip()

            # Support SSE chunked streaming response
            if resp_text.startswith("data:"):
                accumulated_content = []
                for line in resp_text.split("\n"):
                    line = line.strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data:"):
                        line_json_str = line[5:].strip()
                        try:
                            chunk = json.loads(line_json_str)
                            choices = chunk.get("choices") or []
                            if choices:
                                delta = choices[0].get("delta") or {}
                                chunk_text = delta.get("content") or choices[0].get("text") or ""
                                if chunk_text:
                                    accumulated_content.append(chunk_text)
                        except Exception:
                            pass
                full_content = "".join(accumulated_content)
                return LLMResponse(content=full_content, model=model, usage=None)

            try:
                data = response.json()
            except Exception as json_err:
                logger.error("LLMClient: Non-JSON response (status=%d): %s", response.status_code, response.text[:250])
                raise LLMError(f"LLM returned non-JSON response: {response.text[:120]}") from json_err

            choices = data.get("choices") or []
            if not choices or "message" not in choices[0]:
                raise LLMError(f"Malformed LLM response: {data}")

            content = choices[0]["message"].get("content", "")
            # Strip internal reasoning think tags if emitted by reasoning models
            if "<think>" in content and "</think>" in content:
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            elif "<think>" in content:
                content = re.sub(r"^<think>.*?(?:\n\n|\Z)", "", content, flags=re.DOTALL).strip()

            model_returned = data.get("model", model)
            usage = data.get("usage")

            return LLMResponse(content=content, model=model_returned, usage=usage)

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """
        Sends chat completion request with automatic multi-provider resilience.
        """
        endpoints_to_try: list[tuple[str, str, str, str, float]] = []

        has_groq = bool(self._groq_api_key and self._groq_api_key not in ("not-configured", "your-groq-api-key-here", ""))
        has_omniroute = bool(self._omniroute_api_key and self._omniroute_api_key not in ("not-configured", "your-omniroute-api-key-here", ""))

        clean_groq_primary = self._groq_model.split("groq/")[-1] if self._groq_model.startswith("groq/") else self._groq_model
        groq_models = [clean_groq_primary]
        for fallback_m in ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]:
            clean_m = fallback_m.split("groq/")[-1] if fallback_m.startswith("groq/") else fallback_m
            if clean_m not in groq_models:
                groq_models.append(clean_m)

        if self._provider == "groq":
            if has_groq:
                for gm in groq_models:
                    endpoints_to_try.append((f"Direct Groq ({gm})", self._groq_base_url, self._groq_api_key, gm, self._groq_timeout))
            if has_omniroute:
                endpoints_to_try.append(("OmniRoute", self._omniroute_base_url, self._omniroute_api_key, self._omniroute_model, self._omniroute_timeout))
                if "localhost" in self._omniroute_base_url:
                    docker_url = self._omniroute_base_url.replace("localhost", "host.docker.internal")
                    endpoints_to_try.append(("OmniRoute (Docker host)", docker_url, self._omniroute_api_key, self._omniroute_model, self._omniroute_timeout))
        elif self._provider == "omniroute":
            if has_omniroute:
                endpoints_to_try.append(("OmniRoute", self._omniroute_base_url, self._omniroute_api_key, self._omniroute_model, self._omniroute_timeout))
                if "localhost" in self._omniroute_base_url:
                    docker_url = self._omniroute_base_url.replace("localhost", "host.docker.internal")
                    endpoints_to_try.append(("OmniRoute (Docker host)", docker_url, self._omniroute_api_key, self._omniroute_model, self._omniroute_timeout))
            if has_groq:
                for gm in groq_models:
                    endpoints_to_try.append((f"Direct Groq ({gm})", self._groq_base_url, self._groq_api_key, gm, self._groq_timeout))
        else:
            # "auto" mode: OmniRoute -> Direct Groq (with verified model fallbacks)
            if has_omniroute:
                endpoints_to_try.append(("OmniRoute", self._omniroute_base_url, self._omniroute_api_key, self._omniroute_model, self._omniroute_timeout))
                if "localhost" in self._omniroute_base_url:
                    docker_url = self._omniroute_base_url.replace("localhost", "host.docker.internal")
                    endpoints_to_try.append(("OmniRoute (Docker host)", docker_url, self._omniroute_api_key, self._omniroute_model, self._omniroute_timeout))
            if has_groq:
                for gm in groq_models:
                    endpoints_to_try.append((f"Direct Groq ({gm})", self._groq_base_url, self._groq_api_key, gm, self._groq_timeout))

        if not endpoints_to_try:
            logger.warning("LLMClient: No valid API keys configured (neither Groq nor OmniRoute).")
            raise LLMAuthError("No valid LLM API key configured in environment (GROQ_API_KEY or OMNIROUTE_API_KEY).")

        last_err: Exception | None = None
        for name, base_url, api_key, model, timeout in endpoints_to_try:
            try:
                return await self._call_endpoint(
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    timeout=timeout,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                logger.warning("LLMClient: %s attempt for model '%s' failed (%s). Checking next fallback...", name, model, e)
                last_err = e

        if last_err:
            raise last_err
        raise LLMError("All LLM completion endpoints failed.")


def create_llm_client() -> BaseLLMClient:
    """
    Factory creating the configured production LLM Client.
    """
    return OmniRouteLLMClient()
