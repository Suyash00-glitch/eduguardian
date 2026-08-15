"""
Router Component — Intent Classification, Constraint Parsing, and Conditional Routing.

Determines the student's request intent, parses explicit response constraints,
checks for deterministic fast-paths, and provides conditional edge routing functions
for the LangGraph StateGraph.
"""
from __future__ import annotations

import logging
import re
from typing import Union

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
from chatbot.backend.core.memory import UserFacts
from chatbot.backend.orchestrator.deterministic import try_resolve_deterministic_answer

logger = logging.getLogger(__name__)

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
    r"grades?|marks?|gpa|attendance|classes attended|missed classes|"
    r"how am i doing|my progress|my performance|my standing|academic situation|"
    r"why am i struggling|struggling with|falling behind|catch up|"
    r"why are my (marks|grades|scores) (dropping|slipping|low)|"
    r"failing|exam results?|quiz scores?|assessment scores?|"
    r"which subjects?|what topics? to focus on|where do i need to improve|"
    r"what should i focus on next"
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
    r"stress|stressed|anxious|anxiety|depress|depressed|depression|overwhelm|overwhelmed|"
    r"worry|worried|scared|tired|exhausted|hopeless|give\s+up|giving\s+up|impossible|stupid|dumb|"
    r"feel\s+like\s+i'?m?\s+(not|failing|behind|hopeless|depressed|lost)|"
    r"not\s+good\s+at|can'?t\s+understand|falling\s+behind|lost\b|"
    r"not\s+trusting|trust\s+myself|doubt|confidence|self[\s-]doubt|"
    r"why\s+do\s+(?:you|u)\s+(?:think|thing)\s+(?:i\s+)?(?:can|will\s+be\s+able)|"
    r"i\s+am\s+bad|i'?m\s+bad|hard\s+time|feel\s+like\s+i\s+am\s+not|"
    r"what\s+i\s+need\s+to\s+d\b|what\s+should\s+i\s+do\s+about\s+my\s+stress"
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
    Parses explicit format, brevity, and item constraints from user message.
    """
    msg = user_message.lower().strip()
    constraints = ResponseConstraints()

    # One Word
    if re.search(r"\b(in\s+)?(1|one)\s+word\b|\bonly\s+the\s+name\b|\bjust\s+the\s+name\b|\bsingle\s+word\b", msg):
        constraints.one_word = True
        constraints.direct_answer = True
        constraints.max_words = 1

    # One Sentence / One Line
    if re.search(r"\b(in\s+)?(1|one)\s+(sentence|line)\b|\bsingle\s+sentence\b", msg):
        constraints.one_sentence = True
        constraints.direct_answer = True
        constraints.max_sentences = 1

    # Exact count of items (e.g. "give me 3", "3 youtube videos", "3 points")
    item_match = re.search(r"\b(?:give\s+me\s+)?(\d+|three|two|four|five)\s+(?:points|ways|tips|steps|bullets|videos|links|items|resources)\b", msg)
    if item_match:
        val_str = item_match.group(1).lower()
        word_to_num = {"two": 2, "three": 3, "four": 4, "five": 5}
        constraints.exact_items = word_to_num.get(val_str, int(val_str) if val_str.isdigit() else None)

    # Links Only
    if re.search(r"\b(links?\s+only|just\s+(the\s+)?links?|only\s+links?)\b", msg):
        constraints.links_only = True
        constraints.no_extra_text = True

    # No Extra Text / No Bluff / No Explanation
    if re.search(r"\b(no\s+extra\s+text|don'?t\s+give\s+(me\s+)?extra|no\s+bluff|don'?t\s+bluff|no\s+explanation|without\s+explanation|don'?t\s+explain|without\s+extra|direct\s+plan\s+and\s+don'?t\s+give\s+extra)\b", msg):
        constraints.no_extra_text = True
        constraints.direct_answer = True

    # Direct / Short Answer
    if re.search(r"\b(shorter|short\s+answer|briefly|just\s+the\s+answer|just\s+answer|direct\s+answer|only\s+answer|rapid\s+answer)\b", msg):
        constraints.short_answer = True
        constraints.direct_answer = True

    # Yes or No
    if re.search(r"\byes\s+or\s+no\b", msg):
        constraints.yes_no = True

    return constraints


def detect_response_mode(user_message: str) -> ResponseMode:
    """
    Classifies a user message into one of ResponseMode values.
    """
    msg = user_message.strip()
    if not msg:
        return ResponseMode.CONVERSATIONAL

    # Format constraints
    constraints = detect_constraints(msg)
    if constraints.one_word or constraints.one_sentence or constraints.no_extra_text:
        # Check if it's also identity
        if _IDENTITY_PATTERNS.search(msg):
            return ResponseMode.IDENTITY
        if _RESOURCE_PATTERNS.search(msg):
            return ResponseMode.RESOURCE_REQUEST
        if _DIRECT_FACTUAL_PATTERNS.search(msg):
            return ResponseMode.DIRECT_FACTUAL
        return ResponseMode.FORMAT_CONSTRAINED

    if _SYSTEM_ARCHITECTURE_PATTERNS.search(msg):
        return ResponseMode.SYSTEM_ARCHITECTURE

    if _CLARIFICATION_PATTERNS.search(msg):
        return ResponseMode.CLARIFICATION

    if _USER_PROFILE_PATTERNS.search(msg):
        return ResponseMode.USER_PROFILE

    if _IDENTITY_PATTERNS.search(msg):
        return ResponseMode.IDENTITY

    if _PLAN_PATTERNS.search(msg):
        return ResponseMode.STUDY_PLAN

    if _ACADEMIC_PATTERNS.search(msg):
        return ResponseMode.ACADEMIC_INSIGHT

    if _EMOTIONAL_PATTERNS.search(msg):
        return ResponseMode.EMOTIONAL_SUPPORT

    if _RESOURCE_PATTERNS.search(msg):
        return ResponseMode.RESOURCE_REQUEST

    if _TASK_REQUEST_PATTERNS.search(msg):
        return ResponseMode.TASK_REQUEST

    if _DIRECT_FACTUAL_PATTERNS.search(msg):
        return ResponseMode.DIRECT_FACTUAL

    if _EDUCATIONAL_PATTERNS.search(msg):
        return ResponseMode.EDUCATIONAL

    return ResponseMode.CONVERSATIONAL


def process_user_request(
    user_message: str,
    user_facts: UserFacts,
    student_context: StudentContext | None = None,
) -> ProcessedRequest:
    """
    Full semantic and constraint processing for the incoming message.
    """
    msg = user_message.strip()
    constraints = detect_constraints(msg)
    response_mode = detect_response_mode(msg)

    # 1. Check for deterministic fast-path answer
    is_det, det_ans, det_intent = try_resolve_deterministic_answer(
        message=msg,
        user_facts=user_facts,
        constraints=constraints,
        student_context=student_context,
    )

    if is_det and det_ans is not None:
        return ProcessedRequest(
            intent=det_intent or RequestIntent.GENERAL_CONVERSATION,
            workflow_intent=IntentType.GENERAL_SUPPORT,
            response_mode=response_mode,
            constraints=constraints,
            is_deterministic=True,
            deterministic_answer=det_ans,
            confidence=1.0,
            reasoning="Resolved deterministically via fast-path",
        )

    # 2. Map response_mode to workflow RequestIntent and IntentType
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
    elif response_mode == ResponseMode.EMOTIONAL_SUPPORT:
        req_intent = RequestIntent.EMOTIONAL_SUPPORT
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
        reasoning=f"Classified as {req_intent.value} with mode {response_mode.value}",
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
