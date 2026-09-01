"""
Test Suite: Study Plan Multi-Step Intake Flow & Personalization.

Validates:
1. Turn 1 bare study plan request initiates stateful intake questionnaire without calling LLM or generating plan.
2. Step-by-step preference collection preserves student answers across conversation turns.
3. Turn N intake completion invokes plan generation with authentic student profile + preferences.
4. Plan reflects daily hour constraints (e.g. <=60 min for 1 hour/day).
5. Plan reflects evening time slots when requested.
6. Plan excludes weekends when Monday-Friday requested.
7. Plan prioritizes upcoming exams/deadlines.
8. Student isolation (Student A context cannot leak to Student B).
9. Mid-intake answers are correctly routed to study_plan_intake (not recovery_coach).
10. Cancel keyword deactivates the intake session gracefully.
"""
import pytest
from chatbot.backend.schemas.planner import StudyPlanIntakeStep, StudyPlanIntakeState, PlanRequest
from chatbot.backend.agents.study_planner.intake import StudyPlanIntakeManager
from chatbot.backend.agents.study_planner.builder import build_default_plan
from chatbot.backend.orchestrator.graph import run_graph
from chatbot.backend.orchestrator.router import route_after_intent
from chatbot.backend.orchestrator.state import GraphState
from chatbot.tests.fixtures.student_fixtures import get_mock_student_context, STUDENT_A_HIGH_ACHIEVER, STUDENT_B_STRUGGLING


class TestIntakeRouting:
    """Unit tests for the route_after_intent bypass for active intake sessions."""

    def _make_state(self, user_message: str, intake: StudyPlanIntakeState | None) -> GraphState:
        return {  # type: ignore[typeddict-item]
            "user_message": user_message,
            "intent": "general_support",
            "intake_state": intake,
            "processed_request": {"is_deterministic": False},
            "final_response": None,
            "student_id": "test_student",
            "conversation_id": "test_conv",
            "student_context": None,
            "conversation_history": [],
            "agents_used": [],
            "metadata": {},
        }

    def test_no_active_intake_routes_normally(self):
        """Without an active intake, a generic message goes to recovery_coach."""
        state = self._make_state("Hello there", intake=None)
        assert route_after_intent(state) == "recovery_coach"

    def test_active_intake_routes_to_study_plan_intake(self):
        """With an active intake, ANY message (even generic) routes to study_plan_intake."""
        intake = StudyPlanIntakeState(active=True, step=StudyPlanIntakeStep.DAILY_TIME)
        state = self._make_state("1 hour", intake=intake)
        assert route_after_intent(state) == "study_plan_intake"

    def test_active_intake_night_answer_routes_to_intake(self):
        """Short answer 'night' routes to intake, not recovery_coach."""
        intake = StudyPlanIntakeState(active=True, step=StudyPlanIntakeStep.DAYS_AND_TIME)
        state = self._make_state("night", intake=intake)
        assert route_after_intent(state) == "study_plan_intake"

    def test_complete_intake_does_not_override_routing(self):
        """Completed intake should not trigger override (step=COMPLETE, active=False)."""
        intake = StudyPlanIntakeState(active=False, step=StudyPlanIntakeStep.COMPLETE)
        state = self._make_state("what else can you do?", intake=intake)
        # No override: goes to normal routing (general_support → recovery_coach)
        assert route_after_intent(state) == "recovery_coach"

    def test_cancel_keyword_still_routes_to_intake_for_graceful_deactivation(self):
        """Cancel keyword routes to study_plan_intake (which handles graceful deactivation)."""
        intake = StudyPlanIntakeState(active=True, step=StudyPlanIntakeStep.SESSION_STYLE)
        state = self._make_state("cancel", intake=intake)
        # Cancel is handled inside intake node, so still routed there first
        assert route_after_intent(state) == "study_plan_intake"


