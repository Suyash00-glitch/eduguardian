"""
Study Plan Intake Manager — Stateful Preference Collection Engine.

Controls the multi-turn study plan questionnaire conversationally.
The application controls all questions deterministically — the LLM is NEVER
called during intake. Only after preferences are fully collected is the LLM invoked.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from chatbot.backend.schemas.planner import StudyPlanIntakeState, StudyPlanIntakeStep

logger = logging.getLogger(__name__)


class StudyPlanIntakeManager:
    """
    Manages conversational intake flow for study planning.
    Ensures:
    1. Step-by-step preference gathering without overwhelming questionnaires.
    2. Dynamic compound-answer extraction (if a student provides time + days in one message).
    3. Respect for authenticated backend context (never asking for marks/CGPA/weak subjects).
    4. Deterministic progression to COMPLETE state before LLM generation.
    """

    QUESTIONS = {
        StudyPlanIntakeStep.DAILY_TIME: (
            "How much time can you realistically study each day — "
            "1 hour, 2 hours, 3+ hours, or does it vary?"
        ),
        StudyPlanIntakeStep.DAYS_AND_TIME: (
            "Which days would you like to study (e.g., Monday–Friday, Monday–Saturday, Weekends, or All 7 days), "
            "and what time of day works best for you — morning, afternoon, evening, or night?"
        ),
        StudyPlanIntakeStep.SESSION_STYLE: (
            "Do you have a preferred study session structure — "
            "45-minute focused blocks, 1-hour sessions, Pomodoro (25+5 min), continuous, or no preference?"
        ),
        StudyPlanIntakeStep.GOAL: (
            "What is your primary goal (e.g., improving weak subjects, exam prep, boosting CGPA), "
            "and do you have any upcoming exam deadlines or specific subjects you'd like to prioritize?"
        ),
    }

    STEP_ORDER = [
        StudyPlanIntakeStep.DAILY_TIME,
        StudyPlanIntakeStep.DAYS_AND_TIME,
        StudyPlanIntakeStep.SESSION_STYLE,
        StudyPlanIntakeStep.GOAL,
    ]

    def initialize(self, student_name: str | None = None) -> tuple[StudyPlanIntakeState, str]:
        """
        Initializes a fresh intake session (Turn 1).
        Returns the initial intake state and the first friendly question.
        """
        intake = StudyPlanIntakeState(
            active=True,
            step=StudyPlanIntakeStep.DAILY_TIME,
        )
        name_str = f", {student_name}" if student_name else ""
        opener = (
            f"Absolutely{name_str}! I'll build a personalized study plan tailored to your actual academic performance and routine.\n\n"
            f"First, {self.QUESTIONS[StudyPlanIntakeStep.DAILY_TIME]}"
        )
        logger.info("StudyPlanIntake: Initialized new intake session (step=%s)", intake.step.value)
        return intake, opener

    def advance(
        self,
        intake: StudyPlanIntakeState,
        student_message: str,
    ) -> tuple[StudyPlanIntakeState, str | None]:
        """
        Processes student's message, extracts preferences, and advances the intake state.
        Returns:
            (updated_intake_state, next_question_text | None if complete)
        """
        msg = student_message.strip()
        lower = msg.lower()

        # Opportunistic extraction across the whole message
        self._extract_all_present_preferences(intake, msg, lower)

        # Record raw answer for current step
        curr_step_key = intake.step.value
        intake.raw_answers[curr_step_key] = msg

        # Determine the next unanswered step
        next_step = self._find_next_unanswered_step(intake)

        if next_step is None:
            intake.step = StudyPlanIntakeStep.COMPLETE
            intake.active = False
            logger.info("StudyPlanIntake: Intake completed successfully. Preferences: %s", intake.model_dump(exclude={"raw_answers"}))
            return intake, None

        intake.step = next_step
        next_question = self.QUESTIONS[next_step]
        logger.info("StudyPlanIntake: Advanced to step=%s", next_step.value)
        return intake, next_question

    def _find_next_unanswered_step(self, intake: StudyPlanIntakeState) -> StudyPlanIntakeStep | None:
        """Determines the next step in sequence that still needs answers."""
        if intake.daily_minutes is None:
            return StudyPlanIntakeStep.DAILY_TIME
        if intake.study_days is None and intake.preferred_time is None:
            return StudyPlanIntakeStep.DAYS_AND_TIME
        if intake.session_style is None:
            return StudyPlanIntakeStep.SESSION_STYLE
        if intake.main_goal is None and not intake.exam_deadlines and not intake.priority_subjects:
            return StudyPlanIntakeStep.GOAL
        return None

    def _extract_all_present_preferences(self, intake: StudyPlanIntakeState, raw: str, lower: str) -> None:
        """Extracts any preference information present in the message."""
        # 1. Daily Minutes
        mins = self._parse_daily_minutes(lower)
        if mins is not None:
            intake.daily_minutes = mins

        # 2. Preferred Time of Day
        pref_time = self._parse_preferred_time(lower)
        if pref_time is not None:
            intake.preferred_time = pref_time

        # 3. Study Days
        days = self._parse_study_days(lower)
        if days is not None:
            intake.study_days = days

        # 4. Session Style
        style = self._parse_session_style(lower)
        if style is not None:
            intake.session_style = style

        # 5. Main Goal
        goal = self._parse_goal(lower)
        if goal is not None:
            intake.main_goal = goal

        # 6. Deadlines
        deadlines = self._parse_deadlines(lower, raw)
        if deadlines:
            intake.exam_deadlines.extend(deadlines)

        # 7. Priority Subjects
        priority_subs = self._parse_priority_subjects(lower)
        if priority_subs:
            for s in priority_subs:
                if s not in intake.priority_subjects:
                    intake.priority_subjects.append(s)

        # If on SESSION_STYLE step and user answered something general like "no preference" or "regular"
        if intake.step == StudyPlanIntakeStep.SESSION_STYLE and intake.session_style is None:
            if any(w in lower for w in ["no preference", "anything", "whatever", "flexible", "regular", "normal", "default", "standard"]):
                intake.session_style = "flexible"

        # If on GOAL step and user answered general
        if intake.step == StudyPlanIntakeStep.GOAL and intake.main_goal is None:
            if any(w in lower for w in ["no preference", "balanced", "all", "general", "everything", "you decide", "decide based on"]):
                intake.main_goal = "balanced"

    def _parse_daily_minutes(self, lower: str) -> int | None:
        # Check explicit hours
        m_hr = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\b", lower)
        if m_hr:
            hrs = float(m_hr.group(1))
            return int(min(360, max(30, hrs * 60)))
        # Check explicit minutes
        m_min = re.search(r"\b(\d+)\s*(?:mins?|minutes?)\b", lower)
        if m_min:
            return int(min(360, max(20, int(m_min.group(1)))))
        # Words
        if "one hour" in lower or "1 hr" in lower:
            return 60
        if "two hours" in lower or "2 hrs" in lower or "2 hours" in lower:
            return 120
        if "three hours" in lower or "3 hrs" in lower or "3 hours" in lower:
            return 180
        if "four hours" in lower or "4 hrs" in lower or "4 hours" in lower:
            return 240
        if "varies" in lower or "flexible" in lower or "depends" in lower:
            return 120
        return None

    def _parse_preferred_time(self, lower: str) -> str | None:
        time_num_match = re.search(r"\b([1-9]|1[0-2])\s*(?:pm|p\.m\.)\b", lower)
        if time_num_match:
            val = int(time_num_match.group(1))
            h = 12 if val == 12 else val + 12
            return "evening" if h < 21 else "night"
        if re.search(r"\b([1-9]|1[0-2])\s*(?:am|a\.m\.)\b", lower):
            return "morning"
        if re.search(r"\b(morning|mornings|early morning)\b", lower):
            return "morning"
        if re.search(r"\b(afternoon|afternoons)\b", lower):
            return "afternoon"
        if re.search(r"\b(evening|evenings)\b", lower):
            return "evening"
        if re.search(r"\b(night|nights|late night)\b", lower):
            return "night"
        if "flexible" in lower or "anytime" in lower or "whenever" in lower:
            return "evening"
        return None

    def _parse_study_days(self, lower: str) -> list[str] | None:
        if re.search(r"\b(monday\s*(?:to|through|-|-)\s*saturday|mon\s*(?:to|through|-)\s*sat|6\s*days)\b", lower):
            return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        if re.search(r"\b(weekdays?(?:\s+only)?|monday\s*(?:to|through|-|-)\s*friday|mon\s*(?:to|through|-)\s*fri|5\s*days)\b", lower):
            return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        if re.search(r"\b(weekends?(?:\s+only)?|sat(?:urday)?\s*(?:and|&)\s*sun(?:day)?)\b", lower):
            return ["Saturday", "Sunday"]
        if re.search(r"\b(all\s*(?:7\s*)?days|every\s*day|7\s*days|daily)\b", lower):
            return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if "no sunday" in lower or "exclude sunday" in lower:
            return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        # Detect "except sunday", "except weekends"
        if re.search(r"\bexcept\s+sunday\b", lower):
            return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        if re.search(r"\bexcept\s+(?:weekends?|saturday\s*and\s*sunday)\b", lower):
            return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        return None

    def _parse_session_style(self, lower: str) -> str | None:
        if "pomodoro" in lower:
            return "pomodoro"
        if re.search(r"\b(45\s*(?:min|mins|minutes)?|45-min)\b", lower):
            return "45_min_blocks"
        if re.search(r"\b(1\s*hour\s*blocks?|1-hour\s*blocks?|60\s*mins?\s*blocks?)\b", lower):
            return "1_hour_blocks"
        if re.search(r"\b(continuous|one\s+block|single\s+session|single\s+block)\b", lower):
            return "continuous"
        if re.search(r"\b(flexible|no\s+preference|regular|standard|normal)\b", lower):
            return "flexible"
        return None

    def _parse_goal(self, lower: str) -> str | None:
        # Weak subjects / struggling
        if any(k in lower for k in [
            "weak subject", "weak area", "struggling", "improve weak", "focus on weak",
            "bad in", "bad at", "poor in", "not good in", "low marks", "improve marks",
            "improve my marks", "semester marks", "improve semester", "boost marks",
            "low score", "improve score",
        ]):
            return "weak_subjects"
        # Exam preparation
        if any(k in lower for k in [
            "exam prep", "prepare for exam", "exam", "finals", "upcoming exam",
            "internal exam", "end sem", "end-sem", "viva", "test prep",
        ]):
            return "exam_prep"
        # CGPA / grades
        if any(k in lower for k in [
            "cgpa", "sgpa", "grades", "boost marks", "improve gpa", "improve cgpa",
            "improve sgpa", "better grades", "higher grade", "better gpa",
        ]):
            return "improve_cgpa"
        # Syllabus coverage
        if any(k in lower for k in ["syllabus", "complete syllabus", "cover all", "finish syllabus"]):
            return "syllabus"
        # Balanced
        if any(k in lower for k in ["balance", "all subjects equally", "balanced", "overall improvement", "overall"]):
            return "balanced"
        # General improvement catch-all
        if any(k in lower for k in ["improve", "better", "good", "pass", "clear backlog"]):
            return "weak_subjects"
        return None

    def _parse_deadlines(self, lower: str, raw: str) -> list[dict[str, Any]]:
        deadlines: list[dict[str, Any]] = []
        # Named subject + exam in N days/weeks/months
        exam_match = re.search(r"\b([a-zA-Z\s]+?)\s+(?:exam|test|midterm|final)\s+in\s+([0-9]+\s*(?:weeks?|days?|months?))\b", lower)
        if exam_match:
            sub = exam_match.group(1).strip()
            timeframe = exam_match.group(2).strip()
            deadlines.append({"subject": sub.title(), "timeframe": timeframe})
        else:
            # Generic "exam in N days/weeks/months"
            time_only = re.search(r"\b(?:exams?|finals?|tests?)\s+in\s+([0-9]+\s*(?:weeks?|days?|months?))\b", lower)
            if time_only:
                deadlines.append({"subject": "Upcoming Exams", "timeframe": time_only.group(1).strip()})
            else:
                # Natural: "one month", "two weeks", "30 days", "a month"
                word_to_days = {"one": 30, "two": 14, "three": 21, "four": 28, "a ": 30}
                for word, days in word_to_days.items():
                    if f"{word}month" in lower or f"{word} month" in lower:
                        deadlines.append({"subject": "Upcoming Exams", "timeframe": f"{days} days"})
                        break
                    if f"{word}week" in lower or f"{word} week" in lower:
                        deadlines.append({"subject": "Upcoming Exams", "timeframe": f"{days // 2} days"})
                        break
                else:
                    # "N days" standalone
                    simple_days = re.search(r"\b(\d+)\s*(?:days?|weeks?|months?)\b", lower)
                    if simple_days:
                        n = int(simple_days.group(1))
                        unit_match = re.search(r"\b\d+\s*(days?|weeks?|months?)\b", lower)
                        unit = unit_match.group(1) if unit_match else "days"
                        deadlines.append({"subject": "Upcoming Exams", "timeframe": f"{n} {unit}"})
        return deadlines

    def _parse_priority_subjects(self, lower: str) -> list[str]:
        # Extended list of subjects with common shorthand and full names
        known = [
            "dsa", "data structures", "data structure",
            "os", "operating system", "operating systems",
            "dbms", "database management", "database",
            "ml", "machine learning",
            "cn", "computer network", "computer networks",
            "math", "mathematics", "maths",
            "se", "software engineering",
            "ai", "artificial intelligence",
            "python", "java", "c++", "programming",
            "physics", "chemistry", "english",
        ]
        found: list[str] = []
        for k in known:
            if re.search(r"\b" + re.escape(k) + r"\b", lower):
                label = k.upper() if len(k) <= 4 else k.title()
                if label not in found:
                    found.append(label)
        return found

    def build_preferences_dict(self, intake: StudyPlanIntakeState) -> dict[str, Any]:
        """
        Converts the completed intake state into a standardized dictionary
        for PlanRequest.student_preferences.
        """
        return {
            "daily_minutes": intake.daily_minutes or 120,
            "preferred_time": intake.preferred_time or "evening",
            "study_days": intake.study_days or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "schedule_mode": "weekdays" if intake.study_days == ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"] else (
                "mon_sat" if intake.study_days and "Sunday" not in intake.study_days else "everyday"
            ),
            "excluded_days": [d for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] if intake.study_days and d not in intake.study_days],
            "session_style": intake.session_style or "flexible",
            "main_goal": intake.main_goal or "weak_subjects",
            "exam_deadlines": intake.exam_deadlines,
            "priority_subjects": intake.priority_subjects,
            "raw_answers": intake.raw_answers,
            "has_explicit_time": intake.daily_minutes is not None,
            "has_sufficient_preferences": True,
        }
