"""
Router Component — Intent Classification, Constraint Parsing, and Conditional Routing.

Determines the student's request intent, parses explicit response constraints,
checks for deterministic fast-paths, and provides conditional edge routing functions
for the LangGraph StateGraph.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Union

from chatbot.backend.orchestrator.state import GraphState
from chatbot.backend.schemas.routing import (
    IntentType,
    IntentClassification,
    ResponseMode,
    RequestIntent,
    ResponseConstraints,
    ProcessedRequest,
)
from chatbot.backend.schemas.student import StudentContext
from chatbot.backend.schemas.teaching import (
    TeachingDifficulty,
    TeachingEvaluation,
    TeachingState,
    TeachingStep,
)
from chatbot.backend.schemas.quiz import (
    QuizDifficulty,
    QuizEvaluation,
    QuizQuestionType,
    QuizState,
    QuizStep,
)
from chatbot.backend.core.memory import UserFacts, is_name_query, is_hometown_query
from chatbot.backend.orchestrator.deterministic import try_resolve_deterministic_answer
from chatbot.backend.orchestrator.adaptive_quiz import determine_initial_quiz_difficulty
from chatbot.backend.guardrails.service import get_guardrails_service

logger = logging.getLogger(__name__)

# ── Teach Me Tutoring Patterns ───────────────────────────────────────────────

_TEACH_ME_START_PATTERN = re.compile(
    r"^(?:can\s+you\s+|could\s+you\s+|please\s+|help\s+me\s+)?(?:"
    r"teach\s+me(?:\s+about)?|"
    r"i\s+want\s+to\s+learn(?:\s+about)?|"
    r"can\s+you\s+teach\s+me(?:\s+about)?|"
    r"help\s+me\s+learn(?:\s+about)?|"
    r"i\s+need\s+to\s+learn(?:\s+about)?|"
    r"tutor\s+me\s+on|"
    r"i\s+would\s+like\s+to\s+learn(?:\s+about)?|"
    r"start\s+teaching\s+me|"
    r"start\s+teaching"
    r")(?:\s+(.+))?$",
    re.IGNORECASE,
)

_TEACH_ME_EXIT_PATTERN = re.compile(
    r"\b("
    r"stop\s+teaching|exit\s+teach(?:ing)?|end\s+lesson|stop\s+lesson|"
    r"exit\s+lesson|stop\s+this\s+lesson|quit\s+teaching|cancel\s+teaching|"
    r"let'?s\s+stop(?:\s+here|\s+teaching)?|let'?s\s+talk\s+about\s+something\s+else|"
    r"enough\s+teaching|no\s+more\s+teaching|done\s+with\s+teaching|leave\s+teach\s+mode"
    r")\b",
    re.IGNORECASE,
)


# ── Quiz Mode Patterns ───────────────────────────────────────────────────────

_QUIZ_START_PATTERN = re.compile(
    r"^(?:can\s+you\s+|could\s+you\s+|please\s+)?(?:"
    r"quiz\s+me(?:\s+on|\s+about)?|"
    r"give\s+me\s+(?:a\s+|an\s+)?(?:(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)[- ]questions?\s+)?(?:hard|easy|intermediate|advanced|quick|basic|foundational)?\s*(?:quiz|test)(?:\s+on|\s+about)?|"
    r"give\s+me\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+questions(?:\s+on|\s+about)?|"
    r"test\s+me(?:\s+on|\s+about)?|"
    r"i\s+want\s+to\s+practice|"
    r"practice\s+quiz(?:\s+on|\s+about)?|"
    r"take\s+a\s+quiz(?:\s+on|\s+about)?|"
    r"start\s+(?:with\s+a\s+|a\s+|an\s+)?(?:hard|easy|intermediate|advanced|quick|basic|foundational)?\s*(?:quiz|test)?(?:\s+on|\s+about)?|"
    r"quick\s+quiz(?:\s+on|\s+about)?|"
    r"quiz"
    r")(?:\s+(.+))?$",
    re.IGNORECASE,
)

_QUIZ_EXIT_PATTERN = re.compile(
    r"\b("
    r"stop\s+(?:the\s+)?quiz|exit\s+quiz|end\s+quiz|quit\s+quiz|"
    r"cancel\s+quiz|leave\s+quiz|stop\s+testing|done\s+with\s+quiz|"
    r"stop\s+quiz"
    r")\b",
    re.IGNORECASE,
)


def extract_quiz_params(text: str) -> tuple[bool, str | None, QuizDifficulty, int, bool]:
    """
    Extracts topic, difficulty, question count, and whether explicit difficulty was requested.
    Supports arbitrary educational topics and dynamic question counts without hardcoding.
    """
    clean = text.strip().rstrip(".?!")
    m = _QUIZ_START_PATTERN.match(clean)
    if not m:
        return False, None, QuizDifficulty.BEGINNER, 5, False

    raw_args = m.group(1)
    args_clean = raw_args.strip().rstrip(".?!") if raw_args else ""

    # 1. Parse Question Count from clean text (e.g. "3 questions", "3-question", "quick quiz" -> 3)
    total_q = 5
    word_to_num = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
    count_match = re.search(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)[- ]questions?\b", clean, re.IGNORECASE)
    if count_match:
        val_str = count_match.group(1).lower()
        num_val = word_to_num.get(val_str, int(val_str) if val_str.isdigit() else 5)
        total_q = max(1, min(15, num_val))
    elif re.search(r"\bquick\s+quiz\b", clean, re.IGNORECASE):
        total_q = 3

    if not args_clean or args_clean.lower() in ("something", "anything", "a topic", "a new topic", "stuff", "quiz", "a quiz"):
        return True, None, QuizDifficulty.BEGINNER, total_q, False

    # 2. Parse Difficulty
    has_explicit_diff = False
    difficulty = QuizDifficulty.BEGINNER
    if re.search(r"\b(advanced|deep|complex|expert|hard)\b", clean, re.IGNORECASE):
        difficulty = QuizDifficulty.ADVANCED
        has_explicit_diff = True
        args_clean = re.sub(r"\b(advanced|deep|complex|expert|hard)\b", "", args_clean, flags=re.IGNORECASE).strip()
    elif re.search(r"\b(intermediate|moderate|medium)\b", clean, re.IGNORECASE):
        difficulty = QuizDifficulty.INTERMEDIATE
        has_explicit_diff = True
        args_clean = re.sub(r"\b(intermediate|moderate|medium)\b", "", args_clean, flags=re.IGNORECASE).strip()
    elif re.search(r"\b(from\s+basics?|from\s+scratch|beginner|introductory|introduction\s+to|easy|start\s+easy)\b", clean, re.IGNORECASE):
        difficulty = QuizDifficulty.BEGINNER
        has_explicit_diff = True
        args_clean = re.sub(r"\b(from\s+basics?|from\s+scratch|beginner|introductory|introduction\s+to|easy|start\s+easy)\b", "", args_clean, flags=re.IGNORECASE).strip()

    # 3. Clean topic string
    topic_clean = re.sub(r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)[- ]questions?\b", "", args_clean, flags=re.IGNORECASE).strip()
    topic_clean = re.sub(r"^(?:about|on|in|the|a|an|for|with)\s+", "", topic_clean, flags=re.IGNORECASE).strip()
    topic_clean = re.sub(r"\b(?:questions?|quiz|test)\b", "", topic_clean, flags=re.IGNORECASE).strip()
    topic_clean = topic_clean.strip(" '\"`.,;:")

    if not topic_clean:
        return True, None, difficulty, total_q, has_explicit_diff

    return True, topic_clean, difficulty, total_q, has_explicit_diff



def extract_teach_me_topic(text: str) -> tuple[bool, str | None, TeachingDifficulty]:
    """
    Extracts topic and difficulty from a Teach Me initiation message.
    Supports arbitrary educational topics without hardcoding.
    """
    clean = text.strip()
    m = _TEACH_ME_START_PATTERN.match(clean)
    if not m:
        return False, None, TeachingDifficulty.BEGINNER

    topic_raw = m.group(1)
    if not topic_raw:
        return True, None, TeachingDifficulty.BEGINNER

    topic_clean = topic_raw.strip().rstrip(".?!")
    if not topic_clean or topic_clean.lower() in ("something", "anything", "a topic", "a new topic", "something new", "stuff"):
        return True, None, TeachingDifficulty.BEGINNER

    difficulty = TeachingDifficulty.BEGINNER
    if re.search(r"\b(advanced|deep|complex|expert)\b", topic_clean, re.IGNORECASE):
        difficulty = TeachingDifficulty.ADVANCED
        topic_clean = re.sub(r"\b(advanced|deep|complex|expert)\b", "", topic_clean, flags=re.IGNORECASE).strip()
    elif re.search(r"\b(intermediate|moderate)\b", topic_clean, re.IGNORECASE):
        difficulty = TeachingDifficulty.INTERMEDIATE
        topic_clean = re.sub(r"\b(intermediate|moderate)\b", "", topic_clean, flags=re.IGNORECASE).strip()
    elif re.search(r"\b(from\s+basics|from\s+scratch|basics?|beginner|introductory|introduction\s+to)\b", topic_clean, re.IGNORECASE):
        difficulty = TeachingDifficulty.BEGINNER
        topic_clean = re.sub(r"\b(from\s+basics|from\s+scratch|basics?|beginner|introductory|introduction\s+to)\b", "", topic_clean, flags=re.IGNORECASE).strip()

    topic_clean = re.sub(r"^(?:about|on|in|the|a|an)\s+", "", topic_clean, flags=re.IGNORECASE).strip()
    topic_clean = topic_clean.strip(" '\"`.,;:")

    if not topic_clean:
        return True, None, difficulty

    return True, topic_clean, difficulty


# ── Intent Routing Patterns ───────────────────────────────────────────────────

_PLAN_PATTERNS = re.compile(
    r"\b("
    r"study plan|make me a plan|create a plan|give me a plan|"
    r"weekly plan|weekly schedule|daily schedule|"
    r"schedule for|plan for (this|next|the) week|"
    r"help me (organize|plan|schedule)|"
    r"what should i study|revision plan|revision schedule|"
    r"timetable|study timetable|"
    r"how should i study|where do i start studying|"
    r"adjust my (plan|schedule)|make (monday|tuesday|wednesday|thursday|friday|saturday|sunday) easier|"
    r"change my plan|update my schedule|modify my plan"
    r")\b",
    re.IGNORECASE,
)

_ACADEMIC_PATTERNS = re.compile(
    r"\b("
    r"c?gpa|sgpa|grades?|marks?|marks\s+card|credits?|backlogs?|arrears?|attendance|classes\s+attended|missed\s+classes|"
    r"what\s+is\s+my\s+(?:c?gpa|sgpa|latest\s+sgpa|grade|score|mark|attendance)|what'?s\s+my\s+(?:c?gpa|sgpa|latest\s+sgpa|grade|score|mark|attendance)|"
    r"my\s+(?:c?gpa|sgpa|latest\s+sgpa|marks|grades|scores|attendance|progress|record|standing|performance)|"
    r"how\s+am\s+i\s+doing|how\s+am\s+i\s+performing(?:\s+academically)?|how\s+is\s+my\s+(?:progress|attendance|performance)|my\s+academic\s+performance|"
    r"show\s+me\s+my\s+marks(?:\s+performance)?|semester\s+results?|exam\s+results?|quiz\s+scores?|assessment\s+scores?|"
    r"academic\s+trajectory|academic\s+situation|track\s+record|"
    r"why\s+am\s+i\s+struggling|struggling\s+with|falling\s+behind|catch\s+up|"
    r"why\s+are\s+my\s+(?:marks|grades|scores)\s+(?:dropping|slipping|low)|"
    r"failing|which\s+subjects?|what\s+topics?\s+to\s+focus\s+on|where\s+do\s+i\s+need\s+to\s+improve|"
    r"what\s+should\s+i\s+focus\s+on\s+next"
    r")\b",
    re.IGNORECASE,
)

# ── Response Mode Detection Patterns ─────────────────────────────────────────

_IDENTITY_PATTERNS = re.compile(
    r"\b("
    r"who\s+am\s+i|who\s+i\s+am|what\s+is\s+my\s+name|what'?s\s+my\s+name|"
    r"my\s+name\??|tell\s+me\s+my\s+name|say\s+my\s+name|"
    r"who\s+am\s+i\s+registered\s+as|my\s+profile|my\s+info|"
    r"where\s+am\s+i\s+from|where\s+i\s+am\s+from|where\s+do\s+i\s+come\s+from|"
    r"what\s+is\s+my\s+hometown|what'?s\s+my\s+hometown|which\s+city\s+am\s+i\s+from|"
    r"i\s+am\s+asking\s+where\s+i\s+am\s+from|tell\s+me\s+where\s+i\s+am\s+from|"
    r"where\s+do\s+i\s+live|what\s+is\s+my\s+location|"
    r"u\s+dint\s+say\s+my\s+name|you\s+didn'?t\s+say\s+my\s+name|you\s+didnt\s+say\s+my\s+name|"
    r"but\s+i\s+said\s+my\s+name|i\s+told\s+you\s+my\s+name"
    r")\b",
    re.IGNORECASE,
)

_DIRECT_FACTUAL_PATTERNS = re.compile(
    r"\b("
    r"capital\s+of|what\s+is\s+the\s+capital|"
    r"population\s+of|what\s+is\s+the\s+population|"
    r"currency\s+of|president\s+of|prime\s+minister\s+of|"
    r"largest|smallest|highest|deepest|longest|fastest|"
    r"who\s+invented|who\s+discovered|when\s+was|where\s+is|"
    r"what\s+is\s+\d+\s*[\+\-\*\/]\s*\d+|\d+\s*[\+\-\*\/]\s*\d+\s*=?"
    r")\b",
    re.IGNORECASE,
)

_EDUCATIONAL_PATTERNS = re.compile(
    r"\b("
    r"what\s+is\s+(?!my\b|the\s+capital|attendance|score|grade|mark)|"
    r"what\s+are\s+(?!my\b)|"
    r"explain|how\s+does|how\s+do|define\s+(?!my)|"
    r"tell\s+me\s+about|describe|overview\s+of|"
    r"difference\s+between|compare|pros\s+and\s+cons"
    r")\b",
    re.IGNORECASE,
)

_RESOURCE_PATTERNS = re.compile(
    r"\b("
    r"youtube|video|videos|link|links|url|urls|"
    r"resource|resources|tutorial|tutorials|course|playlist|"
    r"give\s+me\s+(a\s+)?link|find\s+me|send\s+me\s+link|"
    r"online\s+course|watch|website|site"
    r")\b",
    re.IGNORECASE,
)

_TASK_REQUEST_PATTERNS = re.compile(
    r"\b("
    r"i\s+want\s+to\s+learn|help\s+me\s+learn|teach\s+me|"
    r"how\s+do\s+i\s+learn|learning\s+path|learning\s+plan|roadmap|"
    r"steps\s+to\s+learn|how\s+to\s+start|where\s+to\s+start|"
    r"list\s+the\s+steps|list\s+the\s+topics|give\s+me\s+topics|"
    r"break\s+it\s+down|i\s+need\s+to\s+learn|i\s+want\s+to\s+understand"
    r")\b",
    re.IGNORECASE,
)

_EMOTIONAL_PATTERNS = re.compile(
    r"\b("
    r"panic\s+attack|breakdown|mental\s+breakdown|crying|suicid|self[\s-]harm|"
    r"can'?t\s+cope|severe\s+depression|deeply\s+depressed|clinical\s+depression"
    r")\b",
    re.IGNORECASE,
)

_GENERAL_STUDENT_PATTERNS = re.compile(
    r"\b("
    r"why\s+(?:will|am|do|should|would)\s+i\s+(?:study|go\s+to|attend|be\s+in)\s+(?:college|university|classes?|school)|"
    r"why\s+(?:study|go\s+to|attend)\s+(?:college|university)|"
    r"is\s+college\s+(?:even\s+)?(?:useful|worth\s+it|for\s+me|necessary|needed)|"
    r"why\s+should\s+i\s+attend\s+classes?|"
    r"why\s+(?:am\s+i|i\s+am)\s+studying|"
    r"will\s+i\s+be\s+able\s+to\s+study|"
    r"am\s+i\s+(?:capable|able)\s+(?:of\s+studying|to\s+study|of\s+finishing)|"
    r"can\s+i\s+(?:really\s+|still\s+)?(?:improve|recover|pass|succeed|do\s+well|make\s+it)|"
    r"do\s+you\s+think\s+i\s+can\s+(?:do\s+this|pass|succeed|improve|recover)|"
    r"will\s+i\s+ever\s+get\s+better|"
    r"what\s+if\s+i\s+fail|"
    r"fear\s+of\s+failing|afraid\s+of\s+failing|scared\s+of\s+failing|"
    r"why\s+(?:does\s+studying\s+feel|is\s+studying)\s+so\s+(?:difficult|hard|tough|exhausting)|"
    r"i\s+don'?t\s+feel\s+like\s+studying|"
    r"no\s+motivation|stay\s+motivated|how\s+(?:do|can)\s+i\s+stay\s+motivated|"
    r"what\s+should\s+i\s+do\s+when\s+i\s+(?:have\s+no\s+motivation|don'?t\s+feel\s+like\s+studying)|"
    r"i\s+feel\s+lost\s+about\s+(?:college|studies|my\s+studies|everything)|"
    r"i\s+feel\s+lost\b|"
    r"i\s+don'?t\s+know\s+what\s+to\s+do|"
    r"i\s+don'?t\s+know\s+if\s+college\s+is\s+(?:really\s+)?for\s+me|"
    r"all\s+this\s+studying\s+is\s+worth\s+it|"
    r"studying\s+is\s+worth\s+it|"
    r"capable\s+of\s+finishing|"
    r"is\s+it\s+too\s+late\s+for\s+me|"
    r"can\s+i\s+still\s+do\s+well|"
    r"difficulty\s+getting\s+started|hard\s+to\s+get\s+started|"
    r"feeling\s+overwhelmed|feel\s+overwhelmed|stressed\s+about\s+studies|"
    r"anxious\s+about\s+exams?|exam\s+anxiety|study\s+anxiety|"
    r"doubt\s+myself|self[\s-]doubt|confidence\s+in\s+studying|"
    r"scared\s+of\s+(?:getting\s+|being\s+)?(?:rejected|judged|left\s+out)|"
    r"fear\s+of\s+(?:rejection|being\s+rejected|failure)|"
    r"afraid\s+of\s+(?:rejection|being\s+rejected)|"
    r"love\s+myself\s+but|"
    r"why\s+(?:dint|didn'?t)\s+you\s+(?:answer|reply|respond)|"
    r"you\s+didn'?t\s+answer|"
    r"why\s+(?:am\s+i|i\s+am)\s+here"
    r")\b",
    re.IGNORECASE,
)

_SYSTEM_ARCHITECTURE_PATTERNS = re.compile(
    r"\b("
    r"which\s+(?:and\s+all\s+)?(?:the\s+)?agents|what\s+agents|list\s+agents|"
    r"agents\s+(?:do\s+)?i\s+have|agents\s+are\s+available|system\s+capabilities|"
    r"how\s+many\s+agents"
    r")\b",
    re.IGNORECASE,
)

_USER_PROFILE_PATTERNS = re.compile(
    r"\b("
    r"where\s+(?:am\s+i|i\s+am)\s+from|where\s+do\s+i\s+come\s+from|"
    r"my\s+hometown|which\s+city\s+am\s+i\s+from|what\s+is\s+my\s+department|"
    r"what\s+year\s+am\s+i\s+in|what\s+is\s+my\s+program"
    r")\b",
    re.IGNORECASE,
)

_CLARIFICATION_PATTERNS = re.compile(
    r"\b("
    r"why\s+(?:am\s+i|i\s+am)\s+here|what\s+am\s+i\s+doing\s+here|"
    r"why\s+am\s+i\s+in\s+this\s+chat|"
    r"why\s+(?:i\s+am|am\s+i)\s+here\s+not\s+you|"
    r"not\s+you\b.*\bwhy\s+(?:i\s+am|am\s+i)\s+here"
    r")\b",
    re.IGNORECASE,
)


def detect_constraints(user_message: str) -> ResponseConstraints:
    """
    Parses explicit format, brevity, word count, sentence count, and item constraints from user message.
    """
    msg = user_message.lower().strip()
    constraints = ResponseConstraints()

    # 1. Exact Word Count (e.g. "400 words", "in 400 words", "exactly 400 words", "400 word", "write 400 words")
    exact_wc_match = re.search(r"\b(?:exactly\s+|in\s+|write\s+)?(\d{1,5})\s*words?\b", msg)
    has_range_keyword = bool(re.search(r"\b(under|less\s+than|max|maximum|at\s+least|more\s+than|min|minimum|around|approx|approximately|about|roughly)\b", msg))

    if exact_wc_match and not has_range_keyword:
        count_val = int(exact_wc_match.group(1))
        if count_val > 1:
            constraints.exact_word_count = count_val
            # 10% tolerance policy: for 400 words -> 360 to 440 words
            constraints.min_word_count = int(count_val * 0.90)
            constraints.max_word_count = int(count_val * 1.10)
            constraints.max_words = count_val

    # 2. Maximum / Under Word Count (e.g. "under 100 words", "less than 100 words", "max 100 words", "within 100 words")
    max_wc_match = re.search(r"\b(?:under|less\s+than|max|maximum|within|up\s+to)\s+(\d{1,5})\s*words?\b", msg)
    if max_wc_match:
        val = int(max_wc_match.group(1))
        constraints.max_word_count = val
        constraints.max_words = val

    # 3. Minimum / At Least Word Count (e.g. "at least 300 words", "more than 300 words", "min 300 words", "minimum 300 words")
    min_wc_match = re.search(r"\b(?:at\s+least|more\s+than|min|minimum|greater\s+than)\s+(\d{1,5})\s*words?\b", msg)
    if min_wc_match:
        constraints.min_word_count = int(min_wc_match.group(1))

    # 4. Approximate Word Count (e.g. "around 400 words", "approx 400 words", "about 400 words", "roughly 400 words")
    approx_wc_match = re.search(r"\b(?:around|approx|approximately|about|roughly)\s+(\d{1,5})\s*words?\b", msg)
    if approx_wc_match:
        val = int(approx_wc_match.group(1))
        constraints.exact_word_count = val
        # Explicit tolerance policy for "around N words": ±10% (e.g. 360-440 words for 400)
        constraints.min_word_count = int(val * 0.90)
        constraints.max_word_count = int(val * 1.10)
        constraints.max_words = int(val * 1.10)

    # 5. One Word
    if re.search(r"\b(in\s+)?(1|one)\s+word\b|\bonly\s+the\s+name\b|\bjust\s+the\s+name\b|\bsingle\s+word\b", msg):
        constraints.one_word = True
        constraints.direct_answer = True
        constraints.exact_word_count = 1
        constraints.max_word_count = 1
        constraints.max_words = 1

    # 6. One Sentence / One Line
    if re.search(r"\b(in\s+)?(1|one)\s+(sentence|line)\b|\bsingle\s+sentence\b", msg):
        constraints.one_sentence = True
        constraints.one_line = True
        constraints.direct_answer = True
        constraints.exact_sentences = 1
        constraints.max_sentences = 1

    # 7. Exact count of items (e.g. "give me 3", "3 youtube videos", "3 points", "5 resources")
    item_match = re.search(r"\b(?:give\s+me\s+)?(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:points|ways|tips|steps|bullets|videos|links|items|resources)\b", msg)
    if item_match:
        val_str = item_match.group(1).lower()
        word_to_num = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
        constraints.exact_items = word_to_num.get(val_str, int(val_str) if val_str.isdigit() else None)

    # 8. Links Only / YouTube Only
    if re.search(r"\b(links?\s+only|just\s+(the\s+)?links?|only\s+links?|only\s+youtube|youtube\s+only|youtube\s+links?)\b", msg):
        constraints.links_only = True
        constraints.no_extra_text = True

    # 9. No Extra Text / Direct Plan Only
    if re.search(r"\b(no\s+extra\s+text|don'?t\s+give\s+(me\s+)?extra|no\s+bluff|don'?t\s+bluff|no\s+explanation|without\s+explanation|don'?t\s+explain|without\s+extra|only\s+the\s+plan)\b", msg):
        constraints.no_extra_text = True
        constraints.direct_answer = True

    # 10. Direct / Short Answer
    if re.search(r"\b(shorter|short\s+answer|briefly|just\s+the\s+answer|just\s+answer|direct\s+answer|only\s+answer|rapid\s+answer)\b", msg):
        constraints.short_answer = True
        constraints.direct_answer = True

    # 11. Yes or No
    if re.search(r"\byes\s+or\s+no\b", msg):
        constraints.yes_no = True

    # 12. No Emojis / Without Emojis
    if re.search(r"\b(no\s+emojis?|without\s+emojis?|zero\s+emojis?|don'?t\s+use\s+emojis?|no\s+emoticons?)\b", msg):
        constraints.no_emojis = True

    # 13. Professional / Formal Tone
    if re.search(r"\b(professional|formal|academic\s+tone|make\s+it\s+formal)\b", msg):
        constraints.professional = True

    return constraints


def resolve_followup_request(
    current_message: str,
    conversation_history: list[Any] | None = None,
) -> tuple[bool, str, str | None, str | None]:
    """
    Distinguishes between:
    1. NEW REQUEST
    2. FOLLOW-UP CONSTRAINT (e.g. "400 words", "in simple words", "make it formal", "7 days", "in one sentence", "only YouTube")
    3. FOLLOW-UP CONTINUATION / REFINEMENT (e.g. "shorter", "longer", "with examples")
    4. CLARIFICATION
    5. CORRECTION

    Returns:
        (is_followup, resolved_message, previous_request_text, followup_type)
    """
    if not conversation_history:
        return False, current_message, None, None

    msg = current_message.strip()
    msg_l = msg.lower().rstrip(".?!")

    # If message is an explicit question or full statement with a distinct subject, check if it's anaphoric
    is_anaphoric = bool(re.search(r"\b(make\s+it|do\s+it|write\s+it|explain\s+it|rewrite\s+it|give\s+it|convert\s+it|turn\s+it|change\s+it|adjust\s+it)\b", msg_l))

    # Check for pure constraint modifiers
    is_pure_word_count = bool(re.fullmatch(r"(?:in\s+|write\s+|make\s+it\s+|exactly\s+|around\s+|approx\s+|about\s+|under\s+|at\s+least\s+)?\d{1,5}\s*words?", msg_l))
    is_pure_brevity = msg_l in ("shorter", "longer", "more concise", "more detailed", "brief", "one paragraph", "in short", "elaborate", "simplify")
    is_pure_format = bool(re.fullmatch(r"(?:in\s+)?(?:1|one)\s+(?:word|sentence|line)|3\s+points|\d+\s*(?:points|ways|tips|steps|bullets)|only\s+links|links\s+only|only\s+youtube|youtube\s+only|just\s+the\s+links?", msg_l))
    is_pure_tone = bool(re.fullmatch(r"(?:make\s+it\s+)?(?:formal|simpler|simple|casual|for\s+beginners|in\s+simple\s+words|in\s+simple\s+terms|simple\s+language)", msg_l))
    is_pure_duration = bool(re.fullmatch(r"(?:for\s+|make\s+it\s+for\s+)?\d+\s*days?|(?:for\s+)?(?:a|one|1)\s*week|weekly|monthly", msg_l))
    is_pure_examples = msg_l in ("with examples", "give examples", "add examples", "include examples")

    is_modifier = is_anaphoric or is_pure_word_count or is_pure_brevity or is_pure_format or is_pure_tone or is_pure_duration or is_pure_examples

    if not is_modifier:
        # Check if short message under 5 words without a clear independent question verb
        words = msg.split()
        if len(words) <= 4 and not any(k in msg_l for k in ["what is my", "who am i", "where am i", "why am i", "what are you", "where are you", "who are you", "my name is", "i am from"]):
            if any(k in msg_l for k in ["word", "sentence", "line", "day", "point", "simple", "formal", "youtube", "link", "example", "detail", "beginner", "short", "long"]):
                is_modifier = True

    if not is_modifier:
        return False, current_message, None, None

    # Find the most recent meaningful user request from conversation history
    prev_user_req: str | None = None
    for item in reversed(conversation_history):
        role = getattr(item, "role", None)
        if role is None and isinstance(item, dict):
            role = item.get("role")
        content = getattr(item, "content", None)
        if content is None and isinstance(item, dict):
            content = item.get("content")

        if str(role).lower() == "user" and content:
            content_str = str(content).strip()
            # Skip identity declarations or questions
            if not re.match(r"^(?:hi|hello|hey|my\s+name\s+is\s+\w+|who\s+am\s+i|where\s+am\s+i\s+from)\b", content_str.lower()):
                prev_user_req = content_str
                break

    if not prev_user_req:
        return False, current_message, None, None

    # Clean the previous request
    prev_clean = prev_user_req.strip().rstrip(".?!")

    # Synthesize the resolved request
    followup_type = "followup_constraint"
    if is_pure_word_count:
        wc_match = re.search(r"(\d{1,5})", msg_l)
        wc = wc_match.group(1) if wc_match else "400"
        resolved = f"{prev_clean} in {wc} words."
    elif "7 days" in msg_l or "for 7 days" in msg_l or "7 day" in msg_l or is_pure_duration:
        dur_match = re.search(r"(\d+\s*days?|week)", msg_l)
        dur = dur_match.group(1) if dur_match else "7 days"
        resolved = f"{prev_clean} for {dur}."
    elif "simple words" in msg_l or "simpler" in msg_l or "for beginners" in msg_l:
        resolved = f"{prev_clean} in simple words."
    elif "formal" in msg_l:
        resolved = f"Write a formal version of: {prev_clean}."
    elif "one sentence" in msg_l or "1 sentence" in msg_l or "in one line" in msg_l:
        resolved = f"{prev_clean} in one sentence."
    elif "only youtube" in msg_l or "youtube" in msg_l:
        resolved = f"{prev_clean} using only YouTube resources."
    elif "3 points" in msg_l or "3 ways" in msg_l:
        resolved = f"{prev_clean} in 3 points."
    elif "shorter" in msg_l or "more concise" in msg_l:
        resolved = f"Provide a shorter, more concise version of: {prev_clean}."
    elif "longer" in msg_l or "elaborate" in msg_l or "with examples" in msg_l:
        resolved = f"{prev_clean} with detailed examples."
    elif is_anaphoric:
        resolved = f"{prev_clean}, {msg}."
    else:
        resolved = f"{prev_clean} ({msg})."

    return True, resolved, prev_user_req, followup_type


def detect_response_mode(
    user_message: str,
    teaching_state: Any | None = None,
    quiz_state: Any | None = None,
) -> ResponseMode:
    """
    Classifies a user message into one of ResponseMode values.
    """
    msg = user_message.strip()
    if not msg:
        return ResponseMode.CONVERSATIONAL

    # Format constraints
    constraints = detect_constraints(msg)
    if constraints.one_word or constraints.one_sentence or constraints.no_extra_text or constraints.exact_word_count:
        if is_name_query(msg) or is_hometown_query(msg) or _IDENTITY_PATTERNS.search(msg):
            return ResponseMode.IDENTITY
        if _RESOURCE_PATTERNS.search(msg):
            return ResponseMode.RESOURCE_REQUEST
        if _DIRECT_FACTUAL_PATTERNS.search(msg):
            return ResponseMode.DIRECT_FACTUAL
        if _PLAN_PATTERNS.search(msg):
            return ResponseMode.STUDY_PLAN
        if _TASK_REQUEST_PATTERNS.search(msg):
            return ResponseMode.TASK_REQUEST
        return ResponseMode.FORMAT_CONSTRAINED

    # 1. Top-Level Overrides (Checked before Teach Me or Quiz modes)
    if _SYSTEM_ARCHITECTURE_PATTERNS.search(msg):
        return ResponseMode.SYSTEM_ARCHITECTURE

    if _CLARIFICATION_PATTERNS.search(msg):
        return ResponseMode.CLARIFICATION

    if _USER_PROFILE_PATTERNS.search(msg):
        return ResponseMode.USER_PROFILE

    if is_name_query(msg) or is_hometown_query(msg) or _IDENTITY_PATTERNS.search(msg):
        return ResponseMode.IDENTITY

    if _PLAN_PATTERNS.search(msg):
        return ResponseMode.STUDY_PLAN

    if _ACADEMIC_PATTERNS.search(msg):
        return ResponseMode.ACADEMIC_INSIGHT

    if _EMOTIONAL_PATTERNS.search(msg):
        return ResponseMode.EMOTIONAL_SUPPORT

    # 2. Teach Me & Quiz Exit Checks
    if _TEACH_ME_EXIT_PATTERN.search(msg) or _QUIZ_EXIT_PATTERN.search(msg):
        return ResponseMode.CONVERSATIONAL

    # 3. Quiz Start Check
    is_quiz_start = extract_quiz_params(msg)[0]
    if is_quiz_start:
        return ResponseMode.QUIZ_ME

    # 4. Active Quiz Session Check
    if quiz_state and getattr(quiz_state, "active", False):
        return ResponseMode.QUIZ_ME

    # 5. Teach Me Start Check
    is_teach_start, _, _ = extract_teach_me_topic(msg)
    if is_teach_start:
        return ResponseMode.TEACH_ME

    # 6. Active Teaching Session Check
    if teaching_state and getattr(teaching_state, "active", False):
        return ResponseMode.TEACH_ME

    if _GENERAL_STUDENT_PATTERNS.search(msg):
        return ResponseMode.GENERAL_STUDENT_CONVERSATION

    if _RESOURCE_PATTERNS.search(msg):
        return ResponseMode.RESOURCE_RECOMMENDATION

    # Conversational keywords check
    msg_l = msg.lower()
    student_keywords = [
        "fail", "grade", "grades", "exam", "exams", "study", "studying", "class", "classes",
        "assignment", "assignments", "homework", "gpa", "marks", "attendance", "absent",
        "professor", "teacher", "lecture", "revision", "syllabus", "subject", "subjects"
    ]
    student_inquiry_markers = [
        "what", "how", "why", "when", "can", "should", "help", "struggle", "struggling",
        "behind", "catch up", "stress", "stressed", "anxious", "worried", "tips", "advice",
        "doubt", "lost", "unsure", "confused", "give up", "worth it", "for me",
        "get started", "getting started", "feel like"
    ]
    has_student_kw = any(k in msg_l for k in student_keywords)
    has_inquiry_marker = any(m in msg_l for m in student_inquiry_markers)
    if has_student_kw and has_inquiry_marker:
        return ResponseMode.GENERAL_STUDENT_CONVERSATION

    return ResponseMode.CONVERSATIONAL


def process_user_request(
    user_message: str,
    user_facts: UserFacts,
    student_context: StudentContext | None = None,
    conversation_history: list[Any] | None = None,
    teaching_state: Any | None = None,
    quiz_state: Any | None = None,
    learning_history: dict[str, Any] | None = None,
) -> ProcessedRequest:
    """
    Full semantic, follow-up, and constraint processing for the incoming message.
    """
    msg = user_message.strip()

    # 0. Centralized Input Guardrails Evaluation
    guardrails = get_guardrails_service()
    guardrail_result = guardrails.validate_input(
        user_message=msg,
        student_context=student_context,
    )
    if guardrail_result.is_blocked:
        logger.warning(
            "process_user_request: Input blocked by guardrail category=%s reason=%r",
            guardrail_result.category.value,
            guardrail_result.reason,
        )
        return ProcessedRequest(
            intent=RequestIntent.GENERAL_CONVERSATION,
            workflow_intent=IntentType.GENERAL_SUPPORT,
            response_mode=ResponseMode.CONVERSATIONAL,
            constraints=ResponseConstraints(),
            is_deterministic=True,
            deterministic_answer=guardrail_result.blocked_response,
            confidence=1.0,
            reasoning=f"Input guardrail triggered: {guardrail_result.reason} ({guardrail_result.category.value})",
            is_followup=False,
            resolved_message=msg,
            teaching_state=teaching_state,
            quiz_state=quiz_state,
        )

    # 1. Resolve Conversational Follow-Up Requests (e.g. "400 words", "in simple words", "7 days")
    is_followup, resolved_msg, prev_req, followup_type = resolve_followup_request(
        current_message=msg,
        conversation_history=conversation_history,
    )

    effective_msg = resolved_msg if is_followup and resolved_msg else msg

    # 2. Extract Constraints from both current message and resolved message (current takes precedence)
    constraints = detect_constraints(msg)
    if is_followup:
        resolved_constraints = detect_constraints(resolved_msg)
        # Merge constraints
        for field_name in ResponseConstraints.model_fields.keys():
            curr_val = getattr(constraints, field_name)
            res_val = getattr(resolved_constraints, field_name)
            if curr_val is None or curr_val is False:
                if res_val is not None and res_val is not False:
                    setattr(constraints, field_name, res_val)

    # 3. Detect Response Mode from effective resolved message
    response_mode = detect_response_mode(effective_msg, teaching_state=teaching_state, quiz_state=quiz_state)

    # Check Quiz Exit command
    if _QUIZ_EXIT_PATTERN.search(msg):
        if quiz_state and getattr(quiz_state, "active", False):
            topic_str = getattr(quiz_state, "topic", "") or "your quiz"
            exit_reply = f"We've paused the quiz on {topic_str}. 🧠 Whenever you're ready to test your knowledge again, just say 'Quiz me'! What would you like to work on next?"
            deactivated_quiz = QuizState(
                active=False,
                topic=getattr(quiz_state, "topic", ""),
                difficulty=getattr(quiz_state, "difficulty", QuizDifficulty.BEGINNER),
                step=QuizStep.COMPLETED,
                total_questions=getattr(quiz_state, "total_questions", 5),
                score=getattr(quiz_state, "score", 0.0),
            )
            return ProcessedRequest(
                intent=RequestIntent.GENERAL_CONVERSATION,
                workflow_intent=IntentType.GENERAL_SUPPORT,
                response_mode=ResponseMode.CONVERSATIONAL,
                constraints=constraints,
                is_deterministic=True,
                deterministic_answer=exit_reply,
                confidence=1.0,
                reasoning="User explicitly exited Quiz mode",
                is_followup=is_followup,
                resolved_message=effective_msg,
                teaching_state=teaching_state,
                quiz_state=deactivated_quiz,
            )
        else:
            return ProcessedRequest(
                intent=RequestIntent.GENERAL_CONVERSATION,
                workflow_intent=IntentType.GENERAL_SUPPORT,
                response_mode=ResponseMode.CONVERSATIONAL,
                constraints=constraints,
                is_deterministic=True,
                deterministic_answer="No active quiz is running right now. 🧠 Just say 'Quiz me on <topic>' whenever you'd like to test your understanding!",
                confidence=1.0,
                reasoning="No active quiz session to exit",
                is_followup=is_followup,
                resolved_message=effective_msg,
                teaching_state=teaching_state,
            )

    # Check Teach Me Exit command
    if _TEACH_ME_EXIT_PATTERN.search(msg):
        if teaching_state and getattr(teaching_state, "active", False):
            topic_str = getattr(teaching_state, "topic", "") or "this topic"
            exit_reply = f"We've paused our lesson on {topic_str}. 🌱 Whenever you're ready to resume learning, just say 'Teach me {topic_str}'! What would you like to work on next?"
            deactivated_state = TeachingState(
                active=False,
                topic=getattr(teaching_state, "topic", ""),
                difficulty=getattr(teaching_state, "difficulty", TeachingDifficulty.BEGINNER),
                step=TeachingStep.COMPLETED,
            )
            return ProcessedRequest(
                intent=RequestIntent.GENERAL_CONVERSATION,
                workflow_intent=IntentType.GENERAL_SUPPORT,
                response_mode=ResponseMode.CONVERSATIONAL,
                constraints=constraints,
                is_deterministic=True,
                deterministic_answer=exit_reply,
                confidence=1.0,
                reasoning="User explicitly exited Teach Me mode",
                is_followup=is_followup,
                resolved_message=effective_msg,
                teaching_state=deactivated_state,
                quiz_state=quiz_state,
            )
        else:
            return ProcessedRequest(
                intent=RequestIntent.GENERAL_CONVERSATION,
                workflow_intent=IntentType.GENERAL_SUPPORT,
                response_mode=ResponseMode.CONVERSATIONAL,
                constraints=constraints,
                is_deterministic=True,
                deterministic_answer="No active tutoring lesson is running right now. 🌱 What would you like to study or work on?",
                confidence=1.0,
                reasoning="No active teaching session to exit",
                is_followup=is_followup,
                resolved_message=effective_msg,
                quiz_state=quiz_state,
            )

    # Check Quiz Start command
    is_quiz_start, quiz_topic, quiz_diff, quiz_total, has_explicit_diff = extract_quiz_params(msg)
    if is_quiz_start:
        deactivated_teach = None
        if teaching_state and getattr(teaching_state, "active", False):
            deactivated_teach = TeachingState(
                active=False,
                topic=getattr(teaching_state, "topic", ""),
                difficulty=getattr(teaching_state, "difficulty", TeachingDifficulty.BEGINNER),
                step=TeachingStep.COMPLETED,
            )

        if quiz_topic is None:
            prompt_reply = "What topic would you like to be quizzed on? 🧠 You can choose any subject or concept (for example: binary trees, neural networks, DBMS, or Java inheritance)!"
            new_quiz = QuizState(
                active=True,
                topic="",
                difficulty=quiz_diff,
                total_questions=quiz_total,
                step=QuizStep.AWAITING_TOPIC,
                metadata={"has_explicit_diff": has_explicit_diff, "explicit_diff": quiz_diff.value if has_explicit_diff else None},
            )
            return ProcessedRequest(
                intent=RequestIntent.QUIZ_ME,
                workflow_intent=IntentType.GENERAL_SUPPORT,
                response_mode=ResponseMode.QUIZ_ME,
                constraints=constraints,
                is_deterministic=True,
                deterministic_answer=prompt_reply,
                confidence=1.0,
                reasoning="Quiz starter prompted for topic",
                is_followup=is_followup,
                resolved_message=effective_msg,
                teaching_state=deactivated_teach or teaching_state,
                quiz_state=new_quiz,
            )
        else:
            initial_diff = determine_initial_quiz_difficulty(
                topic=quiz_topic,
                explicit_difficulty=quiz_diff,
                has_explicit_diff=has_explicit_diff,
                learning_history=learning_history,
            )
            new_quiz = QuizState(
                active=True,
                topic=quiz_topic,
                difficulty=initial_diff,
                total_questions=quiz_total,
                step=QuizStep.IN_PROGRESS,
                current_question_number=1,
                difficulty_history=[initial_diff.value],
            )
            return ProcessedRequest(
                intent=RequestIntent.QUIZ_ME,
                workflow_intent=IntentType.GENERAL_SUPPORT,
                response_mode=ResponseMode.QUIZ_ME,
                constraints=constraints,
                is_deterministic=False,
                confidence=1.0,
                reasoning=f"Starting Adaptive Quiz on '{quiz_topic}' ({quiz_total} questions, {initial_diff.value})",
                is_followup=is_followup,
                resolved_message=effective_msg,
                teaching_state=deactivated_teach or teaching_state,
                quiz_state=new_quiz,
            )

    # Check if student was awaiting quiz topic
    if quiz_state and getattr(quiz_state, "active", False) and getattr(quiz_state, "step", None) == QuizStep.AWAITING_TOPIC:
        chosen_topic = msg.strip().rstrip(".?!")
        meta = getattr(quiz_state, "metadata", {}) or {}
        has_exp = meta.get("has_explicit_diff", False)
        exp_d = QuizDifficulty(meta["explicit_diff"]) if meta.get("explicit_diff") else getattr(quiz_state, "difficulty", QuizDifficulty.BEGINNER)
        initial_diff = determine_initial_quiz_difficulty(
            topic=chosen_topic,
            explicit_difficulty=exp_d,
            has_explicit_diff=has_exp,
            learning_history=learning_history,
        )
        new_quiz = QuizState(
            active=True,
            topic=chosen_topic,
            difficulty=initial_diff,
            total_questions=getattr(quiz_state, "total_questions", 5),
            step=QuizStep.IN_PROGRESS,
            current_question_number=1,
            difficulty_history=[initial_diff.value],
        )
        return ProcessedRequest(
            intent=RequestIntent.QUIZ_ME,
            workflow_intent=IntentType.GENERAL_SUPPORT,
            response_mode=ResponseMode.QUIZ_ME,
            constraints=constraints,
            is_deterministic=False,
            confidence=1.0,
            reasoning=f"Quiz topic received from student: '{chosen_topic}' (difficulty: {initial_diff.value})",
            is_followup=is_followup,
            resolved_message=effective_msg,
            teaching_state=teaching_state,
            quiz_state=new_quiz,
        )

    # If quiz is active and response_mode == QUIZ_ME (and no higher priority intent overrode it)
    if response_mode == ResponseMode.QUIZ_ME:
        return ProcessedRequest(
            intent=RequestIntent.QUIZ_ME,
            workflow_intent=IntentType.GENERAL_SUPPORT,
            response_mode=ResponseMode.QUIZ_ME,
            constraints=constraints,
            is_deterministic=False,
            confidence=1.0,
            reasoning="In-session Quiz turn (evaluating student answer & progressing question)",
            is_followup=is_followup,
            resolved_message=effective_msg,
            teaching_state=teaching_state,
            quiz_state=quiz_state,
        )

    # Check Teach Me Start command
    is_teach_start, teach_topic, teach_diff = extract_teach_me_topic(msg)
    if is_teach_start:
        deactivated_quiz = None
        if quiz_state and getattr(quiz_state, "active", False):
            deactivated_quiz = QuizState(
                active=False,
                topic=getattr(quiz_state, "topic", ""),
                difficulty=getattr(quiz_state, "difficulty", QuizDifficulty.BEGINNER),
                step=QuizStep.COMPLETED,
            )

        if teach_topic is None:
            prompt_reply = "What would you like to learn? 🌱 You can choose any subject or concept (for example: binary trees, neural networks, Java inheritance, or operating systems)!"
            new_state = TeachingState(
                active=True,
                topic="",
                difficulty=teach_diff,
                step=TeachingStep.AWAITING_TOPIC,
            )
            return ProcessedRequest(
                intent=RequestIntent.TEACH_ME,
                workflow_intent=IntentType.GENERAL_SUPPORT,
                response_mode=ResponseMode.TEACH_ME,
                constraints=constraints,
                is_deterministic=True,
                deterministic_answer=prompt_reply,
                confidence=1.0,
                reasoning="Teach Me starter prompted for topic",
                is_followup=is_followup,
                resolved_message=effective_msg,
                teaching_state=new_state,
                quiz_state=deactivated_quiz or quiz_state,
            )
        else:
            new_state = TeachingState(
                active=True,
                topic=teach_topic,
                difficulty=teach_diff,
                step=TeachingStep.TEACHING,
                support_level=0,
                confusion_count=0,
                support_strategy="normal",
            )
            return ProcessedRequest(
                intent=RequestIntent.TEACH_ME,
                workflow_intent=IntentType.GENERAL_SUPPORT,
                response_mode=ResponseMode.TEACH_ME,
                constraints=constraints,
                is_deterministic=False,
                confidence=1.0,
                reasoning=f"Starting Teach Me session on '{teach_topic}'",
                is_followup=is_followup,
                resolved_message=effective_msg,
                teaching_state=new_state,
                quiz_state=deactivated_quiz or quiz_state,
            )

    # Check if student was awaiting teach me topic
    if teaching_state and getattr(teaching_state, "active", False) and getattr(teaching_state, "step", None) == TeachingStep.AWAITING_TOPIC:
        chosen_topic = msg.strip().rstrip(".?!")
        new_state = TeachingState(
            active=True,
            topic=chosen_topic,
            difficulty=getattr(teaching_state, "difficulty", TeachingDifficulty.BEGINNER),
            step=TeachingStep.TEACHING,
            support_level=0,
            confusion_count=0,
            support_strategy="normal",
        )

        return ProcessedRequest(
            intent=RequestIntent.TEACH_ME,
            workflow_intent=IntentType.GENERAL_SUPPORT,
            response_mode=ResponseMode.TEACH_ME,
            constraints=constraints,
            is_deterministic=False,
            confidence=1.0,
            reasoning=f"Topic received from student: '{chosen_topic}'",
            is_followup=is_followup,
            resolved_message=effective_msg,
            teaching_state=new_state,
            quiz_state=quiz_state,
        )

    # If teaching is active and response_mode == TEACH_ME (and no higher priority intent overrode it)
    if response_mode == ResponseMode.TEACH_ME:
        return ProcessedRequest(
            intent=RequestIntent.TEACH_ME,
            workflow_intent=IntentType.GENERAL_SUPPORT,
            response_mode=ResponseMode.TEACH_ME,
            constraints=constraints,
            is_deterministic=False,
            confidence=1.0,
            reasoning="In-session Teach Me turn (answer evaluation or concept progression)",
            is_followup=is_followup,
            resolved_message=effective_msg,
            teaching_state=teaching_state,
            quiz_state=quiz_state,
        )

    # 4. Check for deterministic fast-path answer on effective message
    is_det, det_ans, det_intent = try_resolve_deterministic_answer(
        message=msg,
        user_facts=user_facts,
        constraints=constraints,
        student_context=student_context,
    )

    if is_det and det_ans is not None:
        deactivated_teach = None
        if teaching_state and getattr(teaching_state, "active", False) and response_mode != ResponseMode.IDENTITY:
            deactivated_teach = TeachingState(
                active=False,
                topic=getattr(teaching_state, "topic", ""),
                difficulty=getattr(teaching_state, "difficulty", TeachingDifficulty.BEGINNER),
                step=TeachingStep.COMPLETED,
            )
        deactivated_quiz = None
        if quiz_state and getattr(quiz_state, "active", False) and response_mode != ResponseMode.IDENTITY:
            deactivated_quiz = QuizState(
                active=False,
                topic=getattr(quiz_state, "topic", ""),
                difficulty=getattr(quiz_state, "difficulty", QuizDifficulty.BEGINNER),
                step=QuizStep.COMPLETED,
            )
        return ProcessedRequest(
            intent=det_intent or RequestIntent.GENERAL_CONVERSATION,
            workflow_intent=IntentType.GENERAL_SUPPORT,
            response_mode=response_mode,
            constraints=constraints,
            is_deterministic=True,
            deterministic_answer=det_ans,
            confidence=1.0,
            reasoning="Resolved deterministically via fast-path",
            is_followup=is_followup,
            resolved_message=effective_msg,
            previous_request=prev_req,
            followup_type=followup_type,
            teaching_state=deactivated_teach or teaching_state,
            quiz_state=deactivated_quiz or quiz_state,
        )

    # 5. Map response_mode to workflow RequestIntent and IntentType
    deactivated_teach = None
    if teaching_state and getattr(teaching_state, "active", False) and response_mode in (
        ResponseMode.STUDY_PLAN, ResponseMode.ACADEMIC_INSIGHT, ResponseMode.USER_PROFILE, ResponseMode.QUIZ_ME
    ):
        deactivated_teach = TeachingState(
            active=False,
            topic=getattr(teaching_state, "topic", ""),
            difficulty=getattr(teaching_state, "difficulty", TeachingDifficulty.BEGINNER),
            step=TeachingStep.COMPLETED,
        )

    deactivated_quiz = None
    if quiz_state and getattr(quiz_state, "active", False) and response_mode in (
        ResponseMode.STUDY_PLAN, ResponseMode.ACADEMIC_INSIGHT, ResponseMode.USER_PROFILE, ResponseMode.TEACH_ME
    ):
        deactivated_quiz = QuizState(
            active=False,
            topic=getattr(quiz_state, "topic", ""),
            difficulty=getattr(quiz_state, "difficulty", QuizDifficulty.BEGINNER),
            step=QuizStep.COMPLETED,
        )

    if response_mode == ResponseMode.STUDY_PLAN:
        req_intent = RequestIntent.STUDY_PLAN
        wf_intent = IntentType.STUDY_PLANNING
    elif response_mode == ResponseMode.ACADEMIC_INSIGHT:
        req_intent = RequestIntent.ACADEMIC_INSIGHT
        wf_intent = IntentType.ACADEMIC_INSIGHT
    elif response_mode == ResponseMode.IDENTITY:
        req_intent = RequestIntent.IDENTITY
        wf_intent = IntentType.GENERAL_SUPPORT
    elif response_mode == ResponseMode.USER_PROFILE:
        req_intent = RequestIntent.USER_PROFILE
        wf_intent = IntentType.GENERAL_SUPPORT
    elif response_mode == ResponseMode.SYSTEM_ARCHITECTURE:
        req_intent = RequestIntent.SYSTEM_ARCHITECTURE
        wf_intent = IntentType.GENERAL_SUPPORT
    elif response_mode == ResponseMode.CLARIFICATION:
        req_intent = RequestIntent.CLARIFICATION
        wf_intent = IntentType.GENERAL_SUPPORT
    elif response_mode == ResponseMode.DIRECT_FACTUAL:
        req_intent = RequestIntent.FACTUAL
        wf_intent = IntentType.GENERAL_SUPPORT
    elif response_mode == ResponseMode.EDUCATIONAL:
        req_intent = RequestIntent.EDUCATIONAL
        wf_intent = IntentType.GENERAL_SUPPORT
    elif response_mode == ResponseMode.RESOURCE_REQUEST:
        req_intent = RequestIntent.RESOURCE_REQUEST
        wf_intent = IntentType.GENERAL_SUPPORT
    elif response_mode == ResponseMode.TASK_REQUEST:
        req_intent = RequestIntent.EDUCATIONAL
        wf_intent = IntentType.GENERAL_SUPPORT
    elif response_mode == ResponseMode.EMOTIONAL_SUPPORT:
        req_intent = RequestIntent.EMOTIONAL_SUPPORT
        wf_intent = IntentType.GENERAL_SUPPORT
    elif response_mode == ResponseMode.GENERAL_STUDENT_CONVERSATION:
        req_intent = RequestIntent.GENERAL_STUDENT_CONVERSATION
        wf_intent = IntentType.GENERAL_SUPPORT
    elif response_mode == ResponseMode.TEACH_ME:
        req_intent = RequestIntent.TEACH_ME
        wf_intent = IntentType.GENERAL_SUPPORT
    elif response_mode == ResponseMode.QUIZ_ME:
        req_intent = RequestIntent.QUIZ_ME
        wf_intent = IntentType.GENERAL_SUPPORT
    else:
        req_intent = RequestIntent.GENERAL_CONVERSATION
        wf_intent = IntentType.GENERAL_SUPPORT

    return ProcessedRequest(
        intent=req_intent,
        workflow_intent=wf_intent,
        response_mode=response_mode,
        constraints=constraints,
        is_deterministic=False,
        deterministic_answer=None,
        confidence=0.95,
        reasoning=f"Classified as {req_intent.value} with mode {response_mode.value}" + (f" (followup from '{prev_req}')" if is_followup else ""),
        is_followup=is_followup,
        resolved_message=effective_msg,
        previous_request=prev_req,
        followup_type=followup_type,
        teaching_state=deactivated_teach or teaching_state,
        quiz_state=deactivated_quiz or quiz_state,
    )


def classify_intent_detailed(user_message: str) -> IntentClassification:
    """Classifies user message into a typed IntentClassification (backwards compatible)."""
    facts = UserFacts()
    processed = process_user_request(user_message, facts)
    return IntentClassification(
        intent=processed.workflow_intent,
        confidence=processed.confidence,
        reasoning=processed.reasoning,
        response_mode=processed.response_mode,
        constraints=processed.constraints,
    )


def classify_intent(state: GraphState) -> str:
    """Classifies student message from state."""
    msg = state.get("user_message", "") or ""
    classification = classify_intent_detailed(msg)
    return classification.intent.value


def is_planning_intent(intent: Union[IntentType, str]) -> bool:
    """Checks if an intent represents study planning."""
    val = intent.value if isinstance(intent, IntentType) else str(intent).lower()
    return val in ("study_planning", "plan")


def is_academic_intent(intent: Union[IntentType, str]) -> bool:
    """Checks if an intent represents academic insight."""
    val = intent.value if isinstance(intent, IntentType) else str(intent).lower()
    return val in ("academic_insight", "academic")


def route_after_intent(state: GraphState) -> str:
    """
    Conditional edge function after request processing.
    Directs deterministic and fast-path responses straight to the response validator.
    """
    processed = state.get("processed_request")
    is_det = False
    if isinstance(processed, dict):
        is_det = bool(processed.get("is_deterministic"))
    elif hasattr(processed, "is_deterministic"):
        is_det = bool(getattr(processed, "is_deterministic"))

    final_resp = state.get("final_response")
    if is_det or (final_resp and getattr(final_resp, "response_text", None)):
        return "response_validator"

    intent = state.get("intent", IntentType.GENERAL_SUPPORT)
    if is_planning_intent(intent) or is_academic_intent(intent):
        return "student_insight"
    return "recovery_coach"



def route_after_insight(state: GraphState) -> str:
    """
    Conditional edge function executed after Student Insight Agent.
    """
    intent = state.get("intent", IntentType.GENERAL_SUPPORT)
    if is_planning_intent(intent):
        return "study_planner"
    return "recovery_coach"