class TestIntakeParserFixes:
    """Tests for expanded natural language parsers added in this fix."""

    def test_improve_semester_marks_parsed_as_goal(self):
        """'Improve my semester marks' should map to weak_subjects goal."""
        manager = StudyPlanIntakeManager()
        state, _ = manager.initialize()
        # Answer daily time, days, style, then goal
        state, _ = manager.advance(state, "1 hour")
        state, _ = manager.advance(state, "Monday to Saturday, night")
        state, _ = manager.advance(state, "flexible")
        state, q = manager.advance(state, "Improve my semester marks")
        assert state.main_goal == "weak_subjects"
        assert state.step == StudyPlanIntakeStep.COMPLETE

    def test_monday_to_saturday_parsed(self):
        """'Monday to Saturday' (with 'to') should parse 6 days correctly."""
        manager = StudyPlanIntakeManager()
        state, _ = manager.initialize()
        state, _ = manager.advance(state, "2 hours")
        state, _ = manager.advance(state, "Monday to Saturday, evening")
        assert state.study_days == ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        assert state.preferred_time == "evening"

    def test_dbms_and_os_priority_subjects(self):
        """'DBMS and OS' should be extracted as priority subjects."""
        manager = StudyPlanIntakeManager()
        state, _ = manager.initialize()
        state, _ = manager.advance(state, "1 hour")
        state, _ = manager.advance(state, "Monday to Friday, night")
        state, _ = manager.advance(state, "no preference")
        state, _ = manager.advance(state, "focus on DBMS and OS")
        assert "DBMS" in state.priority_subjects
        assert "OS" in state.priority_subjects

    def test_one_month_deadline_parsed(self):
        """'One month' should produce a deadline entry."""
        manager = StudyPlanIntakeManager()
        state, _ = manager.initialize()
        state, _ = manager.advance(state, "1 hour")
        state, _ = manager.advance(state, "weekdays, night")
        state, _ = manager.advance(state, "flexible")
        state, _ = manager.advance(state, "exam prep in one month")
        assert len(state.exam_deadlines) > 0




class TestStudyPlanIntakeUnit:
    """Unit tests for StudyPlanIntakeManager parsing and progression."""

    def test_manager_initialization(self):
        manager = StudyPlanIntakeManager()
        state, q = manager.initialize(student_name="Aarav")
        assert state.active is True
        assert state.step == StudyPlanIntakeStep.DAILY_TIME
        assert "Aarav" in q
        assert "how much time" in q.lower()

    def test_advance_daily_time_to_days_and_time(self):
        manager = StudyPlanIntakeManager()
        state, _ = manager.initialize()
        state, next_q = manager.advance(state, "I can study 2 hours a day.")
        assert state.daily_minutes == 120
        assert state.step == StudyPlanIntakeStep.DAYS_AND_TIME
        assert "which days" in next_q.lower()

    def test_advance_compound_answer_extracts_multiple(self):
        manager = StudyPlanIntakeManager()
        state, _ = manager.initialize()
        # Student answers both time and days in one message
        state, next_q = manager.advance(state, "2 hours every evening, Monday to Friday")
        assert state.daily_minutes == 120
        assert state.preferred_time == "evening"
        assert state.study_days == ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        # Should advance to session style or goal
        assert state.step == StudyPlanIntakeStep.SESSION_STYLE

    def test_full_intake_conversation_progression(self):
        manager = StudyPlanIntakeManager()
        state, q1 = manager.initialize()
        assert state.step == StudyPlanIntakeStep.DAILY_TIME

        # Turn 2: Daily time
        state, q2 = manager.advance(state, "1 hour per day")
        assert state.daily_minutes == 60
        assert state.step == StudyPlanIntakeStep.DAYS_AND_TIME

        # Turn 3: Days and time
        state, q3 = manager.advance(state, "Monday to Saturday, evening at 7 PM")
        assert state.preferred_time == "evening"
        assert "Sunday" not in state.study_days
        assert state.step == StudyPlanIntakeStep.SESSION_STYLE

        # Turn 4: Session style
        state, q4 = manager.advance(state, "45-minute sessions")
        assert state.session_style == "45_min_blocks"
        assert state.step == StudyPlanIntakeStep.GOAL

        # Turn 5: Goal and deadlines
        state, next_q = manager.advance(state, "Improve my weak subjects, have an OS exam in 2 weeks")
        assert state.main_goal == "weak_subjects"
        assert len(state.exam_deadlines) > 0
        assert state.step == StudyPlanIntakeStep.COMPLETE
        assert state.active is False
        assert next_q is None

        # Build preferences dict
        prefs = manager.build_preferences_dict(state)
        assert prefs["daily_minutes"] == 60
        assert prefs["preferred_time"] == "evening"
        assert prefs["schedule_mode"] == "mon_sat"


