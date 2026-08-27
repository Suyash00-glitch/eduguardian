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
    "eduguardian", "eduguard", "ai", "model", "system", "teacher", "professor",
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
    if re.search(r"\b(where\s+(am\s+i|i\s+am)|what\s+(?:is|was|are)|whats|who\s+am\s+i|why\s+are\s+you|asking\s+where|do\s+you\s+know|can\s+you\s+tell)\b", text, re.IGNORECASE):
        return None

    patterns = [
        # "My name is Ajmal", "Hii my name is Ajmal", "Hello, my name is Ajmal", "My name's Ajmal", "My names Ajmal"
        r"\bmy\s+name(?:'s|\s+is|\s+was|\s+s)?\s+([A-Za-z]+)",
        # "You can call me Ajmal", "Call me Ajmal"
        r"\b(?:you\s+can\s+)?call\s+me\s+([A-Za-z]+)",
        # "I am called Ajmal"
        r"\bi\s+am\s+called\s+([A-Za-z]+)",
        # "I'm Ajmal and...", "I am Ajmal and...", "I am Ajmal."
        r"^(?:hi|hii+|hello|hey)?\s*,?\s*i(?:'m|\s+am)\s+([A-Za-z]+)(?:\s+and\b|\s*,|\s*\.|$)",
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
    """
    Returns True if user is querying their personal name or identity.
    Strictly distinguishes personal name queries from general educational questions
    (e.g., 'What is the name of this algorithm?', 'Name three sorting algorithms').
    """
    if not text:
        return False

    text_clean = text.lower().strip().rstrip("?.!")

    # 1. Disqualify explicit declarations where the user is introducing/stating their name
    if re.search(r"\b(?:my\s+name(?:'s|\s+is|\s+was|\s+s)|i\s+am\s+called|call\s+me|i(?:'m|\s+am))\s+[A-Za-z]+", text_clean):
        # Unless it's a clarification/reminder like "you didn't say my name" or "i told you my name"
        if not re.search(r"\b(?:u\s+dint\s+say|you\s+didn'?t\s+say|you\s+didnt\s+say|but\s+i\s+said|i\s+told\s+you)\b", text_clean):
            return False

    # 2. Disqualify general/educational concept queries containing 'name'
    educational_name_patterns = [
        # "name of this/that/a/the algorithm/binary tree/data structure"
        r"\bname(?:s)?\s+(?:of|for)\s+(?:this|that|a|an|the|these|those|[a-z]+)\b",
        # "name 3 sorting algorithms", "name some data structures"
        r"\b(?:can\s+you\s+|please\s+)?name\s+(?:\d+|some|three|two|four|five|several|multiple|a\s+few|the\s+following)\b",
        # "variable name", "domain name", "file name", "method name", "function name"
        r"\b(?:variable|domain|file|class|method|function|table|column|package|module|tag|process|algorithm|data\s+structure|tree|concept)\s+names?\b",
    ]
    for pat in educational_name_patterns:
        if re.search(pat, text_clean):
            # Check if it has a personal self-reference like "name of me" or "my name"
            if not re.search(r"\b(?:my\s+name|name\s+of\s+(?:me|mine|myself|user|student))\b", text_clean):
                return False

    # 3. Direct standalone identity keywords/tokens
    # e.g., "name", "name?", "namew", "namew?", "my name", "my name?", "what is name", "what is namew"
    if re.fullmatch(r"(?:now\s+)?(?:what\s+is\s+)?(?:my\s+)?namew?", text_clean):
        return True

    # 4. Direct "who am i" / identity questions
    if re.search(r"\b(?:who\s+am\s+i|who\s+i\s+am|what\s+am\s+i\s+called|what'?s\s+my\s+identity|who\s+am\s+i\s+registered\s+as|tell\s+me\s+who\s+i\s+am|do\s+you\s+know\s+who\s+i\s+am)\b", text_clean):
        return True

    # 5. Queries asking for the user's name
    # e.g. "what is my name", "whats my name", "what's my name", "now tell me whats my name", "tell me my name", "what was my name"
    name_query_patterns = [
        # "what is/was my name", "whats my name", "what's my name"
        r"\b(?:what(?:'s|\s+is|\s+was)?|whats)\s+(?:now\s+)?(?:my|the\s+user'?s?|my\s+own)\s+name\b",
        # "tell me / say / speak my name", "tell me whats my name", "now tell me what is my name"
        r"\b(?:tell\s+me|tell|say|speak|give\s+me)\s+(?:now\s+)?(?:what(?:'s|\s+is|\s+was)?\s+|whats\s+)?(?:my|the\s+user'?s?|my\s+own)\s+name\b",
        # "do you know / remember / can you tell me my name"
        r"\b(?:do\s+you\s+(?:know|remember)|can\s+you\s+tell\s+me|could\s+you\s+tell\s+me|remember)\s+(?:what(?:'s|\s+is|\s+was)?\s+|whats\s+)?(?:my|the\s+user'?s?)\s+name\b",
        # "u didnt say my name", "you didn't say my name", "i told you my name"
        r"\b(?:u\s+dint\s+say|you\s+didn'?t\s+say|you\s+didnt\s+say|but\s+i\s+said|i\s+told\s+you)\s+my\s+name\b",
        # "my name?" or "my name"
        r"^(?:now\s+)?my\s+name(?:\s+again)?$",
    ]
    for pat in name_query_patterns:
        if re.search(pat, text_clean):
            return True

    # 6. Check common keyword substrings
    keywords = [
        "what is my name", "what's my name", "whats my name", "who am i", "who i am",
        "tell me my name", "say my name", "in 1 word say my name", "in one word say my name",
        "u dint say my name", "you didnt say my name", "you didn't say my name",
        "but i said my name", "i told you my name", "what am i called",
        "what's my identity", "who am i registered as", "do you know my name",
        "do you remember my name", "can you tell me my name", "what was my name",
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
    if known_name and str(known_name).strip().lower() not in _EXCLUDED_NAME_TOKENS:
        facts.name = " ".join(w.capitalize() for w in str(known_name).strip().split())
    if known_hometown and str(known_hometown).strip().lower() not in _EXCLUDED_NAME_TOKENS:
        facts.hometown = str(known_hometown).strip()

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

    # 2. Direct fallback extraction from user history only if name still missing
    if not facts.name and history:
        for msg in history:
            if isinstance(msg, dict):
                raw_role = str(msg.get("role", "user")).lower()
                c = msg.get("content", "")
            else:
                raw_role = str(getattr(msg, "role", "user")).lower()
                c = getattr(msg, "content", "")
            if "user" in raw_role:
                n = extract_name(str(c or ""))
                if n and n.lower() not in _EXCLUDED_NAME_TOKENS:
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


# ── Explicit Learning Preference Extractor ────────────────────────────────────

def extract_explicit_preference_action(text: str) -> dict[str, Any] | None:
    """
    Extracts an explicit learning preference command or permanent preference declaration.
    Strictly distinguishes persistent preferences ('From now on, keep your answers short')
    from single-turn concept questions ('What is a tree? Keep it short') and quiz answers ('2').

    Returns:
      - {"action": "set", "key": str, "value": str}
      - {"action": "remove", "key": str}
      - None (if message is a normal content question, quiz answer, or single turn modifier)
    """
    if not text:
        return None

    text_clean = text.strip()
    text_lower = text_clean.lower().rstrip(".!")

    # 1. Reject very short strings, pure single words, numbers, or quiz options (e.g. "A", "2", "yes", "ok")
    if len(text_clean.split()) < 2:
        return None

    # 2. Check for explicit Removal / Reset commands:
    reset_match = re.search(r"\b(?:reset|clear|wipe)\s+(?:all\s+)?(?:my\s+)?preferences\b", text_lower)
    if reset_match:
        return {"action": "remove", "key": "all"}

    remove_verbosity = re.search(r"\b(?:forget|don'?t\s+remember|remove|delete)\s+(?:that\s+i\s+prefer\s+|my\s+preference\s+for\s+|my\s+)?(?:short|concise|brief|detailed|long|verbosity)\b", text_lower)
    if remove_verbosity:
        return {"action": "remove", "key": "verbosity"}

    remove_style = re.search(r"\b(?:forget|don'?t\s+remember|remove|delete)\s+(?:that\s+i\s+prefer\s+|my\s+preference\s+for\s+|my\s+)?(?:examples?|step\s*by\s*step|simple|conceptual|practical|explanation[- ]style)\b", text_lower)
    if remove_style:
        return {"action": "remove", "key": "explanation_style"}

    remove_code = re.search(r"\b(?:forget|don'?t\s+remember|remove|delete)\s+(?:that\s+i\s+prefer\s+|my\s+preference\s+for\s+|my\s+)?(?:code\s+language|programming\s+language|python|java|javascript|c\+\+|cpp|golang|c#)\b", text_lower)
    if remove_code:
        return {"action": "remove", "key": "code_language"}

    # 3. Disqualify questions asking specific domain concepts (e.g. "What is a binary tree? Keep it short", "Explain recursion using Python")
    if re.search(r"\b(?:what\s+is|whats|tell\s+me\s+about|how\s+does|teach\s+me|why\s+is|quiz\s+me)\b", text_lower) and not re.search(r"\b(?:from\s+now\s+on|always|i\s+prefer|my\s+preference)\b", text_lower):
        return None
    if re.search(r"\bexplain\s+(?:about\s+)?(?!things\b|concepts\b|step\b|simply\b|in\s+detail\b)[a-z]+\b", text_lower) and not re.search(r"\b(?:from\s+now\s+on|always|i\s+prefer|my\s+preference)\b", text_lower):
        return None

    # 4. Verbosity: concise
    if re.search(r"\b(?:give\s+me\s+(?:short|concise|brief)\s+(?:answers|responses|explanations)|keep\s+(?:your\s+)?(?:answers|responses|explanations)\s+(?:short|concise|brief)|i\s+prefer\s+(?:short|concise|brief)\s+(?:answers|responses|explanations)|(?:from\s+now\s+on|always)\s*,?\s*(?:keep\s+it\s+(?:short|concise|brief)|be\s+(?:brief|concise)|give\s+(?:me\s+)?(?:short|concise|brief)\s+answers)|don'?t\s+give\s+me\s+long\s+explanations)\b", text_lower):
        return {"action": "set", "key": "verbosity", "value": "concise"}

    # 5. Verbosity: detailed
    if re.search(r"\b(?:give\s+me\s+detailed\s+(?:answers|responses|explanations)|explain\s+things\s+in\s+detail\s+from\s+now\s+on|i\s+prefer\s+detailed\s+(?:answers|responses|explanations)|(?:from\s+now\s+on|always)\s*,?\s*(?:give\s+(?:me\s+)?detailed\s+(?:answers|responses|explanations)|explain\s+in\s+detail))\b", text_lower):
        return {"action": "set", "key": "verbosity", "value": "detailed"}

    # 6. Explanation Style: examples
    if re.search(r"\b(?:explain\s+(?:things|concepts)?\s*(?:using|with|through)\s+examples|use\s+examples\s+when\s+(?:you\s+)?explain(?:ing)?|i\s+(?:learn\s+better|prefer)\s+(?:with|using)\s+examples|(?:from\s+now\s+on|always)\s*,?\s*use\s+examples)\b", text_lower):
        return {"action": "set", "key": "explanation_style", "value": "examples"}

    # 7. Explanation Style: step_by_step
    if re.search(r"\b(?:i\s+prefer\s+step[- ]by[- ]step\s+(?:answers|responses|explanations)|(?:from\s+now\s+on|always)\s*,?\s*(?:explain\s+step[- ]by[- ]step|give\s+step[- ]by[- ]step\s+explanations)|explain\s+things\s+step[- ]by[- ]step\s+from\s+now\s+on)\b", text_lower):
        return {"action": "set", "key": "explanation_style", "value": "step_by_step"}

    # 8. Explanation Style: simple / conceptual / practical
    if re.search(r"\b(?:i\s+prefer\s+simple\s+(?:words|explanations)|(?:from\s+now\s+on|always)\s*,?\s*(?:keep\s+it\s+simple|explain\s+simply|use\s+simple\s+words))\b", text_lower):
        return {"action": "set", "key": "explanation_style", "value": "simple"}

    if re.search(r"\b(?:i\s+prefer\s+conceptual\s+explanations|(?:from\s+now\s+on|always)\s*,?\s*focus\s+on\s+concepts)\b", text_lower):
        return {"action": "set", "key": "explanation_style", "value": "conceptual"}

    if re.search(r"\b(?:i\s+prefer\s+practical\s+explanations|(?:from\s+now\s+on|always)\s*,?\s*focus\s+on\s+practical\s+applications)\b", text_lower):
        return {"action": "set", "key": "explanation_style", "value": "practical"}

    # 9. Code Language
    lang_match = re.search(r"\b(?:(?:from\s+now\s+on|always)\s*,?\s*)?(?:use\s+|prefer\s+)?(python|java|javascript|typescript|c\+\+|cpp|golang|rust|c#|sql|html)\s+(?:for\s+(?:all\s+)?code(?:\s+examples)?|when\s+(?:you\s+)?(?:show|write)\s+code|code\s+examples)\b", text_lower)
    if lang_match:
        raw_lang = lang_match.group(1)
        lang_map = {
            "python": "Python",
            "java": "Java",
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "c++": "C++",
            "cpp": "C++",
            "golang": "Go",
            "rust": "Rust",
            "c#": "C#",
            "sql": "SQL",
            "html": "HTML",
        }
        val = lang_map.get(raw_lang, raw_lang.capitalize())
        return {"action": "set", "key": "code_language", "value": val}

    return None
