"""
Centralized Guardrails System for EduGuardian AI — Phases 8.1 / 8.2 / 8.3.

Exports:
- InputGuardrail: Evaluates prompt injection, credential theft, and scope
- OutputGuardrail: Evaluates secret leakage, reasoning tags, and deficit labels
- AcademicGroundingGuardrail: Deterministic academic claim verification
- GuardrailsService: Coordinator, metrics recorder, and dependency provider
- GuardrailMetrics: Thread-safe in-memory observability counters
- ReasonCode: Stable reason codes for metric aggregation
- Base interfaces and schemas
"""
from __future__ import annotations

from chatbot.backend.schemas.guardrails import (
    GuardrailAction,
    GuardrailCategory,
    GuardrailResult,
)
from chatbot.backend.guardrails.base import (
    BaseInputGuardrail,
    BaseOutputGuardrail,
)
from chatbot.backend.guardrails.input_guardrail import InputGuardrail
from chatbot.backend.guardrails.output_guardrail import OutputGuardrail
from chatbot.backend.guardrails.academic_grounding import AcademicGroundingGuardrail
from chatbot.backend.guardrails.metrics import GuardrailMetrics, ReasonCode, infer_reason_code
from chatbot.backend.guardrails.service import (
    GuardrailsService,
    get_guardrails_service,
)

__all__ = [
    "GuardrailAction",
    "GuardrailCategory",
    "GuardrailResult",
    "BaseInputGuardrail",
    "BaseOutputGuardrail",
    "InputGuardrail",
    "OutputGuardrail",
    "AcademicGroundingGuardrail",
    "GuardrailMetrics",
    "ReasonCode",
    "infer_reason_code",
    "GuardrailsService",
    "get_guardrails_service",
]
