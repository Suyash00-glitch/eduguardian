"""
Output Guardrail for EduGuardian AI.

Evaluates and sanitizes outgoing assistant responses before delivery to students:
- Strips leaked API keys, database connection strings, and authentication tokens
- Strips raw <think>...</think> reasoning tags
- Sanitizes forbidden deficit-based/stigmatizing labels
- Removes corrupted greetings and internal metadata dumps
"""
from __future__ import annotations

import re
import logging
from typing import Any

from chatbot.backend.guardrails.base import BaseOutputGuardrail
from chatbot.backend.guardrails.academic_grounding import AcademicGroundingGuardrail
from chatbot.backend.schemas.guardrails import GuardrailAction, GuardrailCategory, GuardrailResult
from chatbot.backend.schemas.student import StudentContext

logger = logging.getLogger(__name__)

# ── Credential & Key Leakage Patterns ─────────────────────────────────────────
_GROQ_KEY_PATTERN = re.compile(r"\bgsk_[a-zA-Z0-9]{20,}\b")
_DATABASE_URL_PATTERN = re.compile(r"postgresql(?:\+asyncpg)?://[^\s:]+:[^\s@]+@[^\s/]+/[^\s]+", re.IGNORECASE)
_JWT_TOKEN_PATTERN = re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b")

# ── Reasoning & Internal Leakage Patterns ─────────────────────────────────────
_THINK_TAG_PATTERN = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)
_INTERNAL_ENVELOPE_PATTERN = re.compile(r"(?:A2ATaskEnvelope|A2AResultEnvelope|InsightResponse|PlanResponse)\([^\)]*\)")

# ── Forbidden Stigmatizing Labels ─────────────────────────────────────────────
_FORBIDDEN_TERMS_PATTERN = re.compile(
    r"\b("
    r"high[- ]risk|at[- ]risk|risk level|risk score|dropout risk"
    r"|weak student|dull student|poor student|low[- ]performing student"
    r"|failing student|predicted to fail|failure risk|failure prediction"
    r"|underperformer|academically weak|below[- ]average student"
    r"|support intensity|intensive support|intervention required"
    r"|concerning student|problematic student"
    r")\b",
    re.IGNORECASE,
)

# ── Bogus Greeting Pattern ───────────────────────────────────────────────────
_BOGUS_GREETING_PATTERN = re.compile(
    r"\bhi\s+(from|asking|neural|what|where|who|why|how|student|test\s+student|user)\b[!.,]?",
    re.IGNORECASE,
)


class OutputGuardrail(BaseOutputGuardrail):
    """
    Centralized Output Guardrail ensuring all outgoing text meets safety and quality standards.
    """

    def __init__(
        self,
        academic_grounding: BaseOutputGuardrail | None = None,
    ) -> None:
        self._academic_grounding = academic_grounding or AcademicGroundingGuardrail()

    def evaluate(
        self,
        response_text: str,
        student_context: StudentContext | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GuardrailResult:
        """
        Evaluates and sanitizes outgoing assistant response text.
        """
        if not response_text:
            return GuardrailResult(
                action=GuardrailAction.ALLOW,
                category=GuardrailCategory.NONE,
                sanitized_text="",
            )

        text = response_text
        modified = False
        categories_triggered: list[GuardrailCategory] = []
        reasons: list[str] = []

        # 1. Check for & Redact Credential Leaks
        if _GROQ_KEY_PATTERN.search(text):
            text = _GROQ_KEY_PATTERN.sub("[REDACTED_API_KEY]", text)
            modified = True
            categories_triggered.append(GuardrailCategory.OUTPUT_SAFETY)
            reasons.append("Redacted leaked Groq API key")

        if _DATABASE_URL_PATTERN.search(text):
            text = _DATABASE_URL_PATTERN.sub("[REDACTED_DATABASE_URL]", text)
            modified = True
            categories_triggered.append(GuardrailCategory.OUTPUT_SAFETY)
            reasons.append("Redacted leaked database connection string")

        if _JWT_TOKEN_PATTERN.search(text):
            text = _JWT_TOKEN_PATTERN.sub("[REDACTED_AUTH_TOKEN]", text)
            modified = True
            categories_triggered.append(GuardrailCategory.OUTPUT_SAFETY)
            reasons.append("Redacted leaked JWT authentication token")

        # 2. Strip Thinking & Chain-of-Thought Tags
        if _THINK_TAG_PATTERN.search(text):
            text = _THINK_TAG_PATTERN.sub("", text).strip()
            modified = True
            categories_triggered.append(GuardrailCategory.OUTPUT_SAFETY)
            reasons.append("Stripped <think> reasoning tags")

        # 3. Strip Raw Internal Envelope Strings
        if _INTERNAL_ENVELOPE_PATTERN.search(text):
            text = _INTERNAL_ENVELOPE_PATTERN.sub("", text).strip()
            modified = True
            categories_triggered.append(GuardrailCategory.OUTPUT_SAFETY)
            reasons.append("Stripped internal A2A envelope representation")

        # 4. Sanitize Forbidden Deficit-Based / Stigmatizing Terms
        if _FORBIDDEN_TERMS_PATTERN.search(text):
            text = _FORBIDDEN_TERMS_PATTERN.sub("student with areas to strengthen", text)
            modified = True
            categories_triggered.append(GuardrailCategory.EMOTIONAL_SUPPORT)
            reasons.append("Sanitized stigmatizing deficit labels to supportive language")

        # 5. Fix Bogus Greetings
        if _BOGUS_GREETING_PATTERN.search(text):
            resolved_name = (student_context.student_name or "").strip() if student_context else ""
            clean_greeting = f"Hi {resolved_name}!" if resolved_name else "Hi!"
            text = _BOGUS_GREETING_PATTERN.sub(clean_greeting, text)
            modified = True
            reasons.append("Corrected corrupted greeting pattern")

        # 6. Academic Grounding Verification (Validate attendance, marks, grades, deadlines against StudentContext)
        grounding_result = self._academic_grounding.evaluate(
            response_text=text,
            student_context=student_context,
            metadata=metadata,
        )
        if grounding_result.sanitized_text is not None and grounding_result.sanitized_text != text:
            text = grounding_result.sanitized_text
            modified = True
            categories_triggered.append(GuardrailCategory.ACADEMIC_GROUNDING)
            reasons.append(grounding_result.reason or "Academically grounded claims")

        text = text.strip()

        if modified:
            primary_category = categories_triggered[0] if categories_triggered else GuardrailCategory.OUTPUT_SAFETY
            return GuardrailResult(
                action=GuardrailAction.REVISE,
                category=primary_category,
                reason="; ".join(reasons),
                sanitized_text=text,
                metadata={"modifications": reasons},
            )

        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            category=GuardrailCategory.NONE,
            reason="Output satisfies all safety and privacy standards.",
            sanitized_text=text,
        )
