"""
Centralized Guardrails Service Manager for EduGuardian AI.

Coordinates Input and Output guardrail evaluators for the LangGraph Orchestrator
and FastAPI services.

Phase 8.3 addition: Every guardrail decision is recorded exactly once in
GuardrailMetrics immediately after the guardrail evaluator returns.
No raw content, user messages, or academic values are stored in metrics.
"""
from __future__ import annotations

import logging
from typing import Any
from functools import lru_cache

from chatbot.backend.guardrails.base import BaseInputGuardrail, BaseOutputGuardrail
from chatbot.backend.guardrails.input_guardrail import InputGuardrail
from chatbot.backend.guardrails.output_guardrail import OutputGuardrail
from chatbot.backend.guardrails.metrics import GuardrailMetrics, infer_reason_code
from chatbot.backend.schemas.guardrails import GuardrailResult
from chatbot.backend.schemas.student import StudentContext

logger = logging.getLogger(__name__)


class GuardrailsService:
    """
    Coordinator managing input and output safety checks across the EduGuardian pipeline.

    Metrics are recorded centrally here — individual guardrail classes do not
    need to know about the metrics system, preventing double-counting.
    """

    def __init__(
        self,
        input_guardrail: BaseInputGuardrail | None = None,
        output_guardrail: BaseOutputGuardrail | None = None,
    ) -> None:
        self._input_guardrail = input_guardrail or InputGuardrail()
        self._output_guardrail = output_guardrail or OutputGuardrail()

    def validate_input(
        self,
        user_message: str,
        student_context: StudentContext | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GuardrailResult:
        """
        Runs input guardrail checks on incoming user messages.
        Records the decision in GuardrailMetrics exactly once.
        """
        result = self._input_guardrail.evaluate(
            user_message=user_message,
            student_context=student_context,
            metadata=metadata,
        )

        # ── Record metrics — no raw content stored ─────────────────────────
        reason_code = infer_reason_code(result.reason or "")
        conversation_id = (metadata or {}).get("conversation_id")
        GuardrailMetrics.record(
            action=result.action.value,
            category=result.category.value,
            reason_code=reason_code,
            guardrail="input",
            conversation_id=conversation_id,
        )

        return result

    def validate_output(
        self,
        response_text: str,
        student_context: StudentContext | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GuardrailResult:
        """
        Runs output guardrail checks on outgoing assistant responses.
        Records the decision in GuardrailMetrics exactly once.

        Note: OutputGuardrail internally invokes AcademicGroundingGuardrail.
        The combined result is recorded here as a single event — no
        double-counting of the grounding sub-check.
        """
        result = self._output_guardrail.evaluate(
            response_text=response_text,
            student_context=student_context,
            metadata=metadata,
        )

        # ── Record metrics — no raw content stored ─────────────────────────
        reason_code = infer_reason_code(result.reason or "")
        conversation_id = (metadata or {}).get("conversation_id")
        GuardrailMetrics.record(
            action=result.action.value,
            category=result.category.value,
            reason_code=reason_code,
            guardrail="output",
            conversation_id=conversation_id,
        )

        return result

    @staticmethod
    def metrics_snapshot() -> dict[str, Any]:
        """
        Returns the current in-memory guardrail metrics snapshot.

        Safe to call from tests and health endpoints — contains only
        aggregate counters, never raw user content or secrets.
        """
        return GuardrailMetrics.snapshot()


@lru_cache(maxsize=1)
def get_guardrails_service() -> GuardrailsService:
    """Returns the singleton GuardrailsService instance."""
    return GuardrailsService()
