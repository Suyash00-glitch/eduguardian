"""
Guardrail Observability & Metrics for EduGuardian AI — Phase 8.3.

Provides a lightweight, thread-safe, in-memory metrics store that tracks
guardrail decisions (ALLOW / BLOCK / REWRITE / FLAG) without storing any
raw user content, StudentContext data, secrets, or personally-identifiable
information.

Architecture:
    GuardrailMetrics  — singleton counter store (threading.Lock protected)
    GuardrailEvent    — immutable structured log event
    ReasonCode        — stable, enumerated reason codes for aggregation

Privacy guarantees:
    - Only metadata is stored (category, action, reason_code, guardrail source).
    - No user messages, student IDs, or academic values are recorded.
    - Snapshot output is a plain dict of counters — safe to expose via API.
"""
from __future__ import annotations

import logging
import threading
from collections import defaultdict
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ── Stable Reason Codes ───────────────────────────────────────────────────────

class ReasonCode(str, Enum):
    """
    Stable, enumerated reason codes for guardrail events.

    These codes are intentionally coarse-grained so they can be safely
    aggregated and compared across releases without exposing message content.
    """

    # ── Input Guardrail ───────────────────────────────────────────────────
    PROMPT_INJECTION          = "prompt_injection"
    SYSTEM_PROMPT_EXTRACTION  = "system_prompt_extraction"
    CREDENTIAL_EXTRACTION     = "credential_extraction"
    INTERNAL_PAYLOAD_REQUEST  = "internal_payload_request"
    SCOPE_VIOLATION           = "scope_violation"
    EMPTY_INPUT               = "empty_input"

    # ── Output Guardrail ──────────────────────────────────────────────────
    CREDENTIAL_LEAK           = "credential_leak"
    THINK_TAG                 = "think_tag"
    INTERNAL_METADATA         = "internal_metadata"
    STIGMATIZING_LANGUAGE     = "stigmatizing_language"
    BOGUS_GREETING            = "bogus_greeting"

    # ── Academic Grounding Guardrail ──────────────────────────────────────
    UNSUPPORTED_ATTENDANCE    = "unsupported_attendance"
    UNSUPPORTED_MARK          = "unsupported_mark"
    UNSUPPORTED_GRADE         = "unsupported_grade"
    UNSUPPORTED_SUBJECT       = "unsupported_subject"
    UNSUPPORTED_DEADLINE      = "unsupported_deadline"
    UNSUPPORTED_ASSIGNMENT_STATUS = "unsupported_assignment_status"
    UNSUPPORTED_PROFILE_CLAIM = "unsupported_profile_claim"
    UNSUPPORTED_SEMESTER      = "unsupported_semester"

    # ── Generic ───────────────────────────────────────────────────────────
    CLEAN                     = "clean"
    UNKNOWN                   = "unknown"


# ── Per-category counter dict ─────────────────────────────────────────────────

def _empty_category_counters() -> dict[str, int]:
    return {"allowed": 0, "blocked": 0, "rewritten": 0, "flagged": 0}


# ── GuardrailMetrics Singleton ────────────────────────────────────────────────