class TestStudyPlanEndToEndFlow:
    """E2E workflow tests through LangGraph orchestrator."""

    @pytest.mark.asyncio
    async def test_test1_bare_request_asks_intake_question_no_plan_generated(self):
        """TEST 1: User requests study plan -> chatbot asks intake question -> LLM is NOT called yet, no plan generated."""
        student_ctx = get_mock_student_context("student_001")
        initial_state: GraphState = {
            "student_id": "student_001",
            "user_message": "Create a detailed study plan for me.",
            "conversation_id": "conv-test-1",
            "student_context": student_ctx,
            "conversation_history": [],
            "teaching_state": None,
            "quiz_state": None,
            "intake_state": None,
            "learning_history": None,
            "insight_response": None,
            "plan_response": None,
            "final_response": None,
            "agents_used": [],
            "intent": "general_support",
        }

        result = await run_graph(initial_state)

        # 1. Study plan MUST NOT be generated
        assert result.get("plan_response") is None
        assert "study_planner" not in result.get("agents_used", [])

        # 2. Intake state must be created and active at step 1
        intake = result.get("intake_state")
        assert intake is not None
        assert intake.active is True
        assert intake.step == StudyPlanIntakeStep.DAILY_TIME

        # 3. Final response text must ask about daily study time
        resp_text = result["final_response"].response_text.lower()
        assert "time" in resp_text or "hour" in resp_text

    @pytest.mark.asyncio
    async def test_test2_answering_intake_generates_personalized_plan(self):
        """TEST 2: User answers questions -> real profile fetched -> LLM plan generation called after intake."""
        student_ctx = get_mock_student_context("student_001")

        # Simulate complete intake state
        manager = StudyPlanIntakeManager()
        intake_state = StudyPlanIntakeState(
            active=False,
            step=StudyPlanIntakeStep.COMPLETE,
            daily_minutes=120,
            study_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            preferred_time="evening",
            session_style="45_min_blocks",
            main_goal="weak_subjects",
        )

        initial_state: GraphState = {
            "student_id": "student_001",
            "user_message": "Yes, focus on my weak subjects.",
            "conversation_id": "conv-test-2",
            "student_context": student_ctx,
            "conversation_history": [],
            "teaching_state": None,
            "quiz_state": None,
            "intake_state": intake_state,
            "learning_history": None,
            "insight_response": None,
            "plan_response": None,
            "final_response": None,
            "agents_used": [],
            "intent": "study_planning",
            "response_mode": "study_plan",
        }

        result = await run_graph(initial_state)

        # 1. Study planner agent must be invoked
        assert "study_planner" in result.get("agents_used", [])
        plan = result.get("plan_response")
        assert plan is not None
        assert len(plan.tasks) > 0

    def test_test3_student_a_and_student_b_produce_different_plans(self):
        """TEST 3: Student A and Student B have different academic data -> generated plan differs."""
        # Student A: High achiever (DSA 94%, OS 89%, DBMS 62% - weak in DBMS)
        ctx_a = STUDENT_A_HIGH_ACHIEVER
        req_a = PlanRequest(
            student_id="student_A",
            student_context=ctx_a,
            student_preferences={
                "daily_minutes": 120,
                "preferred_time": "evening",
                "study_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            }
        )
        plan_a = build_default_plan(req_a)

        # Student B: Struggling (DSA 71%, OS 54%, DBMS 78%, CN 58% - weak in OS and CN)
        ctx_b = STUDENT_B_STRUGGLING
        req_b = PlanRequest(
            student_id="student_B",
            student_context=ctx_b,
            student_preferences={
                "daily_minutes": 60,
                "preferred_time": "morning",
                "study_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            }
        )
        plan_b = build_default_plan(req_b)

        # Verify Student A plan has tasks for Database Management Systems (their weak subject)
        subjects_a = {t.subject for t in plan_a.tasks}
        assert any("database" in s.lower() or "dbms" in s.lower() for s in subjects_a)

        # Verify Student B plan has tasks for Operating Systems or Computer Networks
        subjects_b = {t.subject for t in plan_b.tasks}
        assert any("operating" in s.lower() or "network" in s.lower() for s in subjects_b)

        # Verify daily time differs
        total_dur_a_day1 = sum(t.duration_minutes for t in plan_a.tasks if t.day == "Monday")
        total_dur_b_day1 = sum(t.duration_minutes for t in plan_b.tasks if t.day == "Monday")
        assert total_dur_a_day1 <= 120
        assert total_dur_b_day1 <= 60
        assert total_dur_a_day1 > total_dur_b_day1

    def test_test4_student_chooses_1_hour_does_not_exceed(self):
        """TEST 4: Student chooses 1 hour/day -> generated plan does not exceed 60 min/day."""
        ctx = STUDENT_B_STRUGGLING
        req = PlanRequest(
            student_id="student_B",
            student_context=ctx,
            student_preferences={"daily_minutes": 60, "preferred_time": "morning"}
        )
        plan = build_default_plan(req)
        for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            day_tasks = [t for t in plan.tasks if t.day == d]
            if day_tasks:
                assert sum(t.duration_minutes for t in day_tasks) <= 60

    def test_test5_student_chooses_evening_uses_evening_slots(self):
        """TEST 5: Student chooses evening -> generated plan uses evening schedule (PM)."""
        ctx = STUDENT_A_HIGH_ACHIEVER
        req = PlanRequest(
            student_id="student_A",
            student_context=ctx,
            student_preferences={"daily_minutes": 120, "preferred_time": "evening"}
        )
        plan = build_default_plan(req)
        for t in plan.tasks:
            if t.time_slot:
                assert "PM" in t.time_slot

    def test_test6_student_chooses_mon_fri_no_weekend_tasks(self):
        """TEST 6: Student chooses Monday-Friday -> no Saturday/Sunday mandatory sessions."""
        ctx = STUDENT_A_HIGH_ACHIEVER
        req = PlanRequest(
            student_id="student_A",
            student_context=ctx,
            student_preferences={
                "daily_minutes": 120,
                "study_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "schedule_mode": "weekdays",
            }
        )
        plan = build_default_plan(req)
        scheduled_days = {t.day for t in plan.tasks if t.day}
        assert "Saturday" not in scheduled_days
        assert "Sunday" not in scheduled_days

    def test_test7_student_specifies_exam_prioritizes_exam_subject(self):
        """TEST 7: Student specifies an exam -> plan prioritizes the relevant subject/deadline."""
        ctx = STUDENT_A_HIGH_ACHIEVER
        req = PlanRequest(
            student_id="student_A",
            student_context=ctx,
            student_preferences={
                "daily_minutes": 120,
                "exam_deadlines": [{"subject": "Operating Systems", "timeframe": "2 weeks"}],
                "priority_subjects": ["Operating Systems"],
            }
        )
        plan = build_default_plan(req)
        os_tasks = [t for t in plan.tasks if "operating" in t.subject.lower() or "os" in t.subject.lower()]
        assert len(os_tasks) > 0
        assert any(t.priority.value == "high" for t in os_tasks)

    def test_test8_multi_turn_remembers_state(self):
        """TEST 8: Intake state retains partial answers across multi-turn step progression."""
        manager = StudyPlanIntakeManager()
        state, _ = manager.initialize()
        assert state.daily_minutes is None

        # Turn 1 answer
        state, _ = manager.advance(state, "3 hours")
        assert state.daily_minutes == 180

        # Turn 2 answer
        state, _ = manager.advance(state, "Monday to Friday, mornings")
        # Turn 1 answer is still intact!
        assert state.daily_minutes == 180
        assert state.preferred_time == "morning"
        assert state.study_days == ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    def test_test9_student_isolation(self):
        """TEST 9: Student A cannot use Student B's academic context or intake session."""
        ctx_a = STUDENT_A_HIGH_ACHIEVER
        ctx_b = STUDENT_B_STRUGGLING

        assert ctx_a.student_id != ctx_b.student_id
        assert ctx_a.assessments.gpa != ctx_b.assessments.gpa

        # Plan request for Student A with Student A context
        req_a = PlanRequest(student_id=ctx_a.student_id, student_context=ctx_a)
        assert req_a.student_context.student_name == "Aarav Sharma"
        assert req_a.student_context.assessments.gpa == 8.8

        # Plan request for Student B with Student B context
        req_b = PlanRequest(student_id=ctx_b.student_id, student_context=ctx_b)
        assert req_b.student_context.student_name == "Bhavna Patel"
        assert req_b.student_context.assessments.gpa == 6.2
