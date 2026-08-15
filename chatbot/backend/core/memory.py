"""
User Fact Extraction and Conversational Memory Engine for EduGuardian AI.

Provides structured fact extraction, memory persistence across turns,
and strict query vs declaration disambiguation.
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field


class UserFacts(BaseModel):
    """Structured long-term and short-term facts known about the user."""
    name: str | None = None
    hometown: str | None = None   # Where the user comes from / birthplace
    location: str | None = None   # Where the user currently resides
    interests: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


# Common verbs, prepositions, and non-name words that must NEVER be extracted as a person's name
_EXCLUDED_NAME_TOKENS = {
    "from", "asking", "here", "there", "happy", "sad", "good", "fine", "bad",
    "tired", "struggling", "trying", "going", "ready", "interested", "sure",
    "not", "doing", "sorry", "okay", "ok", "a", "an", "the", "student", "someone",
    "curious", "wondering", "studying", "learning", "thinking", "working",
    "living", "staying", "telling", "saying", "looking", "searching", "reading",
    "writing", "answering", "speaking", "talking", "getting", "making", "feeling",
    "user", "assistant", "bot", "coach", "today", "now", "just", "really",
}

# Question indicators that invalidate fact extraction
_QUESTION_INDICATORS = re.compile(
    r"(\?|\b(where|what|why|how|who|which|when|am\s+i|is\s+my|are\s+you|tell\s+me\s+if|do\s+you\s+know|asking)\b)",
    re.IGNORECASE,
)


def _is_question_or_query(text: str) -> bool:
    """Returns True if the text is asking a question rather than stating a fact."""
    text_clean = text.strip()
    if text_clean.endswith("?"):
        return True
    return bool(_QUESTION_INDICATORS.search(text_clean))


# ── Explicit Fact Extractors ───────────────────────────────────────────────────

def extract_name(text: str) -> str | None:
    """
    Extracts the user's name ONLY when explicitly declared.
    Rejects questions, queries, third-party descriptions, and common verbs/adjectives.
    """
    if not text:
        return None

    # Never extract a name from a question or query asking where/who/what
    if re.search(r"\b(where\s+(am\s+i|i\s+am)|what\s+is\s+my|who\s+am\s+i|why\s+are\s+you|asking\s+where)\b", text, re.IGNORECASE):
        return None

    patterns = [
        # "My name is Ajmal", "Hii my name is Ajmal", "Hello, my name is Ajmal"
        r"\bmy\s+name\s+is\s+([A-Za-z]+)",
        # "You can call me Ajmal", "Call me Ajmal"
        r"\b(?:you\s+can\s+)?call\s+me\s+([A-Za-z]+)",
        # "I am called Ajmal"
        r"\bi\s+am\s+called\s+([A-Za-z]+)",
        # "I'm Ajmal and...", "I am Ajmal and..." (must be followed by proper noun)
        r"^(?:hi|hii+|hello|hey)?\s*,?\s*i(?:'m|\s+am)\s+([A-Z][a-z]+)(?:\s+and\b|\s*,|\s*\.|$)",
    ]

    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if candidate.lower() not in _EXCLUDED_NAME_TOKENS and len(candidate) >= 2:
                return candidate.capitalize()

    return None


def extract_hometown(text: str) -> str | None:
    """
    Extracts the user's hometown/origin ONLY from explicit declarative statements.
    Rejects questions ('Where am I from?'), third-party statements ('My friend is from...'),
    and questions about the AI ('Where are you from?').
    """
    if not text:
        return None

    # Disqualify questions asking where/why/how/asking
    if re.search(r"(\?|\b(where\s+(am\s+i|i\s+am|are\s+you)|what|why|how|who|asking)\b)", text, re.IGNORECASE):
        return None

    # Disqualify third-party references
    if re.search(r"\b(friend|someone|people|they|he|she|brother|sister|teacher|professor|it)\s+is\s+from\b", text, re.IGNORECASE):
        return None

    # Disqualify statements about the AI
    if re.search(r"\b(you\s+are|you're)\s+from\b", text, re.IGNORECASE):
        return None

    patterns = [
        # "I am from Mangalore", "I'm from Mangalore", "I come from Mangalore"
        r"\bi\s*(?:am|'m|\s+come)\s+from\s+([A-Za-z\s]+?)(?:\s*\.|\s*\,|\s+and\b|$)",
        # "My hometown is Mangalore"
        r"\bmy\s+hometown\s+is\s+([A-Za-z\s]+?)(?:\s*\.|\s*\,|\s+and\b|$)",
        # "I am originally from Mangalore"
        r"\bi\s*(?:am|'m)\s+originally\s+from\s+([A-Za-z\s]+?)(?:\s*\.|\s*\,|\s+and\b|$)",
    ]

    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            cand_words = candidate.split()
            if cand_words and cand_words[0].lower() not in _EXCLUDED_NAME_TOKENS:
                return " ".join(w.capitalize() for w in cand_words if w.isalpha())

    return None


def extract_location(text: str) -> str | None:
    """Extracts current place of residence from explicit statements like 'I live in Mangalore'."""
    if not text or _is_question_or_query(text):
        return None

    patterns = [
        r"\bi\s*(?:live|stay|reside|\s*am\s+living|\s*am\s+staying)\s+in\s+([A-Za-z\s]+?)(?:\s*\.|\s*\,|\s+and\b|$)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            cand_words = candidate.split()
            if cand_words and cand_words[0].lower() not in _EXCLUDED_NAME_TOKENS:
                return " ".join(w.capitalize() for w in cand_words if w.isalpha())

    return None


def extract_interests(text: str) -> list[str]:
    """Extracts study topics or interests the user explicitly declared interest in."""
    if not text or _is_question_or_query(text):
        return []

    interests = []
    patterns = [
        (r"\b(?:i\s+want\s+to\s+learn|interested\s+in\s+learning|like\s+to\s+study|studying)\s+([A-Za-z\s]+?)(?:\s*\.|\s*\,|\s+and\b|$)", 1),
        (r"\b(?:my\s+favorite\s+topic\s+is|my\s+favourite\s+topic\s+is|my\s+favorite\s+subject\s+is|my\s+favourite\s+subject\s+is)\s+([A-Za-z\s]+?)(?:\s*\.|\s*\,|\s+and\b|$)", 1),
        (r"\b(?:i\s+love\s+studying|i\s+enjoy\s+learning)\s+([A-Za-z\s]+?)(?:\s*\.|\s*\,|\s+and\b|$)", 1),
    ]
    for pat, grp in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(grp).strip()
            if val and val.lower() not in _EXCLUDED_NAME_TOKENS:
                interests.append(val.title())
    return interests


# ── Query Intent Classifiers ───────────────────────────────────────────────────

def is_interest_query(text: str) -> bool:
    """Returns True if user is asking what they like to study or their favorite topic."""
    text_clean = text.lower().strip().rstrip("?.!")
    keywords = [
        "what do i like to study", "what do i like", "what is my favorite topic",
        "what's my favorite topic", "what are my interests", "what is my interest",
        "what do i study", "what do i enjoy studying", "what is my favorite subject",
    ]
    return any(kw in text_clean for kw in keywords)


def is_name_query(text: str) -> bool:
    """Returns True if user is asking for their name or identity."""
    if not text:
        return False
    # Reject affirmative declarations like "my name is..."
    if re.search(r"\b(my\s+name\s+is|i\s+am\s+called|call\s+me)\b", text, re.IGNORECASE):
        return False

    text_clean = text.lower().strip().rstrip("?.!")
    keywords = [
        "what is my name", "what's my name", "who am i", "who i am",
        "tell me my name", "say my name", "in 1 word say my name",
        "u dint say my name", "you didnt say my name", "you didn't say my name",
        "but i said my name", "i told you my name", "what am i called",
        "what's my identity", "who am i registered as",
    ]
    return any(kw in text_clean for kw in keywords)



def is_hometown_query(text: str) -> bool:
    """Returns True if user is asking where they are from."""
    text_clean = text.lower().strip().rstrip("?.!")
    # Disqualify asking about the AI ("Where are you from?")
    if re.search(r"\b(where\s+are\s+you\s+from|where\s+you\s+from|where\s+is\s+eduguardian)\b", text_clean):
        return False

    keywords = [
        "where am i from", "where i am from", "where do i come from",
        "what is my hometown", "what's my hometown", "which city am i from",
        "what place am i from", "where am i originally from",
        "i am asking where i am from", "tell me where i am from",
        "do you know where i am from",
    ]
    return any(kw in text_clean for kw in keywords)


def is_ai_origin_query(text: str) -> bool:
    """Returns True if user is asking where the AI is from."""
    text_clean = text.lower().strip().rstrip("?.!")
    keywords = [
        "where are you from", "where you from", "who made you", "where is eduguardian from",
    ]
    return any(kw in text_clean for kw in keywords)


def is_system_architecture_query(text: str) -> bool:

    """Returns True if user is asking about the system agents or capabilities."""
    text_clean = text.lower().strip().rstrip("?.!")
    if re.search(r"\b(which|what|list|how\s+many)\s+(?:and\s+all\s+)?(?:the\s+)?agents\b", text_clean):
        return True
    if re.search(r"\bagents\s+(?:do\s+)?i\s+have\b|\bagents\s+are\s+available\b|\bwhat\s+are\s+the\s+agents\b", text_clean):
        return True
    return False


def is_existential_user_query(text: str) -> bool:
    """Returns True if user is asking why they themselves are here (self-referential)."""
    text_clean = text.lower().strip().rstrip("?.!")
    # Disqualify asking about the assistant ("Why are you here?")
    if re.search(r"\bwhy\s+are\s+you\s+here\b", text_clean):
        return False
    patterns = [
        r"\bwhy\s+(?:am\s+i|i\s+am)\s+here\b",
        r"\bwhat\s+am\s+i\s+doing\s+here\b",
        r"\bwhy\s+am\s+i\s+in\s+this\s+chat\b",
    ]
    return any(bool(re.search(pat, text_clean)) for pat in patterns)


def is_clarification_user_query(text: str) -> bool:
    """Returns True if user is clarifying that they were asking about themselves, not the AI."""
    text_clean = text.lower().strip().rstrip("?.!")
    patterns = [
        r"\b(?:no\s+)?i\s+am\s+asking\s+why\s+(?:i\s+am|am\s+i)\s+here\s+not\s+you\b",
        r"\bwhy\s+(?:i\s+am|am\s+i)\s+here\s+not\s+you\b",
        r"\bnot\s+you\b.*\bwhy\s+(?:i\s+am|am\s+i)\s+here\b",
        r"\bi\s+asked\s+about\s+myself\b",
    ]
    return any(bool(re.search(pat, text_clean)) for pat in patterns)


# ── Memory Resolution Engine ───────────────────────────────────────────────────


def resolve_user_facts(
    history: list[Any] | None,
    current_message: str,
    known_name: str | None = None,
    known_hometown: str | None = None,
) -> UserFacts:
    """
    Extracts and aggregates user facts across conversation history and current message.
    Preserves existing facts; questions NEVER overwrite or delete established facts.
    """
    facts = UserFacts()
    if known_name and str(known_name).lower() not in _EXCLUDED_NAME_TOKENS:
        facts.name = str(known_name).capitalize()
    if known_hometown and str(known_hometown).lower() not in _EXCLUDED_NAME_TOKENS:
        facts.hometown = str(known_hometown)

    # 1. Replay history messages in chronological order
    if history:
        for msg in history:
            if isinstance(msg, dict):
                raw_role = msg.get("role", "user")
                content = str(msg.get("content", "") or "")
            else:
                raw_role = getattr(msg, "role", "user")
                content = str(getattr(msg, "content", "") or "")

            role_val = raw_role.value if hasattr(raw_role, "value") else str(raw_role)
            role_str = str(role_val).lower()

            if "user" in role_str:
                _update_facts_from_text(content, facts)

    # 2. Direct fallback extraction from history if name still missing
    if not facts.name and history:
        for msg in history:
            c = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
            n = extract_name(str(c or ""))
            if n:
                facts.name = n
                break

    # 3. Update with current message
    _update_facts_from_text(current_message, facts)

    return facts


def _update_facts_from_text(text: str, facts: UserFacts) -> None:
    """Applies affirmative declarations to facts model without allowing questions to alter facts."""
    if not text:
        return

    # Extract name (only overwrites if explicit affirmative statement present)
    name = extract_name(text)
    if name:
        facts.name = name

    # Extract hometown
    hometown = extract_hometown(text)
    if hometown:
        facts.hometown = hometown

    # Extract location
    loc = extract_location(text)
    if loc:
        facts.location = loc

    # Extract interests
    interests = extract_interests(text)
    for item in interests:
        if item not in facts.interests:
            facts.interests.append(item)
