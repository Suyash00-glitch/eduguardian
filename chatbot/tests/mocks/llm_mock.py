"""
Test Double: MockLLMClient for offline automated testing.

This file lives exclusively in tests/ and is never imported or used by production runtime.
"""
from __future__ import annotations

import json
from chatbot.backend.llm.base import BaseLLMClient, LLMMessage, LLMResponse

_CANNED_RESPONSES: list[tuple[list[str], str]] = [
    (
        ["stress", "anxious", "overwhelmed", "struggling", "worried", "scared"],
        (
            "I hear you — feeling overwhelmed is completely normal, especially "
            "when assignments and classes pile up. You're taking the right step "
            "by reaching out. Let's break things down into small, manageable wins together. "
            "What's one thing we can tackle first today?"
        ),
    ),
    (
        ["study plan", "schedule", "plan for", "plan my", "organize", "timetable"],
        (
            "I've put together a personalized study plan for you! 🎯 "
            "We've focused on giving extra attention to your core subjects "
            "while keeping study sessions balanced and achievable. "
            "Click on 'View Your Study Plan' to see your weekly schedule."
        ),
    ),
    (
        ["attendance", "missed class", "absent", "skipped"],
        (
            "I noticed you've had a few gaps in attendance lately — that's completely okay, "
            "it happens. The key now is to catch up on what you missed step-by-step "
            "and build a steady routine. Would you like me to help you map out the priority topics?"
        ),
    ),
    (
        ["exam", "test", "quiz", "assessment", "marks", "grades", "how am i doing", "progress"],
        (
            "You're making steady progress! Your strengths in core topics are a great foundation. "
            "With a little extra targeted practice in your focus subjects, you'll feel much more confident. "
            "Would you like to build a quick revision schedule?"
        ),
    ),
    (
        ["hello", "hi", "hey", "good morning", "good evening"],
        (
            "Hey there! Great to see you. I'm here to help you stay on track, "
            "organize your schedule, and reach your goals. What would you like to work on today?"
        ),
    ),
]

_DEFAULT_RESPONSE = (
    "I'm here to support your academic journey! "
    "Whether you need help organizing your study time, catching up on classes, "
    "or just figuring out what to tackle next — let me know what you'd like to focus on."
)

_MOCK_INSIGHT_JSON = json.dumps({
    "student_id": "student_001",
    "support_intensity": "standard",
    "has_concerning_patterns": False,
    "confidence_score": 0.85,
    "strengths": ["Consistent attendance in Operating Systems", "High assignment completion"],
    "priority_focus_areas": ["Data Structures recursion"],
    "risk_factors": ["Recent dip in quiz scores"],
    "positive_signals": ["Active participation on forums"],
    "recommended_interventions": ["Provide 2x weekly focused practice"],
})

def _get_mock_plan_json(topic: str = "General") -> str:
    return json.dumps({
        "title": f"Focused Study Plan: {topic}",
        "week_start": "2026-08-15",
        "goals": [
            f"Build strong fundamentals in {topic}",
            "Complete all pending assignments",
            "Maintain balanced study routine",
        ],
        "tasks": [
            {
                "title": f"{topic} Core Concepts",
                "day": "Monday",
                "time_slot": "10:00–11:30",
                "subject": topic,
                "description": f"Review foundational lecture notes for {topic}",
                "duration_minutes": 90,
                "priority": "high",
            },
            {
                "title": f"{topic} Problem Practice",
                "day": "Tuesday",
                "time_slot": "14:00–15:00",
                "subject": topic,
                "description": "Solve 3 practice problems",
                "duration_minutes": 60,
                "priority": "high",
            },
            {
                "title": "Assignment Completion",
                "day": "Wednesday",
                "time_slot": "10:00–11:00",
                "subject": topic,
                "description": "Work on weekly problem set",
                "duration_minutes": 60,
                "priority": "medium",
            },
            {
                "title": "Revision & Self-Quiz",
                "day": "Thursday",
                "time_slot": "16:00–17:00",
                "subject": topic,
                "description": "Review missed concepts from earlier sessions",
                "duration_minutes": 60,
                "priority": "medium",
            },
            {
                "title": "Light Review & Rest",
                "day": "Friday",
                "time_slot": "11:00–12:00",
                "subject": topic,
                "description": "Quick flashcard review, then rest for the weekend",
                "duration_minutes": 60,
                "priority": "low",
            },
        ],
        "resources": [
            f"Lecture slides: {topic} Ch. 3–5",
            "EduGuardian Practice Question Bank",
            "Course Discussion Forum",
        ],
        "notes": (
            "Remember: consistency beats intensity! Take regular 10-minute breaks "
            "and reach out whenever you feel stuck."
        ),
    })


class MockLLMClient(BaseLLMClient):
    """Offline test double for BaseLLMClient used exclusively in unit tests."""

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        system_content = next((m.content for m in messages if m.role == "system"), "")
        user_content = next((m.content for m in messages if m.role == "user"), "")
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "").lower()

        # Structured JSON responses for specialist agents
        if "student insight" in system_content.lower() or "student_insight" in system_content.lower():
            return LLMResponse(
                content=f"```json\n{_MOCK_INSIGHT_JSON}\n```",
                model="mock-gemini-test",
                usage={"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
            )

        if "study planner" in system_content.lower() or "study_planner" in system_content.lower():
            topic = "Data Structures" if "data structure" in user_content.lower() else "General Studies"
            return LLMResponse(
                content=f"```json\n{_get_mock_plan_json(topic)}\n```",
                model="mock-gemini-test",
                usage={"prompt_tokens": 60, "completion_tokens": 200, "total_tokens": 260},
            )

        # Keyword match for Recovery Coach tests
        for keywords, canned in _CANNED_RESPONSES:
            if any(kw in last_user for kw in keywords):
                return LLMResponse(
                    content=canned,
                    model="mock-gemini-test",
                    usage={"prompt_tokens": 40, "completion_tokens": 80, "total_tokens": 120},
                )

        return LLMResponse(
            content=_DEFAULT_RESPONSE,
            model="mock-gemini-test",
            usage={"prompt_tokens": 30, "completion_tokens": 60, "total_tokens": 90},
        )
