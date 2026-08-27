"""
Study Planner Agent — Prompts & Context Builders.

Defines the system prompt and context serialization for generating structured,
actionable, and achievable study plans.
"""
from __future__ import annotations

import json
from datetime import date
from typing import Any
from chatbot.backend.schemas.planner import PlanRequest


STUDY_PLANNER_SYSTEM_PROMPT = """You are the expert Academic Study Planning Specialist for EduGuardian AI.
Your purpose is to turn student academic standing, course requirements, student goals, and supplemental interaction-derived learning history into an actionable, realistic, and personalized daily academic study schedule.

CORE PRINCIPLES (MANDATORY):
1. ACADEMIC STUDY ACTIVITIES ONLY:
   - Every single task in the plan MUST be a direct student academic study activity (e.g., "Data Structures — Binary Tree Traversals: Review inorder/preorder traversal and solve 4 practice problems", "DBMS — Normalization Practice: Solve 1NF to 3NF exercise questions", "Operating Systems — Virtual Memory Review").
   - NEVER generate administrative, coaching, or counseling tasks such as:
     * "Communicate with student"
     * "Discuss student's concerns and goals"
     * "Respect student's autonomy in study planning"
     * "Follow up with student"
     * "Counsel student"
     * "Understand student's goals"
   - The student is the user executing these tasks. All tasks must be self-directed academic work.

2. NEVER SET SUBJECT TO NONE & AVOID GENERIC PLACEHOLDERS WHEN DATA EXISTS:
   - Every task MUST have a valid, non-empty `subject` string (e.g. "Data Structures", "DBMS", "Operating Systems", "Mathematics").
   - NEVER output `"subject": "None"`, `"subject": null`, or `"subject": ""`.
   - When enrolled courses and learning history topics exist, DO NOT generate vague generic tasks like "General Study: Core Concept Review". Map weak topics directly to their parent subject (e.g. "Data Structures: Binary Tree Traversals").
   - Generic tasks ("General Study") are acceptable ONLY when no course or topic information is known.

3. HIERARCHICAL PLANNING PRIORITY:
   Prioritize study allocation according to this strict hierarchy:
   1. Official Urgent Academic Deadlines (assignments/projects due soon — highest priority).
   2. Official Academic Focus Areas from StudentInsight (courses with lower marks or high growth needs).
   3. Practice Focus Topics from LearningHistory (topics with low quiz scores/accuracy — allocate targeted practice).
   4. Maintaining Mastered Topics from LearningHistory (schedule light maintenance/revision, e.g. 20–30 min, rather than daily cramming).
   5. General Coursework Revision & Synthesis.

4. SCOPED GOAL OVERRIDES:
   - If the student's request is specific (e.g. "Make me a study plan for DBMS" or "Prepare for my exam tomorrow"), focus primarily on that subject/goal without forcing unrelated topics.

5. TIME CONSTRAINTS & MANAGEABILITY:
   - If the student specifies an available study time (e.g. "1 hour per day", "2 hours daily", "30 mins"), strictly limit total daily study duration to that target.
   - Default daily study blocks should be 30–60 minutes per session. Never schedule unrealistic workloads.

6. LEARNING PREFERENCES INFLUENCE:
   - If student prefers concise verbosity, keep task descriptions punchy and direct.
   - If student prefers step-by-step explanations, format task descriptions as sequential steps.
   - If student preferred language is Python (or other), suggest that language for programming practice tasks.

7. SUPPORTIVE, GROWTH-ORIENTED TONE (NO LABELS OR SCORE DUMPS):
   - NEVER use stigmatizing labels ("weak student", "failing student", "at-risk").
   - NEVER write "You scored 40%, therefore you are weak".
   - Frame every task as an empowering step toward concept mastery.

8. STRICT JSON OUTPUT:
   - You must output ONLY a valid JSON object matching the StudyPlan schema. Do NOT wrap in conversational text.

JSON SCHEMA:
{
  "title": "<Concise, encouraging plan title, e.g. 'Focused Revision Plan: Data Structures & DBMS'>",
  "goals": ["<Clear academic objective 1>", "<Clear academic objective 2>"],
  "priorities": ["<Priority Subject 1>", "<Priority Subject 2>"],
  "week_start": "<YYYY-MM-DD>",
  "tasks": [
    {
      "task_id": "<uuid or unique string>",
      "title": "<Actionable study task title, e.g. 'Binary Tree Traversal Practice'>",
      "description": "<Clear instructions on what and how to study>",
      "subject": "<Real Course Name, e.g. 'Data Structures'>",
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
  "resources": ["<Specific textbook chapter, lecture slides, or LMS practice set>"],
  "notes": "<Brief encouraging coach's tip for sticking to the schedule>",
  "rationale": "<Why this sequence was chosen based on the student's courses, deadlines, and practice needs>"
}
"""


