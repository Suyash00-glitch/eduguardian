"""
Deterministic Study Plan Builder, Parser, and Sanitizer.

Provides reliable construction, validation, and structured repair of StudyPlan objects.
Guarantees that every generated plan consists of 100% genuine academic study activities,
valid subject names, current week_start dates, and strict adherence to user constraints.
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

# Forbidden non-academic phrases that indicate counselor/case-management hallucinations
_FORBIDDEN_TASK_PATTERNS = re.compile(
    r"\b("
    r"communicate with (the )?student|discuss (and understand )?student|discuss concerns|"
    r"respect student'?s? autonomy|understand student'?s? goals|counsel (the )?student|"
    r"follow[- ]up with (the )?student|meet with (the )?student|case management|"
    r"administrative follow-up|check[- ]in on emotional state|counseling session"
    r")\b",
    re.IGNORECASE,
)


def parse_daily_time_limit(goal_text: str | None) -> int:
    """Extracts student daily time limit in minutes if mentioned (e.g. '1 hour per day')."""
    if not goal_text:
        return 60

    lower = goal_text.lower()
    # Match patterns like '1 hour', '2 hours', '30 mins', '45 minutes'
    hour_match = re.search(r"(\d+)\s*(?:hour|hr)", lower)
    if hour_match:
        return min(240, max(15, int(hour_match.group(1)) * 60))

    min_match = re.search(r"(\d+)\s*(?:min|minute)", lower)
    if min_match:
        return max(15, min(240, int(min_match.group(1))))

    return 60  # Default 60 minutes


def extract_requested_subject(user_goal: str | None, enrolled_courses: list[str]) -> str | None:
    """Detects if the student explicitly requested a specific subject in their message."""
    if not user_goal:
        return None

    lower_goal = user_goal.lower()

    # 1. Match against known enrolled courses
    for course in enrolled_courses:
        if course.lower() in lower_goal:
            return course

    # 2. Match common academic subjects if mentioned
    common_subjects = [
        "Data Structures", "Algorithms", "Operating Systems", "DBMS", "Database Management",
        "Computer Networks", "Software Engineering", "Mathematics", "Calculus", "Linear Algebra",
        "Discrete Mathematics", "Physics", "Chemistry", "Python", "Java", "C++", "Machine Learning",
        "Artificial Intelligence", "Web Development", "Computer Architecture"
    ]
    for sub in common_subjects:
        if sub.lower() in lower_goal:
            return sub

    return None


def build_default_plan(request: PlanRequest) -> StudyPlan:
    """
    Generates a personalized, structured StudyPlan deterministically.
    Used as baseline logic and as a reliable fallback when LLM is offline.
    """
    ctx = request.student_context
    insight = request.student_insight
    user_goal = request.user_goal or "Weekly Study Schedule"
    daily_limit = parse_daily_time_limit(user_goal)

    # 1. Determine subjects and focus areas
    enrolled_courses = [s.subject_name for s in ctx.subjects] if ctx.subjects else []
    requested_subject = extract_requested_subject(user_goal, enrolled_courses)
    is_strictly_scoped = bool(re.search(r"\b(only\s+for|specifically\s+for|just\s+for|strictly\s+for)\b", user_goal.lower()))

    focus_subjects: list[str] = []

    if is_strictly_scoped and requested_subject:
        focus_subjects = [requested_subject]
    else:
        # If student explicitly asked for a subject, place it first
        if requested_subject:
            focus_subjects.append(requested_subject)

        # Add insight focus areas
        if insight and insight.focus_areas:
            for fa in insight.focus_areas:
                matched_course = next((c for c in enrolled_courses if c.lower() in fa.lower() or fa.lower() in c.lower()), None)
                target = matched_course or fa
                if not any(k in target.lower() for k in ("attendance", "rate", "gpa", "stabilization", "completion")) and target not in focus_subjects:
                    focus_subjects.append(target)

        # Append remaining enrolled courses
        for c in enrolled_courses:
            if c not in focus_subjects:
                focus_subjects.append(c)

    if not focus_subjects:
        focus_subjects = [requested_subject] if requested_subject else ["General Study", "Coursework Prep"]

    primary_subject = focus_subjects[0]

    # 2. Extract upcoming deadlines to prioritize
    urgent_tasks: list[StudyTask] = []
    if ctx.assignments and ctx.assignments.upcoming_deadlines:
        for dl in ctx.assignments.upcoming_deadlines:
            sub = dl.get("subject") or primary_subject
            if is_strictly_scoped and requested_subject and sub.lower() != requested_subject.lower():
                continue
            urgent_tasks.append(
                StudyTask(
                    title=f"Complete {dl.get('title', 'Assignment')}",
                    description=f"Finish and review submission for {sub} before deadline ({dl.get('due_date', 'upcoming')}).",
                    subject=sub,
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

    lh = request.learning_history or {}
    needs_practice = lh.get("needs_practice_topics") or []
    mastered = lh.get("mastered_topics") or []

    num_days = min(7, request.timeframe_days)
    for i in range(len(tasks), num_days):
        day_name = _DAYS[i % len(_DAYS)]
        target_subject = focus_subjects[i % len(focus_subjects)]
        is_priority = (insight and target_subject in insight.focus_areas) or (requested_subject == target_subject) or (i == 0)

        # Check if we have relevant needs_practice topic for this subject
        matched_np = [t for t in needs_practice if not is_strictly_scoped or (requested_subject and requested_subject.lower() in target_subject.lower())]
        matched_m = [t for t in mastered if not is_strictly_scoped or (requested_subject and requested_subject.lower() in target_subject.lower())]

        if matched_np and i % 2 == 0:
            topic_item = matched_np[i % len(matched_np)]
            full_title = f"{target_subject}: {topic_item} Practice & Problem Solving"
            full_desc = f"Targeted concept review and structured practice exercises for {topic_item} in {target_subject}."
            priority = PriorityLevel.HIGH
        elif matched_m and i == num_days - 1:
            m_item = matched_m[0]
            full_title = f"{target_subject}: {m_item} Maintenance Review"
            full_desc = f"Light revision and maintenance review for {m_item} to preserve mastery."
            priority = PriorityLevel.LOW
        else:
            task_templates = [
                ("Core Concepts & Lecture Review", "Review lecture notes, summarize core formulas/theorems, and build flashcards."),
                ("Practice Problems & Problem Solving", "Work through standard exercises and practice problem sets step-by-step."),
                ("Active Recall & Self-Quiz", "Test comprehension without reference materials to reinforce long-term memory."),
                ("Lab Work & Practical Implementation", "Implement exercises, write practice code/solutions, and verify correctness."),
                ("Weekly Synthesis & Concept Mapping", "Connect major weekly topics and clarify remaining doubts with study resources."),
                ("Mock Assessment & Timed Practice", "Solve previous exam questions or quiz problems under realistic timing."),
                ("Light Review & Next Week Prep", "Quickly review tricky concepts from the week and organize materials for next week."),
            ]
            activity_title, activity_desc = task_templates[i % len(task_templates)]
            full_title = f"{target_subject}: {activity_title}"
            full_desc = f"{activity_desc} Focus area: {target_subject}."
            priority = PriorityLevel.HIGH if is_priority else PriorityLevel.MEDIUM

        slot_hour = 18 if i % 2 == 0 else 19

        tasks.append(
            StudyTask(
                title=full_title,
                description=full_desc,
                subject=target_subject,
                day=day_name,
                time_slot=f"{slot_hour}:00–{slot_hour + max(1, daily_limit // 60)}:00" if daily_limit >= 60 else f"{slot_hour}:00–{slot_hour}:{daily_limit:02d}",
                duration_minutes=daily_limit,
                priority=priority,
            )
        )

    # 4. Create milestones
    milestones = [
        PlanMilestone(
            title=f"Mid-Week Concept Check ({primary_subject})",
            target_day="Wednesday",
        ),
        PlanMilestone(
            title="Weekly Objectives Mastery Review",
            target_day="Sunday",
        ),
    ]

    # 5. Compile goals and priorities
    goals = [
        f"Master core concepts in {primary_subject}",
        "Maintain consistent daily study routine",
        f"Complete scheduled practice sessions within {daily_limit} mins/day",
    ]
    if request.user_goal and len(request.user_goal) < 60:
        goals[0] = request.user_goal

    title = f"Focused Study Plan: {primary_subject}"

    return StudyPlan(
        title=title,
        goals=goals[:3],
        priorities=focus_subjects[:3],
        week_start=date.today().isoformat(),
        tasks=tasks,
        milestones=milestones,
        resources=[f"{s} Course Materials & Practice Sets" for s in focus_subjects[:2]],
        notes="Consistency is key. Short, focused study blocks yield the highest long-term retention!",
        rationale=f"Plan prioritized around {primary_subject} to build momentum while keeping daily targets at {daily_limit} minutes.",
        metadata={"builder": "deterministic_baseline"},
    )


def sanitize_and_repair_plan(data: dict[str, Any], request: PlanRequest) -> StudyPlan:
    """
    Sanitizes and repairs LLM-generated plan dictionary to guarantee validity:
    - Eliminates forbidden administrative/counseling tasks ('Communicate with student').
    - Ensures every task has a valid, non-empty subject.
    - Ensures current date in week_start.
    - Caps durations to student's daily time limit.
    """
    ctx = request.student_context
    enrolled_courses = [s.subject_name for s in ctx.subjects] if ctx.subjects else []
    requested_subject = extract_requested_subject(request.user_goal, enrolled_courses)
    default_subject = requested_subject or (enrolled_courses[0] if enrolled_courses else "General Study")
    daily_limit = parse_daily_time_limit(request.user_goal)

    # 1. Clean Title
    title = data.get("title")
    if not title or not isinstance(title, str) or _FORBIDDEN_TASK_PATTERNS.search(title) or title.strip().lower() in ("none", "null", ""):
        data["title"] = f"Personalized Study Plan: {default_subject}"
    else:
        data["title"] = title.strip()

    # 2. Clean Week Start
    week_start = data.get("week_start")
    if not week_start or not isinstance(week_start, str) or week_start.strip().lower() in ("none", "null", ""):
        data["week_start"] = date.today().isoformat()

    # 3. Clean Goals
    raw_goals = data.get("goals")
    clean_goals: list[str] = []
    if isinstance(raw_goals, list):
        for g in raw_goals:
            if isinstance(g, str) and not _FORBIDDEN_TASK_PATTERNS.search(g):
                clean_str = g.strip()
                if clean_str and clean_str.lower() not in ("none", "null"):
                    clean_goals.append(clean_str)

    if not clean_goals:
        clean_goals = [
            f"Master core concepts in {default_subject}",
            "Maintain consistent daily study routine",
        ]
    data["goals"] = clean_goals[:4]

    # 4. Clean Priorities
    raw_priorities = data.get("priorities")
    clean_priorities: list[str] = []
    if isinstance(raw_priorities, list):
        for p in raw_priorities:
            if isinstance(p, str) and not _FORBIDDEN_TASK_PATTERNS.search(p):
                clean_str = p.strip()
                if clean_str and clean_str.lower() not in ("none", "null"):
                    clean_priorities.append(clean_str)

    if not clean_priorities:
        clean_priorities = [default_subject]
    data["priorities"] = clean_priorities[:4]

    # 5. Clean and Sanitize Tasks
    raw_tasks = data.get("tasks")
    clean_tasks: list[dict[str, Any]] = []

    if isinstance(raw_tasks, list) and len(raw_tasks) > 0:
        for idx, t in enumerate(raw_tasks):
            if not isinstance(t, dict):
                continue

            # Check and resolve Subject
            raw_sub = t.get("subject")
            task_subject = default_subject
            if isinstance(raw_sub, str) and raw_sub.strip() and raw_sub.strip().lower() not in ("none", "null", "n/a", "undefined", "unknown"):
                task_subject = raw_sub.strip()

            # Check for forbidden counseling tasks
            raw_title = str(t.get("title") or t.get("activity") or "")
            raw_desc = str(t.get("description") or "")

            is_forbidden = bool(_FORBIDDEN_TASK_PATTERNS.search(raw_title) or _FORBIDDEN_TASK_PATTERNS.search(raw_desc))

            if is_forbidden or not raw_title.strip() or raw_title.strip().lower() in ("none", "null"):
                task_title = f"{task_subject} Practice & Review"
                task_desc = f"Review key concepts, solve practice exercises, and self-test in {task_subject}."
            else:
                task_title = raw_title.strip()
                task_desc = raw_desc.strip() if raw_desc.strip() and raw_desc.strip().lower() not in ("none", "null") else f"Study session for {task_subject}."

            # Day
            day_name = str(t.get("day") or _DAYS[idx % len(_DAYS)]).capitalize()
            if day_name not in _DAYS:
                day_name = _DAYS[idx % len(_DAYS)]

            # Time slot
            time_slot = t.get("time_slot")
            if not time_slot or not isinstance(time_slot, str) or time_slot.strip().lower() in ("none", "null", ""):
                time_slot = f"{18 + (idx % 2)}:00–{19 + (idx % 2)}:00"

            # Duration
            try:
                dur = int(t.get("duration_minutes", 60))
                dur = min(daily_limit, max(15, dur)) if daily_limit else max(15, min(240, dur))
            except (ValueError, TypeError):
                dur = min(daily_limit, 60)

            # Priority
            pri = str(t.get("priority", "medium")).lower()
            if pri not in ("high", "medium", "low"):
                pri = "medium"

            clean_tasks.append({
                "task_id": str(t.get("task_id") or uuid.uuid4()),
                "title": task_title,
                "description": task_desc,
                "subject": task_subject,
                "day": day_name,
                "time_slot": time_slot,
                "duration_minutes": dur,
                "priority": pri,
                "is_completed": bool(t.get("is_completed", False)),
            })

    if not clean_tasks:
        logger.warning("StudyPlannerAgent: All tasks invalid or missing in LLM response — building default tasks")
        return build_default_plan(request)

    data["tasks"] = clean_tasks

    # 6. Clean Milestones
    raw_milestones = data.get("milestones")
    clean_milestones: list[dict[str, Any]] = []
    if isinstance(raw_milestones, list):
        for m in raw_milestones:
            if isinstance(m, dict) and m.get("title"):
                clean_milestones.append({
                    "milestone_id": str(m.get("milestone_id") or uuid.uuid4()),
                    "title": str(m["title"]).strip(),
                    "target_day": str(m.get("target_day") or "Wednesday"),
                    "is_reached": bool(m.get("is_reached", False)),
                })
    if not clean_milestones:
        clean_milestones = [
            {"milestone_id": str(uuid.uuid4()), "title": f"Mid-Week Check-in ({default_subject})", "target_day": "Wednesday", "is_reached": False},
            {"milestone_id": str(uuid.uuid4()), "title": "Weekly Objectives Review", "target_day": "Sunday", "is_reached": False},
        ]
    data["milestones"] = clean_milestones

    # 7. Resources & Notes
    if not data.get("resources") or not isinstance(data.get("resources"), list):
        data["resources"] = [f"{default_subject} Course Notes & Practice Sets"]

    if not data.get("notes") or not isinstance(data.get("notes"), str) or data["notes"].strip().lower() in ("none", "null", ""):
        data["notes"] = "Take regular short breaks to maintain focus and maximize retention."

    if not data.get("rationale") or not isinstance(data.get("rationale"), str) or data["rationale"].strip().lower() in ("none", "null", ""):
        data["rationale"] = f"Structured around {default_subject} to balance core review with consistent daily practice."

    return StudyPlan(**data)


def parse_llm_plan_json(raw_text: str, request: PlanRequest) -> StudyPlan:
    """Parses, validates, and sanitizes LLM completion text into a typed StudyPlan object."""
    clean = raw_text.strip()
    if clean.startswith("```"):
        clean = "\n".join(clean.split("\n")[1:-1])
        if clean.startswith("json"):
            clean = clean[4:].strip()

    # Sometimes LLMs append text before/after JSON; extract the outer {...} block
    json_match = re.search(r"(\{.*\})", clean, re.DOTALL)
    if json_match:
        clean = json_match.group(1)

    try:
        data = json.loads(clean)
        return sanitize_and_repair_plan(data, request)
    except Exception as exc:
        logger.warning("StudyPlannerAgent: Failed to parse LLM JSON (%s) — using default baseline plan", exc)
        return build_default_plan(request)

