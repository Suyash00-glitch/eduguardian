"""
Response Validation & Constraint Enforcement Layer for EduGuardian AI.

Ensures that the final student-facing response strictly adheres to:
1. Format constraints (one_word, one_sentence, exact_items, links_only, no_extra_text).
2. Safety rules (zero forbidden stigmatizing terms).
3. Fact integrity (no hallucinated tokens like 'Hi From!' or 'Hi Asking!').
"""
from __future__ import annotations

import re
import logging
from typing import Any

from chatbot.backend.schemas.routing import ResponseConstraints, ProcessedRequest, RequestIntent
from chatbot.backend.core.memory import UserFacts

logger = logging.getLogger(__name__)

# Forbidden terms regex — stigmatizing labels that must never reach students
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

# Bogus greeting detector
_BOGUS_GREETING_PATTERN = re.compile(
    r"\bhi\s+(from|asking|neural|what|where|who|why|how|student|test\s+student|user)\b[!.,]?",
    re.IGNORECASE,
)


class ResponseValidator:
    """Validates, sanitizes, and enforces response constraints."""

    @classmethod
    def validate_and_enforce(
        cls,
        response_text: str,
        constraints: ResponseConstraints,
        user_facts: UserFacts | None = None,
        intent: RequestIntent | None = None,
    ) -> str:
        """
        Applies post-processing validation and deterministic constraint enforcement.
        """
        if not response_text:
            return ""

        text = response_text.strip()

        # 1. Sanitize forbidden terms
        text = _FORBIDDEN_TERMS_PATTERN.sub("student with areas to strengthen", text)

        # 2. Fix any bogus greetings
        if _BOGUS_GREETING_PATTERN.search(text):
            resolved_name = user_facts.name if user_facts and user_facts.name else ""
            clean_greeting = f"Hi {resolved_name}!" if resolved_name else "Hi!"
            text = _BOGUS_GREETING_PATTERN.sub(clean_greeting, text)

        # 3. Check for Self-Reference Confusion on Existential Queries ("why am I here?")
        if intent == RequestIntent.CLARIFICATION or "why am i here" in text.lower():
            if re.search(r"\bi(?:'m|\s+am)\s+here\s+to\s+(?:answer|help|assist)\b", text, re.IGNORECASE):
                text = "That's a deeper question. If you mean your academic goals or purpose as a student, we can explore that together."

        # 4. Check for Hallucinated Names when name is unknown
        if (not user_facts or not user_facts.name) and intent == RequestIntent.IDENTITY:
            if re.search(r"\b(kshithij|rahul|aisha|priya|arjun|test\s+student|student)\b", text, re.IGNORECASE):
                text = "I don't have your name saved yet."

        # 4.5. Reconcile known name if response claims name is missing but memory has it
        if user_facts and user_facts.name:
            if "i don't have your name saved yet" in text.lower():
                text = re.sub(
                    r"\bi\s+don't\s+have\s+your\s+name\s+saved\s+yet\.?\s*",
                    f"Your name is {user_facts.name}. ",
                    text,
                    flags=re.IGNORECASE,
                ).strip()

        # 5. Generic Fallback Sanitization for Emotional Support or Specific Intents

        if text.strip() in ("I'm here to answer your questions and help you with your studies.", "I'm here to answer your questions."):
            if intent == RequestIntent.EMOTIONAL_SUPPORT:
                text = "Feeling overwhelmed or down about your studies is completely normal, but you don't have to tackle everything at once. Start with one small, manageable task today, and we can take it one step at a time."
            elif intent == RequestIntent.SYSTEM_ARCHITECTURE:
                text = "You currently have three agents: Student Insight Agent, Study Planner Agent, and Recovery Coach Agent."
            elif intent == RequestIntent.EDUCATIONAL:
                text = "I'm here to help explain any concept or course topic you'd like to understand."

        # 6. Format Constraint: Exactly One Word
        if constraints.one_word:
            text = cls._enforce_one_word(text, user_facts)
            return text

        # 7. Format Constraint: Exactly One Sentence
        if constraints.one_sentence:
            text = cls._enforce_one_sentence(text, user_facts)
            return text

        # 8. Format Constraint: No Extra Text / Links Only
        if constraints.no_extra_text or constraints.links_only:
            text = cls._strip_conversational_padding(text)

        # 9. Format Constraint: Exact Number of Items
        if constraints.exact_items is not None:
            text = cls._enforce_exact_items(text, constraints.exact_items)

        # 10. Strip trailing conversational cliches if no_extra_text or direct
        if constraints.direct_answer or constraints.no_extra_text:
            text = cls._strip_trailing_coaching_questions(text)

        return text.strip()


    @classmethod
    def _enforce_one_word(cls, text: str, user_facts: UserFacts | None = None) -> str:
        """Extracts/trims output to exactly 1 word."""
        clean = text.strip().rstrip(".!?,")
        words = clean.split()
        if len(words) <= 1:
            return f"{clean}." if clean and not clean.endswith(".") else clean

        # If user asked for name, return known name
        if user_facts and user_facts.name and user_facts.name.lower() in clean.lower():
            return f"{user_facts.name}."

        # If it's a known city/hometown
        if user_facts and user_facts.hometown and user_facts.hometown.lower() in clean.lower():
            return f"{user_facts.hometown}."

        # Otherwise take the last or first word
        candidate = words[-1] if words[-1].isalpha() else words[0]
        candidate = candidate.rstrip(".!?,")
        return f"{candidate}."

    @classmethod
    def _enforce_one_sentence(cls, text: str, user_facts: UserFacts | None = None) -> str:
        """Ensures the response consists of exactly 1 concise sentence."""
        clean = text.strip()
        # Split by sentence boundaries (.!?)
        sentences = re.split(r"(?<=[.!?])\s+", clean)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return clean

        # If first sentence is a greeting like "Hello Ajmal!", take the second meaningful sentence or combine
        if len(sentences) > 1 and re.match(r"^(?:hi|hello|hey|good\s+\w+)\b", sentences[0], re.IGNORECASE):
            main_sentence = sentences[1]
        else:
            main_sentence = sentences[0]

        # Ensure terminal punctuation
        if not main_sentence.endswith((".", "!", "?")):
            main_sentence += "."

        return main_sentence

    @classmethod
    def _strip_conversational_padding(cls, text: str) -> str:
        """Strips conversational greetings and preamble from start of message."""
        lines = text.strip().splitlines()
        filtered_lines = []
        for line in lines:
            line_s = line.strip()
            # Skip introductory filler lines
            if re.match(r"^(?:here\s+(?:are|is)|sure|of\s+course|certainly|below\s+is|hello|hi|hey)\b.*:$", line_s, re.IGNORECASE):
                continue
            if re.match(r"^(?:i\s+hope\s+this\s+helps|let\s+me\s+know|how\s+does\s+that\s+sound|feel\s+free)\b", line_s, re.IGNORECASE):
                continue
            filtered_lines.append(line)

        res = "\n".join(filtered_lines).strip()
        return res if res else text.strip()

    @classmethod
    def _strip_trailing_coaching_questions(cls, text: str) -> str:
        """Strips unsolicited questions at the end like 'How does that sound?'."""
        cliches = [
            r"\bhow\s+does\s+that\s+sound\??",
            r"\bwould\s+you\s+like\s+me\s+to\s+create\s+a\s+plan\??",
            r"\blet\s+me\s+know\s+if\s+you\s+need\s+anything\s+else\.?",
            r"\bif\s+you'?d\s+like,\s+we\s+can\s+explore.*",
            r"\bdon'?t\s+hesitate\s+to\s+ask.*",
            r"\bi'?m\s+always\s+here\s+to\s+help.*",
        ]
        res = text.strip()
        for pat in cliches:
            res = re.sub(pat, "", res, flags=re.IGNORECASE).strip()
        return res

    @classmethod
    def _enforce_exact_items(cls, text: str, count: int) -> str:
        """Limits listed bullet items to the exact number requested."""
        lines = text.strip().splitlines()
        item_lines = []
        non_item_lines = []

        for line in lines:
            line_s = line.strip()
            if re.match(r"^(\d+[\.\)]|[-•*])\s+", line_s):
                item_lines.append(line)
            else:
                if not item_lines:
                    non_item_lines.append(line)

        if len(item_lines) >= count:
            selected_items = item_lines[:count]
            return "\n".join(selected_items)

        return text
