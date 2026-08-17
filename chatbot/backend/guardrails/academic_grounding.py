"""
Academic Grounding Guardrail for EduGuardian AI.

Provides deterministic, lightweight verification of official student academic claims:
- Validates attendance percentages (overall and subject-specific)
- Validates subject marks, scores, and letter grades
- Validates enrolled subjects and semester/year/department profile data
- Validates assignment deadlines, pending counts, and completion counts
- Rewrites contradicted claims to authoritative StudentContext ground truth
- Preserves general educational explanations, study techniques, and emotional support
- Ensures strict multi-student isolation using authenticated StudentContext
"""
from __future__ import annotations

import re
import logging
from typing import Any

from chatbot.backend.guardrails.base import BaseOutputGuardrail
from chatbot.backend.schemas.guardrails import GuardrailAction, GuardrailCategory, GuardrailResult
from chatbot.backend.schemas.student import StudentContext, SubjectPerformance

logger = logging.getLogger(__name__)

# Common educational subject abbreviations mapping
_SUBJECT_ALIASES: dict[str, list[str]] = {
    "data structures": ["ds", "dsa", "data structure", "data structures and algorithms"],
    "mathematics": ["math", "maths", "calculus", "linear algebra", "discrete math"],
    "database management systems": ["dbms", "database", "databases", "sql"],
    "operating systems": ["os", "operating system"],
    "computer networks": ["cn", "networking", "networks"],
    "python programming": ["python", "python programming", "py"],
    "machine learning": ["ml", "machine learning", "ai"],
    "software engineering": ["se", "software engineering"],
}


def _normalize(name: str) -> str:
    """Normalizes a string by stripping punctuation, extra spaces, and lowercasing."""
    if not name:
        return ""
    clean = re.sub(r"[^a-zA-Z0-9\s]", " ", name.lower())
    return " ".join(clean.split())


def _find_subject(
    query_subject: str,
    subjects: list[SubjectPerformance],
) -> SubjectPerformance | None:
    """Finds a matching SubjectPerformance by name, code, or alias."""
    norm_query = _normalize(query_subject)
    if not norm_query:
        return None

    # 1. Exact or substring match in enrolled subjects
    for subj in subjects:
        norm_name = _normalize(subj.subject_name)
        norm_code = _normalize(subj.subject_code or "")
        if norm_query == norm_name or norm_query == norm_code:
            return subj
        if norm_query in norm_name or norm_name in norm_query:
            return subj

    # 2. Alias mapping lookup
    for canonical_name, aliases in _SUBJECT_ALIASES.items():
        if norm_query in aliases or norm_query == canonical_name:
            for subj in subjects:
                norm_subj = _normalize(subj.subject_name)
                if canonical_name in norm_subj or any(a in norm_subj for a in aliases):
                    return subj

    return None


