"""
Adaptive Teaching Support Strategy Module for EduGuardian AI.

Implements dynamic pedagogical strategy progression for Teach Me mode when
a student demonstrates confusion. Adapts pedagogical strategy without
permanently labeling the student or simply dumping longer text.

Teaching Support Levels:
- Level 0: Normal explanation (concise, beginner-friendly, small example)
- Level 1: Simpler wording + concrete example (simplified vocabulary, 1 concrete example, no jargon)
- Level 2: Real-world analogy (intuitive everyday analogy connected to technical concept)
- Level 3: Step-by-step breakdown (numbered steps with tiny worked tracing example)
- Level 4: Interactive micro-teaching (1-2 sentences on one tiny piece + 1 simple check question)
"""
from __future__ import annotations

import re
from typing import Any
from chatbot.backend.schemas.teaching import TeachingState, TeachingStep


_CONFUSION_PATTERNS = re.compile(
    r"\b("
    r"don'?t\s+understand|didn'?t\s+understand|"
    r"don'?t\s+get\s+it|didn'?t\s+get\s+it|don'?t\s+get\s+this|didn'?t\s+get\s+this|"
    r"not\s+understanding|not\s+getting\s+it|"
    r"explain\s+(?:it\s+)?again|explain\s+differently|explain\s+(?:it\s+)?in\s+another\s+way|"
    r"can\s+you\s+explain\s+(?:it\s+)?(?:again|differently|in\s+simpler\s+words|simpler)?|"
    r"could\s+you\s+explain\s+(?:it\s+)?(?:again|differently|in\s+simpler\s+words|simpler)?|"
    r"tell\s+me\s+again|say\s+that\s+again|"
    r"still\s+(?:don'?t|do\s+not)\s+understand|still\s+(?:don'?t|do\s+not)\s+get\s+it|"
    r"still\s+confused|i'?m\s+(?:still\s+)?confused|i\s+am\s+(?:still\s+)?confused|"
    r"so\s+confused|a\s+bit\s+confused|quite\s+confused|"
    r"i'?m\s+lost|i\s+am\s+lost|you\s+lost\s+me|"
    r"what\s+does\s+(?:that|this)\s+mean|makes?\s+no\s+sense|doesn'?t\s+make\s+sense|"
    r"too\s+complicated|too\s+hard|hard\s+to\s+follow|too\s+complex|"
    r"simpler\s+please|make\s+it\s+simpler|in\s+simple\s+words|simple\s+terms"
    r")\b",
    re.IGNORECASE,
)

STRATEGY_DESCRIPTIONS = {
    0: "Normal explanation (beginner-friendly, concise, small example)",
    1: "Simpler wording + concrete example (simplified vocabulary, 1 concrete example)",
    2: "Real-world analogy (intuitive everyday analogy connected to technical concept)",
    3: "Step-by-step breakdown (numbered steps with tiny worked tracing example)",
    4: "Interactive micro-teaching (1-2 sentences on one tiny piece + 1 simple check question)",
}


def is_confusion_signal(text: str) -> bool:
    """
    Detects if the student's message indicates confusion, misunderstanding,
    or a request for re-explanation.
    """
    if not text:
        return False
    clean = text.strip()
    return bool(_CONFUSION_PATTERNS.search(clean))


def get_strategy_name(level: int) -> str:
    """Returns human-readable strategy identifier for the given support level."""
    mapping = {
        0: "normal",
        1: "simpler_with_example",
        2: "real_world_analogy",
        3: "step_by_step_breakdown",
        4: "interactive_micro_teaching",
    }
    return mapping.get(level, "normal")


def adapt_teaching_support(
    current_level: int,
    is_confusion: bool,
) -> int:
    """
    Computes the next adaptive support level.
    If confusion is indicated, level increases up to maximum Level 4.
    """
    if is_confusion:
        return min(4, max(0, current_level) + 1)
    return max(0, min(4, current_level))
