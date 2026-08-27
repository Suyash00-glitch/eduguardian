"""
Student Insight Agent — LLM prompt templates.
"""
from __future__ import annotations

from chatbot.backend.agents.student_insight.schemas import InsightRequest

SYSTEM_PROMPT = """You are an internal academic analysis engine for EduGuardian AI.

Your role is to analyze a student's academic data and produce a structured JSON assessment.

CRITICAL RULES:
1. Your output is INTERNAL ONLY — it will NEVER be shown directly to the student.
2. Do NOT use emotionally negative language like "failing", "at-risk", "poor performance",
   or "high risk" — use professional analytical language.
3. Be precise, factual, and data-driven.
4. You must return a valid JSON object matching the InsightResponse schema.

Output JSON format:
{
  "student_id": "<string>",
  "overall_summary": "<one sentence professional internal summary>",
  "strengths": ["<subject or skill>", ...],
  "focus_areas": ["<subject or area>", ...],
  "subject_insights": [
    {
      "subject_name": "<string>",
      "status": "strength|needs_attention|critical",
      "key_observation": "<factual observation>",
      "recommended_action": "<specific action>"
    }
  ],
  "contributing_factors": ["<factor>", ...],
  "recommended_areas_of_attention": ["<area>", ...],
  "support_intensity": "light|standard|intensive",
  "has_concerning_patterns": true|false
}
"""


def build_user_prompt(request: InsightRequest) -> str:
    ctx = request.student_context
    lines = [
        f"Student ID: {ctx.student_id}",
        f"Name: {ctx.full_name}",
        f"Program: {ctx.program or 'Unknown'}, Year {ctx.year_of_study or '?'}, {ctx.semester or ''}",
    ]

    if ctx.attendance:
        att = ctx.attendance
        lines.append(f"\nAttendance:")
        lines.append(f"  Overall: {att.overall_percentage}%")
        lines.append(f"  Recent trend: {att.recent_trend or 'unknown'}")
        if att.subjects_below_threshold:
            lines.append(f"  Below threshold: {', '.join(att.subjects_below_threshold)}")

    if ctx.subjects:
        lines.append("\nSubject Performance:")
        for s in ctx.subjects:
            parts = [f"  {s.subject_name}:"]
            if s.marks_percentage is not None:
                parts.append(f"marks={s.marks_percentage}%")
            if s.grade:
                parts.append(f"grade={s.grade}")
            if s.assignment_completion_rate is not None:
                parts.append(f"assignments={s.assignment_completion_rate*100:.0f}%")
            if s.quiz_average is not None:
                parts.append(f"quiz_avg={s.quiz_average}")
            lines.append(" ".join(parts))

    if ctx.engagement:
        eng = ctx.engagement
        lines.append(f"\nEngagement (last 30 days):")
        lines.append(f"  LMS logins: {eng.lms_logins_last_30_days}")
        lines.append(f"  Resources accessed: {eng.resources_accessed}")

    if request.focus_question:
        lines.append(f"\nFocus question: {request.focus_question}")

    lines.append("\nAnalyze the above and return the InsightResponse JSON:")
    return "\n".join(lines)
