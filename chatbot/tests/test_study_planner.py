"""
Unit tests for the Study Planner Agent.

Tests cover:
1. Basic study-plan creation with structured output
2. Personalization reflecting StudentContext and StudentInsight focus areas
3. Urgent deadline prioritization (scheduling nearer deadlines first with High priority)
4. Time constraints handling (e.g. 1 hour per day max duration)
5. Missing deadlines (graceful scheduling without fabricated due dates)
6. Missing student data (handles minimal context without hallucinations)
7. Existing plan revision
8. Positive/neutral student context (advanced prep without assuming struggle)
9. Student-friendly safety check (zero negative labels)
10. Strict schema compliance & serialization round-trip
"""
from __future__ import annotations

import re
import pytest

from chatbot.backend.agents.study_planner.agent import StudyPlannerAgent
from chatbot.backend.schemas.planner import (
    PlanMilestone,
    PlanRequest,
    PriorityLevel,
    StudyPlan,
    StudyTask,
)
from chatbot.backend.schemas.student import (
    AssignmentSummary,
    AttendanceSummary,
    StudentContext,
    SubjectPerformance,
)
from chatbot.backend.schemas.insight import StudentInsight, SubjectInsight

# Regex for safety verification
_JUDGMENTAL_LABELS = re.compile(
    r"\b(dull|lazy|stupid|weak student|failure|incapable|bad student)\b",
    re.IGNORECASE,
)


