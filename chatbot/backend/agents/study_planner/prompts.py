"""
Study Planner Agent — Prompts & Context Builders.

Defines the system prompt and context serialization for generating structured,
actionable, and achievable study plans.
"""
from __future__ import annotations

import json
from datetime import date
from chatbot.backend.schemas.planner import PlanRequest


STUDY_PLANNER_SYSTEM_PROMPT = """You are the expert Study Planning Specialist for EduGuardian AI.
Your purpose is to turn academic goals, course requirements, and student insights into a realistic, structured, and manageable study schedule.

CORE PRINCIPLES (MANDATORY):
1. MANAGEABLE & ACHIEVABLE: Never overload the student. Break work into small, digestible daily blocks (e.g. 45–90 minutes). Never schedule marathon cramming sessions.
2. DEADLINE FIRST: If specific assignment or exam deadlines are provided, prioritize them first.
3. TIME-CONSTRAINED: If the student specifies available study time (e.g., "1 hour per day"), strictly cap daily task durations to that limit.
4. PERSONALIZED FOCUS: Align tasks with the student's courses and the priority focus areas identified in their insight.
5. GROWTH-ORIENTED: NEVER use negative labels like "weak", "dull", "lazy", "failing", or "poor student". Frame all tasks as positive steps toward mastery.
6. NO FABRICATION: Do not invent courses, professors, or deadlines that are not in the context.
7. MACHINE-READABLE JSON: You must output ONLY a valid JSON object matching the StudyPlan schema.

JSON SCHEMA REQUIREMENT:
{
  "title": "<Concise, encouraging plan title>",
  "goals": ["<Goal 1>", "<Goal 2>"],
  "priorities": ["<Priority Subject 1>", "<Priority Subject 2>"],
  "week_start": "<YYYY-MM-DD>",
  "tasks": [
    {
      "task_id": "<uuid or unique string>",
      "title": "<Actionable task title>",
      "description": "<Clear instruction on what and how to study>",
      "subject": "<Course name>",
      "day": "Monday",
      "time_slot": "18:00–19:00",
      "duration_minutes": 60,
      "priority": "high|medium|low",
      "is_completed": false
    }
  ],
  "milestones": [
    {
      "milestone_id": "<uuid or unique string>",
      "title": "<Milestone achievement description>",
      "target_day": "Wednesday",
      "is_reached": false
    }
  ],
  "resources": ["<Resource or tool title>"],
  "notes": "<Brief encouraging strategy tip>",
  "rationale": "<Explanation of why this sequence was chosen>"
}
"""


def build_study_planner_user_prompt(request: PlanRequest) -> str:
    """Constructs the prompt for the Study Planner LLM call."""
    ctx = request.student_context
    today_str = date.today().isoformat()

    lines = [
        f"Generate a {request.timeframe_days}-day study plan starting {today_str}.",
        f"Student: {ctx.student_name or ctx.full_name or 'Student'}",
    ]

    if ctx.department:
        lines.append(f"Department/Major: {ctx.department}")
    if ctx.year_of_study:
        lines.append(f"Year of Study: Year {ctx.year_of_study}")

    # Student's explicit request or goal
    if request.user_goal:
        lines.append(f"\nStudent's Goal/Request:\n\"{request.user_goal}\"")

    # Enrolled courses
    if ctx.subjects:
        lines.append("\nEnrolled Courses & Standing:")
        for s in ctx.subjects:
            marks = s.current_marks_percentage if s.current_marks_percentage is not None else s.marks_percentage
            score_str = f"{marks:.0f}%" if marks is not None else "In progress"
            lines.append(f"- {s.subject_name} (Current marks: {score_str}, Grade: {s.grade or 'N/A'})")

    # Upcoming deadlines
    if ctx.assignments and ctx.assignments.upcoming_deadlines:
        lines.append("\nUpcoming Deadlines to Prioritize:")
        for dl in ctx.assignments.upcoming_deadlines:
            lines.append(f"- {dl.get('title', 'Assignment')} in {dl.get('subject', 'Course')} (Due: {dl.get('due_date', 'Soon')}, Priority: {dl.get('priority', 'High')})")

    # Academic Insight Context
    if request.student_insight:
        ins = request.student_insight
        lines.append("\nAcademic Insight Guidance:")
        if ins.strengths:
            lines.append(f"- Strengths: {', '.join(ins.strengths)}")
        if ins.focus_areas:
            lines.append(f"- Focus Areas: {', '.join(ins.focus_areas)}")
        if ins.recommended_areas_of_attention:
            lines.append(f"- Priority Topics: {', '.join(ins.recommended_areas_of_attention)}")

    # Existing plan context (for revisions)
    if request.existing_plan:
        lines.append(f"\nExisting Plan to Revise (\" {request.existing_plan.title} \"):")
        lines.append(f"- Current Tasks: {len(request.existing_plan.tasks)}")
        completed = [t.title for t in request.existing_plan.tasks if t.is_completed]
        if completed:
            lines.append(f"- Already Completed: {', '.join(completed)}")
        lines.append("Instruction: Adjust uncompleted tasks to fit the student's updated needs.")

    lines.append("\nOutput the complete StudyPlan JSON:")
    return "\n".join(lines)
