"""
Deterministic Study Plan Builder & Parser.

Provides reliable construction and validation of structured StudyPlan objects.
Ensures that regardless of LLM availability or JSON parsing hiccups, a realistic,
manageable, and personalized study plan is always produced.
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import date
from typing import Any

from chatbot.backend.schemas.planner import (
    PlanMilestone,
    PlanRequest,
    PriorityLevel,
    StudyPlan,
    StudyTask,
)

logger = logging.getLogger(__name__)

# Days of the week for scheduling
_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def parse_daily_time_limit(goal_text: str | None) -> int:
    """Extracts student daily time limit in minutes if mentioned (e.g. '1 hour per day')."""
    if not goal_text:
        return 60

    lower = goal_text.lower()
    # Match patterns like '1 hour', '2 hours', '30 mins', '45 minutes'
    hour_match = re.search(r"(\d+)\s*(?:hour|hr)", lower)
    if hour_match:
        return min(240, int(hour_match.group(1)) * 60)

    min_match = re.search(r"(\d+)\s*(?:min|minute)", lower)
    if min_match:
        return max(15, min(240, int(min_match.group(1))))

    return 60  # Default 60 minutes


def build_default_plan(request: PlanRequest) -> StudyPlan:
    """
    Generates a personalized, structured StudyPlan deterministically.
    Used as baseline logic and as reliable fallback if LLM is offline.
    """
    ctx = request.student_context
    insight = request.student_insight
    user_goal = request.user_goal or "Weekly Study Schedule"
    daily_limit = parse_daily_time_limit(user_goal)

    # 1. Determine subjects and focus areas
    available_course_names = [s.subject_name for s in ctx.subjects] if ctx.subjects else []
    focus_subjects = []

    if insight and insight.focus_areas:
        for fa in insight.focus_areas:
            # If the focus area matches an enrolled course, prioritize it
            matched_course = next((c for c in available_course_names if c.lower() in fa.lower() or fa.lower() in c.lower()), None)
            if matched_course and matched_course not in focus_subjects:
                focus_subjects.append(matched_course)
            elif not any(keyword in fa.lower() for keyword in ("attendance", "rate", "gpa", "stabilization", "completion")) and fa not in focus_subjects:
                focus_subjects.append(fa)

    # Append any remaining enrolled courses
    for c in available_course_names:
        if c not in focus_subjects:
            focus_subjects.append(c)

    if not focus_subjects:
        focus_subjects = ["General Revision", "Coursework Prep"]

    # 2. Extract upcoming deadlines to prioritize
    urgent_tasks = []
    if ctx.assignments and ctx.assignments.upcoming_deadlines:
        for dl in ctx.assignments.upcoming_deadlines:
            urgent_tasks.append(
                StudyTask(
                    title=f"Complete {dl.get('title', 'Assignment')}",
                    description=f"Finish submission for {dl.get('subject', 'Course')} before deadline ({dl.get('due_date', 'upcoming')}).",
                    subject=dl.get("subject", focus_subjects[0]),
                    day="Monday",
                    time_slot="18:00–19:00",
                    duration_minutes=min(daily_limit, 60),
                    priority=PriorityLevel.HIGH,
                )
            )

    # 3. Schedule daily tasks up to timeframe_days
    tasks: list[StudyTask] = []
    if urgent_tasks:
        tasks.extend(urgent_tasks)

    num_days = min(7, request.timeframe_days)
    for i in range(len(tasks), num_days):
        day_name = _DAYS[i % len(_DAYS)]
        target_subject = focus_subjects[i % len(focus_subjects)]
        is_priority = (insight and target_subject in insight.focus_areas) or i == 0
        priority = PriorityLevel.HIGH if is_priority else PriorityLevel.MEDIUM

        tasks.append(
            StudyTask(
                title=f"{target_subject} Focused Review",
                description=f"Review foundational concepts and solve practice questions in {target_subject}.",
                subject=target_subject,
                day=day_name,
                time_slot=f"{18 + (i % 2)}:00–{19 + (i % 2)}:00",
                duration_minutes=min(daily_limit, 60),
                priority=priority,
            )
        )

    # 4. Create milestones
    milestones = [
        PlanMilestone(
            title=f"Mid-Week Progress Review ({focus_subjects[0]})",
            target_day="Wednesday",
        ),
        PlanMilestone(
            title="Weekly Objectives Check-in",
            target_day="Sunday",
        ),
    ]

    # 5. Compile goals and priorities
    goals = [
        f"Master core concepts in {focus_subjects[0]}",
        "Maintain consistent daily study routine",
    ]
    if request.user_goal:
        goals.insert(0, request.user_goal)

    title = f"Focused Study Plan: {focus_subjects[0]}" if focus_subjects else "Personalized Weekly Study Plan"

    return StudyPlan(
        title=title,
        goals=goals[:3],
        priorities=focus_subjects[:3],
        week_start=date.today().isoformat(),
        tasks=tasks,
        milestones=milestones,
        resources=[f"{s} LMS Notes & Practice Sets" for s in focus_subjects[:2]],
        notes="Consistency is key. Short, focused sessions yield the highest retention!",
        rationale=f"Plan prioritized around {focus_subjects[0]} to build momentum while keeping daily targets at {daily_limit} minutes.",
        metadata={"builder": "deterministic_baseline"},
    )


def parse_llm_plan_json(raw_text: str, request: PlanRequest) -> StudyPlan:
    """Parses and validates LLM completion text into a typed StudyPlan object."""
    clean = raw_text.strip()
    if clean.startswith("```"):
        clean = "\n".join(clean.split("\n")[1:-1])
        if clean.startswith("json"):
            clean = clean[4:].strip()

    try:
        data = json.loads(clean)
        # Ensure task IDs are set
        if "tasks" in data and isinstance(data["tasks"], list):
            for t in data["tasks"]:
                if "task_id" not in t or not t["task_id"]:
                    t["task_id"] = str(uuid.uuid4())
                if "priority" in t and isinstance(t["priority"], str):
                    t["priority"] = t["priority"].lower()
                    if t["priority"] not in ("high", "medium", "low"):
                        t["priority"] = "medium"

        if "milestones" in data and isinstance(data["milestones"], list):
            for m in data["milestones"]:
                if "milestone_id" not in m or not m["milestone_id"]:
                    m["milestone_id"] = str(uuid.uuid4())

        return StudyPlan(**data)
    except Exception as exc:
        logger.warning("StudyPlannerAgent: Failed to parse LLM JSON (%s) — using default plan", exc)
        return build_default_plan(request)
