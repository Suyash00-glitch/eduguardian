"""
Intent, Constraint & Routing Contracts for EduGuardian AI.

Defines the typed intent representation, fine-grained response modes,
and structured response constraints used by the LangGraph orchestrator
to decide workflow paths and post-processing validation.
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """
    Primary LangGraph workflow routing intents:
    - GENERAL_SUPPORT: Conversational greetings, identity, direct answers, educational (Recovery Coach only)
    - ACADEMIC_INSIGHT: Grade questions, attendance, subject performance (Insight -> Coach)
    - STUDY_PLANNING: Timetable creation, study plan requests (Insight -> Planner -> Coach)
    """
    GENERAL_SUPPORT = "general_support"
    ACADEMIC_INSIGHT = "academic_insight"
    STUDY_PLANNING = "study_planning"


class RequestIntent(str, Enum):
    """Fine-grained semantic category of user request (12 Intent Taxonomy)."""
    GREETING = "greeting"
    IDENTITY = "identity"
    USER_PROFILE = "user_profile"
    SYSTEM_ARCHITECTURE = "system_architecture"
    FACTUAL = "factual"
    EDUCATIONAL = "educational"
    RESOURCE_REQUEST = "resource_request"
    ACADEMIC_INSIGHT = "academic_insight"
    STUDY_PLAN = "study_plan"
    EMOTIONAL_SUPPORT = "emotional_support"
    GENERAL_CONVERSATION = "general_conversation"
    CLARIFICATION = "clarification"


class ResponseMode(str, Enum):
    """
    Fine-grained response behavior mode — set by the classifier and consumed by Recovery Coach.

    Controls how the Recovery Coach formats and constrains its response.
    """
    DIRECT_FACTUAL = "direct_factual"          # "capital of India", "2+2"
    IDENTITY = "identity"                      # "who am I", "what's my name"
    USER_PROFILE = "user_profile"              # "where am I from", "my hometown"
    SYSTEM_ARCHITECTURE = "system_architecture"# "which agents do I have", "available agents"
    FORMAT_CONSTRAINED = "format_constrained"  # "in 1 word", "in 1 line", "no extra text"
    EDUCATIONAL = "educational"                # "explain X", "how does X work", "what is X"
    TASK_REQUEST = "task_request"              # "give me a plan", "I want to learn X"
    RESOURCE_REQUEST = "resource_request"      # "give me links", "youtube videos"
    ACADEMIC_INSIGHT = "academic_insight"      # "my grades", "how am I doing", "attendance"
    STUDY_PLAN = "study_plan"                 # "create a study plan", "make me a schedule"
    EMOTIONAL_SUPPORT = "emotional_support"    # "I feel stressed", "depressed about studies"
    CLARIFICATION = "clarification"            # "why am I here", "I asked why I am here"
    CONVERSATIONAL = "conversational"          # greetings, thanks, small talk



class ResponseConstraints(BaseModel):
    """Explicit format and length constraints parsed from user prompt."""
    one_word: bool = False
    one_sentence: bool = False
    short_answer: bool = False
    exact_items: int | None = None
    links_only: bool = False
    no_extra_text: bool = False
    direct_answer: bool = False
    yes_no: bool = False
    max_words: int | None = None
    max_sentences: int | None = None


class ProcessedRequest(BaseModel):
    """Complete analyzed representation of the user request."""
    intent: RequestIntent = RequestIntent.GENERAL_CONVERSATION
    workflow_intent: IntentType = IntentType.GENERAL_SUPPORT
    response_mode: ResponseMode = ResponseMode.CONVERSATIONAL
    constraints: ResponseConstraints = Field(default_factory=ResponseConstraints)
    is_deterministic: bool = False
    deterministic_answer: str | None = None
    confidence: float = 1.0
    reasoning: str | None = None


class IntentClassification(BaseModel):
    """Result of router intent classification."""
    intent: IntentType = Field(description="Detected workflow category")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Classification confidence")
    reasoning: str | None = Field(default=None, description="Keywords or rules matching this intent")
    response_mode: ResponseMode | None = Field(
        default=None,
        description="Fine-grained response behavior mode for the Recovery Coach",
    )
    constraints: ResponseConstraints | None = Field(
        default=None,
        description="Parsed explicit format constraints",
    )