class FakePlannerLLM:
    """Mock LLM returning valid JSON or custom plan output."""
    def __init__(self, custom_json: str | None = None) -> None:
        self.custom_json = custom_json
        self.last_system_prompt: str | None = None
        self.last_user_prompt: str | None = None

    async def complete_simple(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        if self.custom_json:
            return self.custom_json

        return """```json
{
  "title": "Personalized 7-Day Academic Revision Plan",
  "goals": ["Master Binary Tree Traversals", "Review OS Memory Paging"],
  "priorities": ["Data Structures", "Operating Systems"],
  "week_start": "2026-08-18",
  "tasks": [
    {
      "task_id": "task_1",
      "title": "Tree Traversal Practice",
      "description": "Implement Inorder, Preorder, and Postorder recursion",
      "subject": "Data Structures",
      "day": "Monday",
      "time_slot": "18:00–19:00",
      "duration_minutes": 60,
      "priority": "high",
      "is_completed": false
    },
    {
      "task_id": "task_2",
      "title": "Virtual Memory Chapter Review",
      "description": "Read chapter 8 on virtual memory page tables",
      "subject": "Operating Systems",
      "day": "Tuesday",
      "time_slot": "18:00–19:00",
      "duration_minutes": 60,
      "priority": "medium",
      "is_completed": false
    }
  ],
  "milestones": [
    {
      "milestone_id": "m1",
      "title": "Tree practice set completed",
      "target_day": "Wednesday",
      "is_reached": false
    }
  ],
  "resources": ["Visualgo.net tree animations", "Textbook Ch. 8"],
  "notes": "Short, focused sessions are most effective!",
  "rationale": "Prioritizing Data Structures foundational concepts first."
}
```"""


class TestStudyPlannerAgent:

    @pytest.mark.asyncio
    async def test_1_basic_study_plan_request(self):
        """Basic plan request returns structured StudyPlan with tasks and milestones."""
        fake_llm = FakePlannerLLM()
        agent = StudyPlannerAgent(llm_client=fake_llm)

        ctx = StudentContext(student_id="student_001", student_name="Aisha Raza")
        req = PlanRequest(
            student_id="student_001",
            student_context=ctx,
            user_goal="Create a study plan for this week.",
        )

        plan = await agent.create_plan_async(req)

        assert isinstance(plan, StudyPlan)
        assert len(plan.tasks) >= 2
        assert plan.tasks[0].subject == "Data Structures"
        assert len(plan.milestones) >= 1
        assert not _JUDGMENTAL_LABELS.search(plan.title)

    @pytest.mark.asyncio
    async def test_2_personalized_plan_with_insight(self):
        """Plan reflects focus areas identified in StudentInsight."""
        fake_llm = FakePlannerLLM()
        agent = StudyPlannerAgent(llm_client=fake_llm)

        ctx = StudentContext(
            student_id="student_002",
            student_name="Devin",
            subjects=[
                SubjectPerformance(subject_name="Discrete Math", current_marks_percentage=52.0),
                SubjectPerformance(subject_name="Operating Systems", current_marks_percentage=85.0),
            ],
        )
        insight = StudentInsight(
            student_id="student_002",
            overall_summary="Solid OS standing; Discrete Math needs practice.",
            strengths=["Operating Systems"],
            focus_areas=["Discrete Math"],
            recommended_areas_of_attention=["Graph Theory", "Set Induction"],
        )

        req = PlanRequest(
            student_id="student_002",
            student_context=ctx,
            student_insight=insight,
            user_goal="Help me prepare my schedule.",
        )

        await agent.create_plan_async(req)

        # Verify prompt contained the insight focus areas
        assert "Discrete Math" in fake_llm.last_user_prompt
        assert "Graph Theory" in fake_llm.last_user_prompt

    def test_3_deadline_prioritization(self):
        """Deterministic builder prioritizes urgent deadlines with High priority."""
        agent = StudyPlannerAgent()

        ctx = StudentContext(
            student_id="student_003",
            student_name="Samir",
            assignments=AssignmentSummary(
                total_assigned=5,
                total_submitted=3,
                upcoming_deadlines=[
                    {"title": "Algorithms Lab 3", "subject": "Algorithms", "due_date": "Tomorrow", "priority": "High"},
                    {"title": "History Essay", "subject": "History", "due_date": "Next Friday", "priority": "Low"},
                ],
            ),
        )

        req = PlanRequest(
            student_id="student_003",
            student_context=ctx,
            user_goal="Make me a plan",
        )

        plan = agent.create_plan(req)

        assert len(plan.tasks) > 0
        first_task = plan.tasks[0]
        assert "Algorithms Lab 3" in first_task.title
        assert first_task.priority == PriorityLevel.HIGH

    def test_4_limited_study_time_constraint(self):
        """When user says '1 hour per day', tasks are capped to max 60 minutes."""
        agent = StudyPlannerAgent()

        ctx = StudentContext(
            student_id="student_004",
            student_name="Priya",
            subjects=[SubjectPerformance(subject_name="Physics")],
        )

        req = PlanRequest(
            student_id="student_004",
            student_context=ctx,
            user_goal="I only have 1 hour per day to study",
        )

        plan = agent.create_plan(req)

        for task in plan.tasks:
            assert task.duration_minutes <= 60

    def test_5_missing_deadlines_handled_gracefully(self):
        """When no upcoming deadlines exist, planner schedules topics without fabricated due dates."""
        agent = StudyPlannerAgent()

        ctx = StudentContext(
            student_id="student_005",
            student_name="Elena",
            subjects=[SubjectPerformance(subject_name="Chemistry")],
            assignments=AssignmentSummary(total_assigned=2, total_submitted=2, upcoming_deadlines=[]),
        )

        req = PlanRequest(student_id="student_005", student_context=ctx)
        plan = agent.create_plan(req)

        assert len(plan.tasks) > 0
        assert plan.tasks[0].subject == "Chemistry"

    def test_6_missing_student_data_handled(self):
        """Minimal student context produces a realistic general plan without hallucinations."""
        agent = StudyPlannerAgent()

        ctx = StudentContext(student_id="student_006", student_name="Jordan")
        req = PlanRequest(student_id="student_006", student_context=ctx)

        plan = agent.create_plan(req)

        assert isinstance(plan, StudyPlan)
        assert len(plan.tasks) > 0
        assert plan.week_start is not None

    @pytest.mark.asyncio
    async def test_7_existing_plan_revision(self):
        """Existing plan context is passed into prompt when adjusting schedule."""
        fake_llm = FakePlannerLLM()
        agent = StudyPlannerAgent(llm_client=fake_llm)

        ctx = StudentContext(student_id="student_007", student_name="Maya")
        existing = StudyPlan(
            title="Original Week Plan",
            tasks=[
                StudyTask(title="Task 1 Done", subject="Math", is_completed=True),
                StudyTask(title="Task 2 Pending", subject="Math", is_completed=False),
            ],
        )

        req = PlanRequest(
            student_id="student_007",
            student_context=ctx,
            existing_plan=existing,
            user_goal="I couldn't finish Monday's tasks, can you adjust my plan?",
        )

        await agent.create_plan_async(req)

        assert "Original Week Plan" in fake_llm.last_user_prompt
        assert "Task 1 Done" in fake_llm.last_user_prompt

    def test_8_positive_neutral_student_context(self):
        """High-performing student context produces an advanced mastery schedule."""
        agent = StudyPlannerAgent()

        ctx = StudentContext(
            student_id="student_008",
            student_name="Rahul",
            subjects=[
                SubjectPerformance(subject_name="Machine Learning", current_marks_percentage=92.0, grade="A+"),
            ],
        )

        req = PlanRequest(
            student_id="student_008",
            student_context=ctx,
            user_goal="Advanced preparation for Machine Learning finals",
        )

        plan = agent.create_plan(req)

        assert plan.priorities[0] == "Machine Learning"
        assert not _JUDGMENTAL_LABELS.search(plan.rationale or "")

    def test_9_zero_judgmental_labels(self):
        """Plan notes, goals, and descriptions contain zero negative labels."""
        agent = StudyPlannerAgent()

        ctx = StudentContext(
            student_id="student_009",
            student_name="Challenged Student",
            subjects=[SubjectPerformance(subject_name="Calculus", current_marks_percentage=40.0)],
        )

        req = PlanRequest(student_id="student_009", student_context=ctx)
        plan = agent.create_plan(req)

        full_text = f"{plan.title} {' '.join(plan.goals)} {plan.notes or ''} {plan.rationale or ''}"
        for t in plan.tasks:
            full_text += f" {t.title} {t.description}"

        assert not _JUDGMENTAL_LABELS.search(full_text)

    def test_10_schema_roundtrip_validation(self):
        """Generated StudyPlan validates cleanly via JSON round-trip."""
        agent = StudyPlannerAgent()

        ctx = StudentContext(
            student_id="student_010",
            student_name="Test Student",
            subjects=[SubjectPerformance(subject_name="Databases")],
        )

        req = PlanRequest(student_id="student_010", student_context=ctx)
        plan = agent.create_plan(req)

        json_data = plan.model_dump_json()
        restored = StudyPlan.model_validate_json(json_data)

        assert restored.plan_id == plan.plan_id
        assert len(restored.tasks) == len(plan.tasks)
        assert restored.tasks[0].priority in (PriorityLevel.HIGH, PriorityLevel.MEDIUM, PriorityLevel.LOW)