class AcademicGroundingGuardrail(BaseOutputGuardrail):
    """
    Deterministic Academic Grounding Guardrail validating official claims against StudentContext.
    """

    def evaluate(
        self,
        response_text: str,
        student_context: StudentContext | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GuardrailResult:
        """
        Evaluates and grounds student-specific academic claims in the assistant response.
        """
        if not response_text:
            return GuardrailResult(
                action=GuardrailAction.ALLOW,
                category=GuardrailCategory.NONE,
                sanitized_text="",
            )

        text = response_text
        modified = False
        reasons: list[str] = []

        # ── 1. Attendance Grounding ───────────────────────────────────────────
        # A. Subject-specific attendance: e.g. "Data Structures attendance is 91%"
        subj_att_pattern = re.compile(
            r"\b(?:your\s+)?([A-Za-z\s]{3,30}?)\s+attendance\s+(?:is|was|stands\s+at|is\s+currently|of|at)?\s*:?\s*(\d+(?:\.\d+)?)\s*%",
            re.IGNORECASE,
        )
        for match in list(subj_att_pattern.finditer(text)):
            subj_name = match.group(1).strip()
            # Ignore if phrase is generic like "overall", "class", "total", "college"
            if subj_name.lower() in ("overall", "total", "class", "general", "course", "college", "school", "your", "my"):
                continue

            claimed_pct = float(match.group(2))
            if student_context and student_context.subjects:
                found_subj = _find_subject(subj_name, student_context.subjects)
                if found_subj and found_subj.attendance_percentage is not None:
                    actual_pct = found_subj.attendance_percentage
                    if abs(claimed_pct - actual_pct) > 0.5:
                        old_claim = match.group(0)
                        pct_str = f"{actual_pct:g}%"
                        new_claim = f"{found_subj.subject_name} attendance is {pct_str}"
                        text = text.replace(old_claim, new_claim)
                        modified = True
                        reasons.append(f"Grounding: Corrected {found_subj.subject_name} attendance from {claimed_pct:g}% to {pct_str}")
                        logger.info("AcademicGroundingGuardrail: category=attendance action=rewrite subject=%s original=%g%% grounded=%s", found_subj.subject_name, claimed_pct, pct_str)
                elif not found_subj:
                    # Claimed attendance in a non-enrolled subject
                    old_claim = match.group(0)
                    new_claim = f"attendance for {subj_name} (not currently in your official course list)"
                    text = text.replace(old_claim, new_claim)
                    modified = True
                    reasons.append(f"Grounding: Flagged unverified subject attendance for '{subj_name}'")

        # B. Overall attendance: e.g. "Your attendance is 82%"
        overall_att_pattern = re.compile(
            r"\b(?:your|my|overall)\s+attendance\s+(?:is|was|stands\s+at|is\s+currently|of|at)?\s*:?\s*(\d+(?:\.\d+)?)\s*%",
            re.IGNORECASE,
        )
        for match in list(overall_att_pattern.finditer(text)):
            claimed_pct = float(match.group(1))
            if student_context and student_context.attendance and student_context.attendance.overall_percentage is not None:
                actual_pct = student_context.attendance.overall_percentage
                if abs(claimed_pct - actual_pct) > 0.5:
                    old_claim = match.group(0)
                    pct_str = f"{actual_pct:g}%"
                    new_claim = f"your attendance is {pct_str}"
                    text = text.replace(old_claim, new_claim)
                    modified = True
                    reasons.append(f"Grounding: Corrected overall attendance from {claimed_pct:g}% to {pct_str}")
                    logger.info("AcademicGroundingGuardrail: category=attendance action=rewrite original=%g%% grounded=%s", claimed_pct, pct_str)
            elif not student_context or not student_context.attendance or student_context.attendance.overall_percentage is None:
                # Attendance record not available
                old_claim = match.group(0)
                new_claim = "your attendance record is not available right now"
                text = text.replace(old_claim, new_claim)
                modified = True
                reasons.append("Grounding: Replaced ungrounded attendance claim with missing-record notice")

        # ── 2. Marks & Score Grounding ────────────────────────────────────────
        # e.g. "You scored 85% in Data Structures" or "Your DBMS mark is 51%"
        marks_pattern_1 = re.compile(
            r"\b(?:you|i)\s+scored\s+(\d+(?:\.\d+)?)\s*%\s+in\s+([A-Za-z\s]{3,30})\b",
            re.IGNORECASE,
        )
        for match in list(marks_pattern_1.finditer(text)):
            claimed_score = float(match.group(1))
            subj_name = match.group(2).strip()
            if student_context and student_context.subjects:
                found_subj = _find_subject(subj_name, student_context.subjects)
                actual_score = found_subj.marks_percentage or found_subj.current_marks_percentage if found_subj else None
                if found_subj and actual_score is not None:
                    if abs(claimed_score - actual_score) > 0.5:
                        old_claim = match.group(0)
                        score_str = f"{actual_score:g}%"
                        new_claim = f"you scored {score_str} in {found_subj.subject_name}"
                        text = text.replace(old_claim, new_claim)
                        modified = True
                        reasons.append(f"Grounding: Corrected {found_subj.subject_name} score from {claimed_score:g}% to {score_str}")
                        logger.info("AcademicGroundingGuardrail: category=marks action=rewrite subject=%s original=%g%% grounded=%s", found_subj.subject_name, claimed_score, score_str)
                elif not found_subj:
                    old_claim = match.group(0)
                    new_claim = f"you don't have official records for {subj_name}"
                    text = text.replace(old_claim, new_claim)
                    modified = True
                    reasons.append(f"Grounding: Flagged score claim in unverified subject '{subj_name}'")

        marks_pattern_2 = re.compile(
            r"\b(?:your|my)?\s*([A-Za-z\s]{3,30}?)\s+(?:marks?|score)\s+(?:is|was|stands\s+at|is\s+currently|of)?\s*:?\s*(\d+(?:\.\d+)?)\s*%",
            re.IGNORECASE,
        )
        for match in list(marks_pattern_2.finditer(text)):
            subj_name = match.group(1).strip()
            if subj_name.lower() in ("overall", "quiz", "test", "exam", "average", "your", "my"):
                continue
            claimed_score = float(match.group(2))
            if student_context and student_context.subjects:
                found_subj = _find_subject(subj_name, student_context.subjects)
                actual_score = found_subj.marks_percentage or found_subj.current_marks_percentage if found_subj else None
                if found_subj and actual_score is not None:
                    if abs(claimed_score - actual_score) > 0.5:
                        old_claim = match.group(0)
                        score_str = f"{actual_score:g}%"
                        new_claim = f"{found_subj.subject_name} mark is {score_str}"
                        text = text.replace(old_claim, new_claim)
                        modified = True
                        reasons.append(f"Grounding: Corrected {found_subj.subject_name} mark from {claimed_score:g}% to {score_str}")
                        logger.info("AcademicGroundingGuardrail: category=marks action=rewrite subject=%s original=%g%% grounded=%s", found_subj.subject_name, claimed_score, score_str)

        # ── 3. Grade Grounding ────────────────────────────────────────────────
        # e.g. "You got an A in Operating Systems" or "Your grade in Math is B+"
        grade_pattern = re.compile(
            r"\b(?:you|i)\s+(?:got|received|have|earned|hold)\s+(?:an?|a\s+grade\s+of)?\s*([A-D][+-]?|F|O|S)\s+in\s+([A-Za-z\s]{3,30})\b",
            re.IGNORECASE,
        )
        for match in list(grade_pattern.finditer(text)):
            claimed_grade = match.group(1).strip().upper()
            subj_name = match.group(2).strip()
            if student_context and student_context.subjects:
                found_subj = _find_subject(subj_name, student_context.subjects)
                if found_subj and found_subj.grade:
                    actual_grade = found_subj.grade.strip().upper()
                    if claimed_grade != actual_grade:
                        old_claim = match.group(0)
                        new_claim = f"you received a grade of {actual_grade} in {found_subj.subject_name}"
                        text = text.replace(old_claim, new_claim)
                        modified = True
                        reasons.append(f"Grounding: Corrected {found_subj.subject_name} grade from {claimed_grade} to {actual_grade}")
                        logger.info("AcademicGroundingGuardrail: category=grade action=rewrite subject=%s original=%s grounded=%s", found_subj.subject_name, claimed_grade, actual_grade)

        # ── 4. Subject Enrollment Grounding ───────────────────────────────────
        # e.g. "You are enrolled in Machine Learning"
        enrollment_pattern = re.compile(
            r"\b(?:you\s+are|you're)\s+(?:currently\s+)?enrolled\s+in\s+([A-Za-z\s]{3,30})\b",
            re.IGNORECASE,
        )
        for match in list(enrollment_pattern.finditer(text)):
            subj_name = match.group(1).strip()
            if student_context and student_context.subjects:
                found_subj = _find_subject(subj_name, student_context.subjects)
                if not found_subj:
                    # Claimed enrollment in a subject not in student context
                    old_claim = match.group(0)
                    new_claim = f"you have coursework available in your curriculum, though {subj_name} is not in your official enrollment"
                    text = text.replace(old_claim, new_claim)
                    modified = True
                    reasons.append(f"Grounding: Corrected fabricated enrollment in '{subj_name}'")

        # ── 5. Assignment Deadline & Completion Grounding ─────────────────────
        # e.g. "Your Data Structures assignment is due Monday"
        deadline_pattern = re.compile(
            r"\b(?:your\s+)?([A-Za-z\s]{3,30}?)\s+assignment(?:\s+\d+)?\s+(?:is\s+)?due\s+(?:on\s+)?(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|[A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?|\d{4}-\d{2}-\d{2})\b",
            re.IGNORECASE,
        )
        for match in list(deadline_pattern.finditer(text)):
            subj_name = match.group(1).strip()
            claimed_day = match.group(2).strip()
            if student_context and student_context.assignments:
                # Find matching upcoming deadline in assignments
                deadlines = student_context.assignments.upcoming_deadlines or []
                matched_deadline = None
                for d in deadlines:
                    d_subj = d.get("subject") or d.get("subject_name") or d.get("title") or ""
                    if _find_subject(subj_name, [SubjectPerformance(subject_name=d_subj)]):
                        matched_deadline = d
                        break

                if matched_deadline:
                    actual_due = str(matched_deadline.get("due_date") or matched_deadline.get("due") or matched_deadline.get("deadline") or "")
                    if claimed_day.lower() not in actual_due.lower():
                        old_claim = match.group(0)
                        new_claim = f"your {subj_name} assignment is due {actual_due}"
                        text = text.replace(old_claim, new_claim)
                        modified = True
                        reasons.append(f"Grounding: Corrected {subj_name} assignment deadline from {claimed_day} to {actual_due}")
                        logger.info("AcademicGroundingGuardrail: category=assignment_deadline action=rewrite subject=%s original=%s grounded=%s", subj_name, claimed_day, actual_due)
                else:
                    # No deadline recorded for this subject
                    pass

        # Pending assignment counts: e.g. "You have 4 pending assignments"
        pending_pattern = re.compile(
            r"\b(?:you\s+have|there\s+are)\s+(\d+)\s+pending\s+assignments?\b",
            re.IGNORECASE,
        )
        for match in list(pending_pattern.finditer(text)):
            claimed_count = int(match.group(1))
            if student_context and student_context.assignments and student_context.assignments.pending_count is not None:
                actual_count = student_context.assignments.pending_count
                if claimed_count != actual_count:
                    old_claim = match.group(0)
                    new_claim = f"you have {actual_count} pending assignment{'s' if actual_count != 1 else ''}"
                    text = text.replace(old_claim, new_claim)
                    modified = True
                    reasons.append(f"Grounding: Corrected pending assignments count from {claimed_count} to {actual_count}")
                    logger.info("AcademicGroundingGuardrail: category=pending_assignments action=rewrite original=%d grounded=%d", claimed_count, actual_count)

        # Completed assignment counts: e.g. "You completed 2 assignments"
        completed_pattern = re.compile(
            r"\b(?:you\s+have\s+)?completed\s+(\d+)\s+assignments?\b",
            re.IGNORECASE,
        )
        for match in list(completed_pattern.finditer(text)):
            claimed_count = int(match.group(1))
            if student_context and student_context.assignments and student_context.assignments.total_submitted is not None:
                actual_count = student_context.assignments.total_submitted
                if claimed_count != actual_count:
                    old_claim = match.group(0)
                    new_claim = f"completed {actual_count} assignment{'s' if actual_count != 1 else ''}"
                    text = text.replace(old_claim, new_claim)
                    modified = True
                    reasons.append(f"Grounding: Corrected completed assignments count from {claimed_count} to {actual_count}")

        # ── 6. Profile / Year / Semester Grounding ─────────────────────────────
        # e.g. "You are in 4th semester"
        sem_pattern = re.compile(
            r"\b(?:you\s+are\s+in|in\s+your)\s+(\d+)(?:st|nd|rd|th)?\s+semester\b",
            re.IGNORECASE,
        )
        for match in list(sem_pattern.finditer(text)):
            claimed_sem = int(match.group(1))
            if student_context and student_context.semester is not None:
                try:
                    actual_sem = int(student_context.semester)
                    if claimed_sem != actual_sem:
                        old_claim = match.group(0)
                        new_claim = f"in your {actual_sem}th semester"
                        text = text.replace(old_claim, new_claim)
                        modified = True
                        reasons.append(f"Grounding: Corrected semester from {claimed_sem} to {actual_sem}")
                except Exception:
                    pass

        # Year of study: e.g. "You are in 3rd year"
        year_pattern = re.compile(
            r"\b(?:you\s+are\s+in|in\s+your)\s+(\d+)(?:st|nd|rd|th)?\s+year\b",
            re.IGNORECASE,
        )
        for match in list(year_pattern.finditer(text)):
            claimed_year = int(match.group(1))
            if student_context and student_context.year_of_study is not None:
                actual_year = student_context.year_of_study
                if claimed_year != actual_year:
                    old_claim = match.group(0)
                    new_claim = f"in your {actual_year}th year"
                    text = text.replace(old_claim, new_claim)
                    modified = True
                    reasons.append(f"Grounding: Corrected year of study from {claimed_year} to {actual_year}")

        # ── 7. Clean Result Assembly ──────────────────────────────────────────
        text = text.strip()

        if modified:
            return GuardrailResult(
                action=GuardrailAction.REVISE,
                category=GuardrailCategory.ACADEMIC_GROUNDING,
                reason="; ".join(reasons),
                sanitized_text=text,
                metadata={"grounding_modifications": reasons},
            )

        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            category=GuardrailCategory.NONE,
            reason="Output is academically grounded or contains no official academic claims.",
            sanitized_text=text,
        )