def format_planner_learning_context(
    learning_history: dict[str, Any] | None,
    user_goal: str | None = None,
) -> str | None:
    """
    Constructs a compact, actionable learning context block (< 60 tokens)
    for Study Planner prompts.
    """
    if not learning_history or not isinstance(learning_history, dict):
        return None

    mastered = learning_history.get("mastered_topics") or []
    needs_practice = learning_history.get("needs_practice_topics") or []
    quiz_mastery = learning_history.get("quiz_mastery") or {}
    prefs = learning_history.get("explicit_preferences") or {}

    lines = []

    # 1. Topics needing practice
    if needs_practice:
        practice_items = []
        for t in needs_practice:
            acc = quiz_mastery.get(t)
            acc_str = f" ({int(acc*100)}% accuracy)" if acc is not None else ""
            practice_items.append(f"{t}{acc_str}")
        lines.append(f"- Needs Practice Focus Topics: {', '.join(practice_items)}")
        lines.append("  (Instruction: Allocate dedicated, topic-specific practice blocks for these topics under their relevant enrolled courses)")

    # 2. Mastered topics
    if mastered:
        lines.append(f"- Mastered Topics: {', '.join(mastered)}")
        lines.append("  (Instruction: Schedule light maintenance/revision rather than heavy daily cramming)")

    # 3. Active Learning Preferences
    pref_directives = []
    if "verbosity" in prefs and prefs["verbosity"] == "concise":
        pref_directives.append("Keep task descriptions concise and actionable.")
    if "explanation_style" in prefs and prefs["explanation_style"] == "step_by_step":
        pref_directives.append("Frame task descriptions as clear sequential steps.")
    if "code_language" in prefs:
        pref_directives.append(f"Use {prefs['code_language']} for programming practice tasks.")

    if pref_directives:
        lines.append(f"- Student Study Preferences: {' '.join(pref_directives)}")

    if not lines:
        return None

    return "── SUPPLEMENTAL LEARNING CONTEXT (Interaction-Derived Signals) ──\n" + "\n".join(lines)


def build_study_planner_user_prompt(request: PlanRequest) -> str:
    """Constructs the prompt for the Study Planner LLM call."""
    ctx = request.student_context
    today_str = date.today().isoformat()

    lines = [
        f"Current Planning Date (week_start): {today_str}",
        f"Plan Timeframe: {request.timeframe_days} days",
        f"Student: {ctx.student_name or ctx.full_name or 'Student'}",
    ]

    if ctx.department:
        lines.append(f"Department/Major: {ctx.department}")
    if ctx.year_of_study:
        lines.append(f"Year of Study: Year {ctx.year_of_study}")

    # Student's explicit request or goal
    if request.user_goal:
        lines.append(f"\nStudent's Explicit Goal/Request:\n\"{request.user_goal}\"")

    # Enrolled courses
    if ctx.subjects:
        lines.append("\nEnrolled Courses & Academic Standing:")
        for s in ctx.subjects:
            marks = s.current_marks_percentage if s.current_marks_percentage is not None else s.marks_percentage
            score_str = f"{marks:.0f}%" if marks is not None else "In progress"
            lines.append(f"- {s.subject_name} (Current marks: {score_str}, Grade: {s.grade or 'N/A'})")
    else:
        lines.append("\nEnrolled Courses: No course records on file. Build a structured academic plan based directly on the student's request.")

    # Upcoming deadlines
    if ctx.assignments and ctx.assignments.upcoming_deadlines:
        lines.append("\nUpcoming Deadlines to Prioritize:")
        for dl in ctx.assignments.upcoming_deadlines:
            lines.append(f"- {dl.get('title', 'Assignment')} in {dl.get('subject', 'Course')} (Due: {dl.get('due_date', 'Soon')}, Priority: {dl.get('priority', 'High')})")

    # Academic Insight Guidance
    if request.student_insight:
        ins = request.student_insight
        lines.append("\nAcademic Insight Guidance:")
        if ins.strengths:
            lines.append(f"- Strengths to Maintain: {', '.join(ins.strengths)}")
        if ins.focus_areas:
            lines.append(f"- Focus Areas for Growth: {', '.join(ins.focus_areas)}")
        if ins.recommended_areas_of_attention:
            lines.append(f"- Recommended Practice Topics: {', '.join(ins.recommended_areas_of_attention)}")

    # Supplemental Learning History (Quiz performance & explicit preferences)
    learning_context_sec = format_planner_learning_context(request.learning_history, request.user_goal)
    if learning_context_sec:
        lines.append(f"\n{learning_context_sec}")

    # Existing plan context (for revisions)
    if request.existing_plan:
        lines.append(f"\nExisting Plan to Revise (\"{request.existing_plan.title}\"):")
        lines.append(f"- Current Tasks: {len(request.existing_plan.tasks)}")
        completed = [t.title for t in request.existing_plan.tasks if t.is_completed]
        if completed:
            lines.append(f"- Already Completed: {', '.join(completed)}")
        lines.append("Instruction: Keep completed progress and adjust remaining tasks to fit the student's updated needs.")

    lines.append("\nCRITICAL REMINDER: Output ONLY valid JSON. Every task MUST have a valid subject name. Do NOT output 'Communicate with student' or 'Subject = None'.")
    lines.append("Output the complete StudyPlan JSON:")
    return "\n".join(lines)

