"""
Input Guardrail for EduGuardian AI.

Evaluates incoming user messages before orchestration:
- Detects prompt injection, jailbreak attempts, and system prompt extraction
- Prevents credential/API key theft and internal system context dumps
- Allows legitimate authorized academic queries (attendance, grades, subjects)
- Allows natural greetings, casual talk, and emotional support requests
"""
from __future__ import annotations

import re
import logging
from typing import Any

from chatbot.backend.guardrails.base import BaseInputGuardrail
from chatbot.backend.schemas.guardrails import GuardrailAction, GuardrailCategory, GuardrailResult
from chatbot.backend.schemas.student import StudentContext

logger = logging.getLogger(__name__)

# ── Prompt Injection & Jailbreak Patterns ─────────────────────────────────────
_PROMPT_INJECTION_PATTERNS = [
    re.compile(r"\bignore\s+(all\s+)?(previous|prior|above|existing)\s+instructions\b", re.IGNORECASE),
    re.compile(r"\b(disregard|forget|override)\s+(all\s+)?(previous|prior|system|developer)\s+(instructions|prompts|rules)\b", re.IGNORECASE),
    re.compile(r"\b(you\s+are\s+now\s+in\s+dan\s+mode|jailbreak|developer\s+mode\s+enabled|unrestricted\s+mode)\b", re.IGNORECASE),
    re.compile(r"\b(show|reveal|display|tell|print|dump|output|leak)\s+(me\s+)?(your\s+)?(system\s+prompt|developer\s+prompt|hidden\s+instructions|internal\s+instructions|system\s+instructions|initial\s+prompt)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(is|are)\s+your\s+(system\s+prompt|developer\s+instructions|secret\s+instructions)\b", re.IGNORECASE),
]

# ── Secret, Key & Credential Extraction Patterns ──────────────────────────────
_SECRET_EXTRACTION_PATTERNS = [
    re.compile(r"\b(give|tell|reveal|show|print|leak|output|get)\s+(me\s+)?(the\s+)?(api[ _-]?key|secret[ _-]?key|groq[ _-]?key|groq_api_key|database_url|db_password|jwt_secret|postgres_password|credentials?)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+is\s+(the|your)\s+(api[ _-]?key|groq_api_key|database_url|jwt_secret)\b", re.IGNORECASE),
]

# ── Internal Architecture & Raw Context Extraction Patterns ───────────────────
_INTERNAL_EXTRACTION_PATTERNS = [
    re.compile(r"\b(show|dump|reveal|print|leak)\s+(the\s+)?(a2a\s+payload|studentcontext\s+internals|learninghistory\s+internals|chain[ -]of[ -]thought|internal\s+reasoning\s+steps)\b", re.IGNORECASE),
    re.compile(r"\b(dump|list|show)\s+(all\s+)?(database\s+records|users\s+table|other\s+students|student\s+passwords|raw\s+sql)\b", re.IGNORECASE),
]

# Safe refusal response for system integrity violations
_SAFE_PROMPT_INJECTION_REFUSAL = (
    "I cannot disclose internal system prompts, API keys, or operational configurations. "
    "However, I am fully available to explain concepts, build structured study plans, or assist with your coursework. "
    "What topic would you like to explore?"
)

_SAFE_CREDENTIALS_REFUSAL = (
    "I cannot access or reveal API keys, credentials, or internal system configurations. "
    "I am here to assist with your academic learning, study scheduling, and course concepts. "
    "How can I assist your studies today?"
)

_SAFE_EMPTY_INPUT_REFUSAL = (
    "It looks like your message was empty. Please feel free to ask a course question, "
    "request a study schedule, or explore an academic topic."
)


class InputGuardrail(BaseInputGuardrail):
    """
    Centralized Input Guardrail evaluator protecting EduGuardian endpoints.
    """

    def evaluate(
        self,
        user_message: str,
        student_context: StudentContext | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GuardrailResult:
        """
        Evaluates incoming user text against input safety policies.
        """
        if not user_message or not user_message.strip():
            return GuardrailResult(
                action=GuardrailAction.BLOCK,
                category=GuardrailCategory.SCOPE_RELEVANCE,
                reason="Empty or whitespace-only user input.",
                blocked_response=_SAFE_EMPTY_INPUT_REFUSAL,
            )

        text = user_message.strip()

        # 1. Check for Prompt Injection / Jailbreak / System Prompt Extraction
        for pattern in _PROMPT_INJECTION_PATTERNS:
            if pattern.search(text):
                logger.warning("InputGuardrail: Prompt injection attempt detected: %r", text[:80])
                return GuardrailResult(
                    action=GuardrailAction.BLOCK,
                    category=GuardrailCategory.PROMPT_INJECTION,
                    reason="Detected attempt to override instructions or extract system prompt.",
                    blocked_response=_SAFE_PROMPT_INJECTION_REFUSAL,
                    metadata={"matched_pattern": pattern.pattern},
                )

        # 2. Check for Secret & Credential Extraction
        for pattern in _SECRET_EXTRACTION_PATTERNS:
            if pattern.search(text):
                logger.warning("InputGuardrail: Credential extraction attempt detected: %r", text[:80])
                return GuardrailResult(
                    action=GuardrailAction.BLOCK,
                    category=GuardrailCategory.PRIVACY_SENSITIVE_DATA,
                    reason="Detected attempt to extract API keys or secret credentials.",
                    blocked_response=_SAFE_CREDENTIALS_REFUSAL,
                    metadata={"matched_pattern": pattern.pattern},
                )

        # 3. Check for Internal Payload / Context Dump Extraction
        for pattern in _INTERNAL_EXTRACTION_PATTERNS:
            if pattern.search(text):
                logger.warning("InputGuardrail: Internal context dump attempt detected: %r", text[:80])
                return GuardrailResult(
                    action=GuardrailAction.BLOCK,
                    category=GuardrailCategory.PRIVACY_SENSITIVE_DATA,
                    reason="Detected attempt to extract raw internal architecture context or payloads.",
                    blocked_response=_SAFE_CREDENTIALS_REFUSAL,
                    metadata={"matched_pattern": pattern.pattern},
                )

        # 4. Legitimate Academic & Conversational Queries
        # Normal questions, greetings ("hi", "how are you"), attendance queries ("what is my attendance?"),
        # emotional expressions ("feeling stressed"), and study requests are all ALLOWED.
        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            category=GuardrailCategory.NONE,
            reason="Input message satisfies all safety and scope boundaries.",
            sanitized_text=text,
        )