class GuardrailMetrics:
    """
    Thread-safe, in-memory guardrail metrics store.

    All mutation is serialised via a single threading.Lock so it is safe under
    FastAPI's default threadpool executor as well as from sync code paths.

    This class intentionally uses class-level state (not instance state) so
    there is a single global counter store without needing an explicit singleton
    pattern or dependency injection.
    """

    _lock: threading.Lock = threading.Lock()

    # ── Global counters ───────────────────────────────────────────────────
    _total_checks: int = 0
    _total_allowed: int = 0
    _total_blocked: int = 0
    _total_rewritten: int = 0
    _total_flagged: int = 0

    # ── Per-category counters: {category_key: {action: count}} ───────────
    _by_category: dict[str, dict[str, int]] = defaultdict(_empty_category_counters)

    # ── Per-reason-code counters: {reason_code: count} ───────────────────
    _by_reason_code: dict[str, int] = defaultdict(int)

    # ─────────────────────────────────────────────────────────────────────

    @classmethod
    def record(
        cls,
        *,
        action: str,
        category: str,
        reason_code: str | ReasonCode = ReasonCode.UNKNOWN,
        guardrail: str = "unknown",
        conversation_id: str | None = None,
    ) -> None:
        """
        Record a single guardrail decision.

        Args:
            action:          "allow" | "block" | "revise" | "modify" | "flag"
            category:        GuardrailCategory value string (e.g. "prompt_injection")
            reason_code:     Stable ReasonCode or string label for this decision.
            guardrail:       Which guardrail produced this result ("input" | "output" | "academic_grounding").
            conversation_id: Optional correlation ID — logged but NOT stored in counters.
        """
        action_lower = action.lower()
        category_key = str(category).lower()
        # Strip "reasoncode." prefix if a full enum repr is passed
        code_key = str(reason_code).lower()
        if "." in code_key:
            code_key = code_key.rsplit(".", 1)[-1]

        with cls._lock:
            cls._total_checks += 1

            if action_lower == "allow":
                cls._total_allowed += 1
                cls._by_category[category_key]["allowed"] += 1
            elif action_lower == "block":
                cls._total_blocked += 1
                cls._by_category[category_key]["blocked"] += 1
            elif action_lower in ("revise", "modify", "rewrite"):
                cls._total_rewritten += 1
                cls._by_category[category_key]["rewritten"] += 1
            else:
                # Treat anything else as flagged
                cls._total_flagged += 1
                cls._by_category[category_key]["flagged"] += 1

            cls._by_reason_code[code_key] += 1

        # Structured log — no user content, just metadata
        logger.info(
            "GuardrailEvent: guardrail=%s category=%s action=%s reason_code=%s%s",
            guardrail,
            category_key,
            action_lower,
            code_key,
            f" conversation_id={conversation_id}" if conversation_id else "",
        )

    @classmethod
    def snapshot(cls) -> dict[str, Any]:
        """
        Returns a safe, read-only metrics snapshot as a plain dictionary.

        This snapshot contains ONLY aggregate counters — no user data,
        no StudentContext, no secrets.
        """
        with cls._lock:
            return {
                "total_checks": cls._total_checks,
                "allowed": cls._total_allowed,
                "blocked": cls._total_blocked,
                "rewritten": cls._total_rewritten,
                "flagged": cls._total_flagged,
                "by_category": {
                    cat: dict(counts)
                    for cat, counts in cls._by_category.items()
                },
                "by_reason_code": dict(cls._by_reason_code),
            }

    @classmethod
    def reset(cls) -> None:
        """
        Resets all in-memory counters to zero.

        FOR TESTING ONLY — does not touch any database records.
        """
        with cls._lock:
            cls._total_checks = 0
            cls._total_allowed = 0
            cls._total_blocked = 0
            cls._total_rewritten = 0
            cls._total_flagged = 0
            cls._by_category.clear()
            cls._by_reason_code.clear()

        logger.debug("GuardrailMetrics: counters reset (testing only)")


# ── Helper: derive reason code from natural-language reason string ─────────────

_REASON_CODE_MAP: list[tuple[str, ReasonCode]] = [
    # Input guardrail triggers
    ("override instructions", ReasonCode.PROMPT_INJECTION),
    ("extract system prompt", ReasonCode.SYSTEM_PROMPT_EXTRACTION),
    ("system prompt", ReasonCode.SYSTEM_PROMPT_EXTRACTION),
    ("credential", ReasonCode.CREDENTIAL_EXTRACTION),
    ("api key", ReasonCode.CREDENTIAL_EXTRACTION),
    ("internal", ReasonCode.INTERNAL_PAYLOAD_REQUEST),
    ("a2a payload", ReasonCode.INTERNAL_PAYLOAD_REQUEST),
    ("scope", ReasonCode.SCOPE_VIOLATION),
    ("empty", ReasonCode.EMPTY_INPUT),

    # Output guardrail triggers
    ("api key", ReasonCode.CREDENTIAL_LEAK),
    ("database", ReasonCode.CREDENTIAL_LEAK),
    ("jwt", ReasonCode.CREDENTIAL_LEAK),
    ("think", ReasonCode.THINK_TAG),
    ("envelope", ReasonCode.INTERNAL_METADATA),
    ("stigmatiz", ReasonCode.STIGMATIZING_LANGUAGE),
    ("deficit", ReasonCode.STIGMATIZING_LANGUAGE),
    ("greeting", ReasonCode.BOGUS_GREETING),

    # Academic grounding
    ("attendance", ReasonCode.UNSUPPORTED_ATTENDANCE),
    ("mark", ReasonCode.UNSUPPORTED_MARK),
    ("grade", ReasonCode.UNSUPPORTED_GRADE),
    ("subject", ReasonCode.UNSUPPORTED_SUBJECT),
    ("deadline", ReasonCode.UNSUPPORTED_DEADLINE),
    ("assignment status", ReasonCode.UNSUPPORTED_ASSIGNMENT_STATUS),
    ("assignment", ReasonCode.UNSUPPORTED_DEADLINE),
    ("profile", ReasonCode.UNSUPPORTED_PROFILE_CLAIM),
    ("semester", ReasonCode.UNSUPPORTED_SEMESTER),
]


def infer_reason_code(reason_text: str) -> ReasonCode:
    """
    Maps a natural-language reason string to the nearest stable ReasonCode.

    This is used by GuardrailsService so that individual guardrails do not
    need to be modified to emit reason codes themselves.
    """
    if not reason_text:
        return ReasonCode.CLEAN

    text_lower = reason_text.lower()
    for fragment, code in _REASON_CODE_MAP:
        if fragment in text_lower:
            return code

    return ReasonCode.UNKNOWN
