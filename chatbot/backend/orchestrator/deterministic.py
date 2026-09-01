"""
Deterministic Fast-Path Resolver for EduGuardian AI.

Provides instant, 0ms-latency, non-hallucinating deterministic answers
for simple factual, identity, arithmetic, and direct profile queries.
"""
from __future__ import annotations

import re
from typing import Any

from chatbot.backend.schemas.student import StudentContext
from chatbot.backend.schemas.routing import ResponseConstraints, RequestIntent
from chatbot.backend.core.memory import (
    UserFacts,
    is_name_query,
    is_hometown_query,
    is_ai_origin_query,
    is_interest_query,
    is_system_architecture_query,
    is_existential_user_query,
    is_clarification_user_query,
)


def try_resolve_deterministic_answer(
    message: str,
    user_facts: UserFacts,
    constraints: ResponseConstraints,
    student_context: StudentContext | None = None,
) -> tuple[bool, str | None, RequestIntent | None]:
    """
    Attempts to produce a deterministic answer for trivial/direct questions.

    Returns:
        (is_deterministic, answer_text, request_intent)
    """
    msg_clean = message.lower().strip().rstrip("?.!")
    resolved_name = (
        user_facts.name
        or (student_context.student_name if student_context else "")
        or (student_context.full_name if student_context else "")
        or ""
    ).strip()

    # 1. System Architecture / Available Agents Query
    if is_system_architecture_query(message):
        system_agents_text = (
            "You currently have three agents:\n"
            "1. Student Insight Agent — Analyzes academic performance and focus areas internally.\n"
            "2. Study Planner Agent — Generates structured, actionable weekly study schedules.\n"
            "3. Recovery Coach Agent — Delivers supportive, personalized conversational coaching."
        )
        return True, system_agents_text, RequestIntent.SYSTEM_ARCHITECTURE

    # 2. Direct Attendance Inquiry ("what is my attendance", "what is my attendence", "my attendance")
    if any(w in msg_clean for w in ["attendance", "attendence"]) and any(kw in msg_clean for kw in ["what", "my", "percentage", "rate", "status", "how much", "classes"]):
        if student_context and student_context.attendance and student_context.attendance.overall_percentage is not None:
            pct = student_context.attendance.overall_percentage
            if constraints.one_word or "in 1 word" in msg_clean or "one word" in msg_clean:
                return True, f"{pct:.1f}%.", RequestIntent.ACADEMIC_INSIGHT
            return True, f"Your current attendance is {pct:.1f}%.", RequestIntent.ACADEMIC_INSIGHT
        return True, "I don't have your attendance records available right now.", RequestIntent.ACADEMIC_INSIGHT

    # 3. Direct CGPA / SGPA Inquiry ("what is my cgpa", "my cgpa", "what is my sgpa", "my latest sgpa")
    if any(kw in msg_clean for kw in ["cgpa", "sgpa", "gpa"]) and any(kw in msg_clean for kw in ["what", "my", "tell", "current", "latest"]):
        hist = student_context.historical_academic_performance if student_context else None
        if hist and (hist.get("cgpa") is not None or hist.get("latest_sgpa") is not None):
            cgpa = hist.get("cgpa")
            sgpa = hist.get("latest_sgpa")
            sem = hist.get("total_semesters_completed") or 4
            trend = hist.get("sgpa_trend") or "stable"
            if "sgpa" in msg_clean and "cgpa" not in msg_clean and sgpa is not None:
                return True, f"Your latest SGPA is {sgpa} (Semester {sem}).", RequestIntent.ACADEMIC_INSIGHT
            if cgpa is not None and sgpa is not None:
                return True, f"Your current CGPA is {cgpa}. Your latest SGPA is {sgpa} from Semester {sem}, and your academic trajectory is {trend}.", RequestIntent.ACADEMIC_INSIGHT
            if cgpa is not None:
                return True, f"Your current CGPA is {cgpa}.", RequestIntent.ACADEMIC_INSIGHT
        return True, "I don't have your CGPA records available right now.", RequestIntent.ACADEMIC_INSIGHT

    # 4. Compound Question: Operating System + Tell me my name
    if "operating system" in msg_clean and "name" in msg_clean:
        os_def = "An operating system is system software that manages computer hardware, software resources, and provides common services for computer programs."
        if resolved_name:
            name_phrase = f"Your name is {resolved_name}."
            if constraints.one_word:
                return True, f"{resolved_name}.", RequestIntent.IDENTITY
        else:
            name_phrase = "I don't have your name saved yet."
            if constraints.one_word:
                return True, "Unknown.", RequestIntent.IDENTITY
        return True, f"{name_phrase} {os_def}", RequestIntent.EDUCATIONAL

    # 5. Combined Name + Interest / Study Topic Query (e.g. "Tell me my name and what I like to study in one sentence.")
    if "name" in msg_clean and any(k in msg_clean for k in ["study", "favorite", "like", "interest"]):
        fav_topic = user_facts.interests[0] if user_facts.interests else "your studies"
        if resolved_name:
            return True, f"Your name is {resolved_name}, and you like studying {fav_topic}.", RequestIntent.IDENTITY
        else:
            return True, f"I don't have your name saved yet, and you like studying {fav_topic}.", RequestIntent.IDENTITY

    # 6. Identity & Name Questions
    if is_name_query(message):
        if not resolved_name:
            if constraints.one_word:
                return True, "Unknown.", RequestIntent.IDENTITY
            return True, "I don't have your name saved yet.", RequestIntent.IDENTITY

        # Identity corrections
        if any(k in msg_clean for k in ["u dint say", "you didnt say", "you didn't say"]):
            return True, f"You're right — your name is {resolved_name}.", RequestIntent.IDENTITY
        if any(k in msg_clean for k in ["but i said", "i said my name", "i told you my name"]):
            return True, f"Yes, you said your name is {resolved_name}.", RequestIntent.IDENTITY

        if constraints.one_word or "in 1 word" in msg_clean or "one word" in msg_clean:
            return True, f"{resolved_name}.", RequestIntent.IDENTITY
        if constraints.one_sentence or "in 1 line" in msg_clean or "in 1 sentence" in msg_clean or "one sentence" in msg_clean:
            return True, f"Your name is {resolved_name}.", RequestIntent.IDENTITY

        return True, f"{resolved_name}.", RequestIntent.IDENTITY

    # 7. Interest & Study Topic Questions ("What do I like to study?", "What is my favorite topic?")
    if is_interest_query(message):
        if user_facts.interests:
            fav_topic = user_facts.interests[0]
            if constraints.one_word:
                return True, f"{fav_topic}.", RequestIntent.IDENTITY
            if constraints.one_sentence:
                return True, f"You like studying {fav_topic}.", RequestIntent.IDENTITY
            return True, f"{fav_topic}.", RequestIntent.IDENTITY
        else:
            return True, "I don't have your favorite study topics saved yet.", RequestIntent.IDENTITY

    # 8. Hometown / Origin Queries ("Where am I from?", "Where i am from")
    if is_hometown_query(message):
        if user_facts.hometown:
            if constraints.one_word:
                return True, f"{user_facts.hometown}.", RequestIntent.USER_PROFILE
            if constraints.one_sentence:
                return True, f"You're from {user_facts.hometown}.", RequestIntent.USER_PROFILE
            return True, f"You're from {user_facts.hometown}.", RequestIntent.USER_PROFILE
        else:
            return True, "I don't have your hometown information yet.", RequestIntent.USER_PROFILE

    # 9. AI Origin Query ("Where are you from?")
    if is_ai_origin_query(message):
        return True, "I am EduGuardian, an AI academic assistant built to support university students.", RequestIntent.GENERAL_CONVERSATION

    # 10. Direct World Facts & Simple Math
    if "capital of india" in msg_clean:
        return True, "New Delhi.", RequestIntent.FACTUAL

    if msg_clean in ["2 + 2", "2+2", "what is 2 + 2", "what is 2+2", "2 plus 2"]:
        return True, "4.", RequestIntent.FACTUAL

    # 11. Pure Educational Concepts
    if msg_clean in ["what is operating system", "what is an operating system", "what is os", "define operating system"]:
        return True, "An operating system is system software that manages computer hardware, software resources, and provides common services for computer programs.", RequestIntent.EDUCATIONAL

    # 12. Simple Greeting (with or without name intro)
    is_greeting_only = bool(re.match(r"^(?:hi|hii+|hello|hey|good\s+(?:morning|afternoon|evening|day))(?:\s*,\s*|\s+)?(?:(?:my\s+name\s+is|i\s+am|i'm)\s+\w+)?$", msg_clean)) or bool(re.match(r"^(?:my\s+name\s+is\s+\w+|i\s+am\s+[a-zA-Z]+)$", msg_clean))
    if is_greeting_only and not message.endswith("?"):
        target_name = resolved_name
        if target_name:
            return True, f"Hi {target_name}! How can I help?", RequestIntent.GREETING
        return True, "Hi! How can I help?", RequestIntent.GREETING

    # 14. Gratitude / Closure
    if msg_clean in ["thanks", "thank you", "thanks a lot", "thank you so much", "thx"]:
        return True, "You're welcome! Let me know if you need anything else.", RequestIntent.GENERAL_CONVERSATION

    if msg_clean in ["bye", "goodbye", "see you", "cya"]:
        return True, "Goodbye! Best of luck with your studies.", RequestIntent.GENERAL_CONVERSATION

    return False, None, None


    return False, None, None
