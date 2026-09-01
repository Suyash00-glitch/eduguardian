"""
Recovery Coach Agent Implementation.

The Recovery Coach is the primary student-facing conversational agent in EduGuardian AI.
It consumes student context, academic insight, and study plans to produce an empathetic,
actionable, and non-judgmental response.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from chatbot.backend.schemas.routing import ResponseMode

from chatbot.backend.agents.recovery_coach.prompts import (
    build_recovery_coach_user_prompt,
    build_teach_me_prompt,
    build_quiz_prompt,
    get_system_prompt,
    resolve_student_name,
    get_curated_resources_for_text,
    _detect_format_modifier,
    _detect_math_or_simple_qa,
    _detect_academic_focus_request,
    _detect_progress_request,
    _detect_complex_detailed_request,
    _detect_resource_link_request,
    _detect_direct_task_request,
    _detect_no_extra_constraint,
    _detect_educational_concept,
)
from chatbot.backend.core.memory import (
    UserFacts,
    resolve_user_facts,
    is_name_query,
    is_hometown_query,
    is_ai_origin_query,
    is_system_architecture_query,
    is_existential_user_query,
    is_clarification_user_query,
)
from chatbot.backend.orchestrator.adaptive_quiz import adapt_quiz_difficulty
from chatbot.backend.orchestrator.adaptive_teaching import (
    is_confusion_signal,
    adapt_teaching_support,
    get_strategy_name,
)

from chatbot.backend.schemas.coach import CoachRequest, CoachResponse, CoachMessageItem
from chatbot.backend.schemas.routing import ResponseConstraints
from chatbot.backend.orchestrator.router import detect_constraints
from chatbot.backend.orchestrator.validator import ResponseValidator
from chatbot.backend.llm.base import BaseLLMClient
from chatbot.backend.llm.omniroute import create_llm_client


logger = logging.getLogger(__name__)

# Forbidden terms regex — catches stigmatizing labels that must never reach the student
_FORBIDDEN_TERMS_PATTERN = re.compile(
    r"\b("
    r"high[- ]risk|at[- ]risk|risk level|risk score|dropout risk"
    r"|weak student|dull student|poor student|low[- ]performing student"
    r"|failing student|predicted to fail|failure risk|failure prediction"
    r"|underperformer|academically weak|below[- ]average student"
    r"|support intensity|intensive support|intervention required"
    r"|concerning student|problematic student"
    r")\b",
    re.IGNORECASE,
)


class RecoveryCoachAgent:
    """
    Service class for the Recovery Coach Agent.

    Encapsulates prompt construction, LLM completion, safety post-processing,
    and fallback handling.
    """

    def __init__(self, llm_client: BaseLLMClient | None = None) -> None:
        self._llm_client = llm_client or create_llm_client()

    @staticmethod
    def sanitize_response(text: str) -> str:
        """Post-processes LLM text to ensure no forbidden negative labels or think tags leak to students."""
        cleaned = text
        if "<think>" in cleaned and "</think>" in cleaned:
            cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()
        elif "<think>" in cleaned:
            cleaned = re.sub(r"^<think>.*?(?:\n\n|\Z)", "", cleaned, flags=re.DOTALL).strip()
        cleaned = _FORBIDDEN_TERMS_PATTERN.sub("student with areas to strengthen", cleaned)
        return cleaned

    async def recover(self, request: CoachRequest) -> CoachResponse:
        """Alias for generate_response."""
        return await self.generate_response(request)

    async def generate_response(self, request: CoachRequest) -> CoachResponse:
        """
        Generates the student-facing supportive response.

        Consumes:
            request: CoachRequest (user message, student context, insight, plan, history)
        Returns:
            CoachResponse (supportive response text, attached study plan, quick followups)
        """
        student_id = request.student_id

        # Resolve user facts from memory
        known_name = (request.student_context.student_name or request.student_context.full_name or "").strip() if request.student_context else ""
        user_facts = resolve_user_facts(
            history=request.conversation_history,
            current_message=request.user_message,
            known_name=known_name or request.conversational_name,
        )
        if request.user_facts:
            for k, v in request.user_facts.items():
                if v and not getattr(user_facts, k, None):
                    setattr(user_facts, k, v)

        resolved_name = user_facts.name or ""

        logger.info("RecoveryCoachAgent: Generating response for student_id=%s (name=%s, hometown=%s)", student_id, resolved_name, user_facts.hometown)

        support_intensity = "standard"
        if request.student_insight and request.student_insight.support_intensity:
            support_intensity = request.student_insight.support_intensity

        is_teach_me = (
            getattr(request, "response_mode", None) == "teach_me"
            or (isinstance(request.teaching_state, dict) and request.teaching_state.get("active"))
        )

        is_quiz_mode = (
            getattr(request, "response_mode", None) == "quiz_me"
            or (isinstance(request.quiz_state, dict) and request.quiz_state.get("active"))
        )

        system_prompt = get_system_prompt(support_intensity)
        if is_quiz_mode:
            user_prompt = build_quiz_prompt(request, user_facts, resolved_name, request.quiz_state)
        elif is_teach_me:
            t_dict = dict(request.teaching_state or {})
            student_msg_raw = (request.resolved_user_message or request.user_message).strip()
            # If student expresses confusion or asks for re-explanation, adapt support level
            if is_confusion_signal(student_msg_raw):
                curr_lvl = int(t_dict.get("support_level", 0))
                next_lvl = adapt_teaching_support(curr_lvl, is_confusion=True)
                t_dict["support_level"] = next_lvl
                t_dict["confusion_count"] = int(t_dict.get("confusion_count", 0)) + 1
                t_dict["support_strategy"] = get_strategy_name(next_lvl)
            user_prompt = build_teach_me_prompt(request, user_facts, resolved_name, t_dict)
        else:
            user_prompt = build_recovery_coach_user_prompt(request)
        suggested_followups: list[str] = []

        # Calibrate temperature and token limits dynamically based on format modifier and query complexity
        user_msg = (request.resolved_user_message or request.user_message).lower().strip()
        format_mod = _detect_format_modifier(user_msg)
        constraints_dict = request.constraints or {}
        constraints = ResponseConstraints(**constraints_dict) if constraints_dict else detect_constraints(user_msg)
        no_extra = _detect_no_extra_constraint(user_msg) or format_mod == "no_extra" or constraints.no_extra_text

        is_name_q = is_name_query(user_msg)
        is_hometown_q = is_hometown_query(user_msg)
        is_ai_origin_q = is_ai_origin_query(user_msg)
        is_math = _detect_math_or_simple_qa(user_msg)
        is_focus = _detect_academic_focus_request(user_msg)
        is_progress = _detect_progress_request(user_msg)
        is_resource_link = _detect_resource_link_request(user_msg)
        is_direct_task = _detect_direct_task_request(user_msg)
        is_educational = _detect_educational_concept(user_msg)
        is_complex = _detect_complex_detailed_request(user_msg) or bool(request.study_plan)
        is_greeting = bool(re.search(r"^(?:hi|hii+|hello|hey|good\s+(?:morning|afternoon|evening))\b", user_msg)) and not (user_msg.endswith("?") or is_hometown_q or is_name_q or is_ai_origin_q or is_math or is_educational or is_teach_me or is_quiz_mode)

        is_compound_concept_name = ("operating system" in user_msg or "neural network" in user_msg) and ("name" in user_msg or "who am i" in user_msg)
        learning_prefs = (request.learning_history or {}).get("explicit_preferences", {})
        is_concise_pref = learning_prefs.get("verbosity") == "concise" and not is_complex

        if constraints.exact_word_count and constraints.exact_word_count > 1:
            call_temp = 0.5
            token_limit = max(int(constraints.exact_word_count * 2.2), 800)
        elif constraints.min_word_count and constraints.min_word_count > 50:
            call_temp = 0.5
            token_limit = max(int(constraints.min_word_count * 2.2), 800)
        elif constraints.max_word_count:
            call_temp = 0.2
            token_limit = max(int(constraints.max_word_count * 1.6), 80)
        elif format_mod == "one_word" or constraints.one_word:
            call_temp = 0.0
            token_limit = 10
        elif is_compound_concept_name:
            call_temp = 0.1
            token_limit = 120
        elif is_name_q or is_hometown_q or is_ai_origin_q:
            call_temp = 0.0
            token_limit = 25
        elif is_math:
            call_temp = 0.0
            token_limit = 25
        elif format_mod == "short_direct" or format_mod == "one_sentence" or constraints.one_sentence:
            call_temp = 0.1
            token_limit = 60
        elif is_focus or is_progress:
            call_temp = 0.3
            token_limit = 300
        elif format_mod == "three_points" or constraints.exact_items == 3:
            call_temp = 0.2
            token_limit = 180
        elif is_resource_link or constraints.links_only:
            call_temp = 0.1
            token_limit = 150
        elif is_quiz_mode:
            call_temp = 0.3
            token_limit = 450
        elif is_teach_me:
            call_temp = 0.3
            token_limit = 450
        elif no_extra and is_direct_task:
            call_temp = 0.2
            token_limit = 350
        elif is_direct_task:
            call_temp = 0.3
            token_limit = 500
        elif is_greeting:
            call_temp = 0.2
            token_limit = 40
        elif is_complex:
            call_temp = 0.5
            token_limit = 1024
        elif is_concise_pref:
            call_temp = 0.3
            token_limit = 200
        else:
            call_temp = 0.3
            token_limit = 350

        try:
            # Provide at least 300 max_tokens to accommodate model reasoning/thinking tokens
            actual_max_tokens = max(token_limit, 300)
            raw_text = await self._llm_client.complete_simple(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=call_temp,
                max_tokens=actual_max_tokens,
            )

            # Sanitize and validate response format
            safe_text = self.sanitize_response(raw_text)
            validated_text = ResponseValidator.validate_and_enforce(
                response_text=safe_text,
                constraints=constraints,
                user_facts=user_facts,
            )

            if not validated_text.strip():
                validated_text = self._build_contextual_fallback(
                    request=request,
                    resolved_name=resolved_name,
                    user_facts=user_facts,
                    user_msg=user_msg,
                    constraints=constraints,
                    format_mod=format_mod,
                    is_name_q=is_name_q,
                    is_hometown_q=is_hometown_q,
                    is_focus=is_focus,
                    is_progress=is_progress,
                    is_greeting=is_greeting,
                    is_educational=is_educational,
                    is_quiz_mode=is_quiz_mode,
                )

            logger.info("RecoveryCoachAgent: Generated response (%d chars, validated to %d chars)", len(safe_text), len(validated_text))

            # Determine suggested quick followup prompts only when appropriate (not for 1-word or strict formats)
            suggested_followups = []
            updated_teaching_state: dict[str, Any] | None = None
            updated_quiz_state: dict[str, Any] | None = None

            if is_quiz_mode:
                q_dict = dict(request.quiz_state or {})
                q_dict["active"] = True
                curr_num = int(q_dict.get("current_question_number", 1))
                total_q = int(q_dict.get("total_questions", 5))
                had_active_q = bool(q_dict.get("current_question_text"))

                if had_active_q:
                    # 1. Evaluate previous question answer
                    eval_header = validated_text[:140].lower()
                    if re.search(r"\b(correct|spot on|exactly right|great job|well done|excellent|right!|you got it)\b", eval_header):
                        pts = 1.0
                        is_corr = True
                        eval_enum = "correct"
                    elif re.search(r"\b(partially correct|half right|almost right|part of your answer)\b", eval_header):
                        pts = 0.5
                        is_corr = False
                        eval_enum = "partially_correct"
                    else:
                        pts = 0.0
                        is_corr = False
                        eval_enum = "incorrect"

                    # Mathematically calculate and update score
                    current_score = float(q_dict.get("score", 0.0)) + pts
                    q_dict["score"] = round(current_score, 1)
                    q_dict["last_evaluation"] = eval_enum
                    q_dict["last_student_answer"] = request.user_message

                    # Within-quiz adaptive difficulty progression
                    curr_diff = q_dict.get("difficulty", "beginner")
                    recent_evals = list(q_dict.get("recent_evaluations") or [])
                    next_diff = adapt_quiz_difficulty(curr_diff, is_corr, recent_evals)
                    recent_evals.append(is_corr)
                    q_dict["recent_evaluations"] = recent_evals
                    q_dict["difficulty"] = next_diff.value
                    diff_hist = list(q_dict.get("difficulty_history") or [])
                    diff_hist.append(next_diff.value)
                    q_dict["difficulty_history"] = diff_hist

                    record = {
                        "question_number": curr_num,
                        "question_text": q_dict.get("current_question_text", ""),
                        "question_type": q_dict.get("current_question_type", "multiple_choice"),
                        "student_answer": request.user_message,
                        "is_correct": is_corr,
                        "score_awarded": pts,
                        "explanation": "",
                    }
                    history_list = list(q_dict.get("history") or [])
                    history_list.append(record)
                    q_dict["history"] = history_list

                    if curr_num >= total_q:
                        # Completed!
                        q_dict["step"] = "completed"
                        q_dict["active"] = False
                        q_dict["current_question_text"] = None
                        q_dict["current_options"] = None
                        suggested_followups.extend(["📝 Make me a study plan", "🧠 Quiz me on another topic", "🌱 Teach me another topic"])
                    else:
                        q_dict["current_question_number"] = curr_num + 1

                # If not completed, extract new question & options
                if q_dict.get("step") != "completed":
                    opt_matches = re.findall(r"([A-D]\.\s+[^\n]+)", validated_text)
                    if opt_matches:
                        q_dict["current_options"] = [opt.strip() for opt in opt_matches[:4]]
                        q_dict["current_question_type"] = "multiple_choice"

                    q_match = re.search(r"(Question\s+\d+[^A-D\n]+(?:\n[^\nA-D]+)*?\?)", validated_text, re.IGNORECASE)
                    if q_match:
                        q_dict["current_question_text"] = q_match.group(1).strip()
                    elif "?" in validated_text:
                        parts = validated_text.split("?")
                        q_dict["current_question_text"] = (parts[-2].split("\n")[-1] + "?").strip()

                    q_dict["step"] = "in_progress"
                    q_dict["active"] = True
                    suggested_followups.extend(["A", "B", "C", "D", "🛑 Stop quiz"])

                # Ensure current_correct_answer is NEVER leaked
                q_dict.pop("current_correct_answer", None)
                updated_quiz_state = q_dict

            elif is_teach_me:
                t_dict = dict(request.teaching_state or {})
                t_dict["active"] = True
                t_dict["last_student_answer"] = request.user_message

                # Update adaptive support level and strategy
                student_msg_raw = (request.resolved_user_message or request.user_message).strip()
                if is_confusion_signal(student_msg_raw):
                    curr_lvl = int(t_dict.get("support_level", 0))
                    next_lvl = adapt_teaching_support(curr_lvl, is_confusion=True)
                    t_dict["support_level"] = next_lvl
                    t_dict["confusion_count"] = int(t_dict.get("confusion_count", 0)) + 1
                    t_dict["support_strategy"] = get_strategy_name(next_lvl)
                else:
                    t_dict.setdefault("support_level", 0)
                    t_dict.setdefault("confusion_count", 0)
                    t_dict["support_strategy"] = get_strategy_name(int(t_dict["support_level"]))

                # Extract checking question from output
                all_questions = re.findall(r"(?:^|\n|[.!?]\s+)([^.!?\n]+(?:\?|🧠))", validated_text)
                suggested_followups.append("💡 Explain differently")
                suggested_followups.append("📝 Give me a problem")
                suggested_followups.append("🛑 Stop teaching")

            elif not format_mod and not is_name_q and not is_hometown_q and not is_math and not is_greeting and not constraints.one_word and not constraints.one_sentence and not constraints.no_extra_text:
                if request.study_plan:
                    suggested_followups.append("📋 Show my full timetable")
                    suggested_followups.append("💡 Tips for staying on track")
                elif request.student_context and request.student_context.attendance:
                    suggested_followups.append("🎯 Help me make a study plan")
                    suggested_followups.append("💡 How can I improve my schedule?")

            return CoachResponse(
                response_text=validated_text,
                has_study_plan=request.study_plan is not None,
                study_plan=request.study_plan,
                suggested_followups=suggested_followups,
                resources=request.study_plan.resources if request.study_plan else [],
                teaching_state=updated_teaching_state,
                quiz_state=updated_quiz_state,
                metadata={"support_intensity": support_intensity},
            )

        except Exception as exc:
            logger.warning("RecoveryCoachAgent: Live LLM completion unavailable (%s). Using safe baseline fallback.", exc)
            fallback_text = self._build_contextual_fallback(
                request=request,
                resolved_name=resolved_name,
                user_facts=user_facts,
                user_msg=user_msg,
                constraints=constraints,
                format_mod=format_mod,
                is_name_q=is_name_q,
                is_hometown_q=is_hometown_q,
                is_focus=is_focus,
                is_progress=is_progress,
                is_greeting=is_greeting,
                is_educational=is_educational,
                is_quiz_mode=is_quiz_mode,
            )

            # Validate fallback against format constraints
            constraints_dict = request.constraints or {}
            fallback_constraints = ResponseConstraints(**constraints_dict) if constraints_dict else ResponseConstraints()
            validated_fallback = ResponseValidator.validate_and_enforce(
                response_text=fallback_text,
                constraints=fallback_constraints,
                user_facts=user_facts,
            )

            fallback_teaching_state = request.teaching_state
            if is_teach_me and request.teaching_state:
                t_dict = dict(request.teaching_state or {})
                t_dict["active"] = True
                t_dict["last_student_answer"] = request.user_message
                student_msg_raw = (request.resolved_user_message or request.user_message).strip()
                if is_confusion_signal(student_msg_raw):
                    curr_lvl = int(t_dict.get("support_level", 0))
                    next_lvl = adapt_teaching_support(curr_lvl, is_confusion=True)
                    t_dict["support_level"] = next_lvl
                    t_dict["confusion_count"] = int(t_dict.get("confusion_count", 0)) + 1
                    t_dict["support_strategy"] = get_strategy_name(next_lvl)
                fallback_teaching_state = t_dict

            return CoachResponse(
                response_text=validated_fallback,
                has_study_plan=request.study_plan is not None,
                study_plan=request.study_plan,
                teaching_state=fallback_teaching_state,
                quiz_state=request.quiz_state,
                suggested_followups=suggested_followups or [],
                resources=request.study_plan.resources if request.study_plan else [],
                metadata={"is_fallback": True},
            )

    def _build_contextual_fallback(
        self,
        request: CoachRequest,
        resolved_name: str,
        user_facts: UserFacts,
        user_msg: str,
        constraints: ResponseConstraints,
        format_mod: str | None,
        is_name_q: bool,
        is_hometown_q: bool,
        is_focus: bool,
        is_progress: bool,
        is_greeting: bool,
        is_educational: bool,
        is_quiz_mode: bool,
    ) -> str:
        """Constructs a deterministic, context-aware fallback response when LLM output is unavailable."""
        name_str = f", {resolved_name}" if resolved_name else ""

        # 1. Attached Study Plan Presentation
        if request.study_plan:
            plan_title = request.study_plan.title or "Personalized Study Schedule"
            rationale_str = f" {request.study_plan.rationale}" if getattr(request.study_plan, "rationale", None) else ""
            return (
                f"I've put together a personalized study plan: \"{plan_title}\"! 🎯{rationale_str} "
                "Click on **View Active Study Plan** above to review your schedule and check off tasks as you complete them."
            )

        # 1b. Study Plan Preference Gathering (when student requested a study plan but no preferences were given yet)
        if getattr(request, "response_mode", None) in ("study_plan", ResponseMode.STUDY_PLAN) or any(k in user_msg for k in ["study plan", "timetable", "study schedule", "make me a plan", "create a plan", "detailed plan"]):
            return (
                f"Absolutely{name_str}! I can build a tailored study plan around your actual courses and performance.\n\n"
                "Before I generate your timetable, could you share a few details?\n"
                "1. **Daily Study Time**: How much time can you realistically study each day? (e.g., 1 hour, 2 hours, 3 hours)\n"
                "2. **Preferred Days**: Which days are you available? (e.g., Monday–Friday, Monday–Saturday, Every day)\n"
                "3. **Study Time**: What time of day do you prefer? (Morning, Afternoon, Evening, Night)\n"
                "4. **Main Goal**: What is your primary focus? (e.g., improving weak subjects, exam prep, boosting CGPA, balancing all subjects)\n"
                "5. **Upcoming Deadlines**: Do you have any specific exam dates or assignment deadlines coming up?"
            )

        # 2. Identity Name Inquiry
        if is_name_q:
            if resolved_name:
                return f"{resolved_name}." if format_mod == "one_word" else f"Your name is {resolved_name}."
            return "Unknown." if format_mod == "one_word" else "I don't have your name saved yet."

        # 3. Hometown Inquiry
        if is_hometown_q:
            if user_facts.hometown:
                return f"{user_facts.hometown}." if format_mod == "one_word" else f"You're from {user_facts.hometown}."
            return "I don't have your hometown information yet."

        # 4. Direct Attendance Inquiry
        if any(w in user_msg for w in ["attendance", "attendence"]) and any(kw in user_msg for kw in ["what", "my", "percentage", "how much", "rate", "status"]):
            if request.student_context and request.student_context.attendance and request.student_context.attendance.overall_percentage is not None:
                pct = request.student_context.attendance.overall_percentage
                return f"Your current attendance is {pct:.1f}%."
            return "I don't have your attendance records available right now."

        # 5. Focus Area Inquiry
        if is_focus:
            focus_subj = None
            if request.student_insight and request.student_insight.focus_areas:
                for fa in request.student_insight.focus_areas:
                    if "attendance" not in fa.lower():
                        focus_subj = fa
                        break
            if not focus_subj and request.student_context and request.student_context.subjects:
                sorted_subs = sorted(
                    [s for s in request.student_context.subjects if s.current_marks_percentage is not None or s.marks_percentage is not None],
                    key=lambda x: x.current_marks_percentage if x.current_marks_percentage is not None else (x.marks_percentage or 0),
                )
                if sorted_subs:
                    focus_subj = sorted_subs[0].subject_name
            if focus_subj:
                return f"{focus_subj} would be the main priority right now."
            return "I don't have your academic records available right now to determine a focus subject. Which topic would you like to work on?"

        # 6. Progress Status Inquiry
        if is_progress or any(k in user_msg for k in ["how am i doing", "am i doing well", "my progress", "my performance"]):
            if request.student_insight and request.student_insight.overall_summary:
                return request.student_insight.overall_summary
            if request.student_context and request.student_context.subjects:
                subs_summary = ", ".join([f"{s.subject_name} ({s.current_marks_percentage or s.marks_percentage or 0:.0f}%)" for s in request.student_context.subjects[:3]])
                return f"Here is your current course standing: {subs_summary}."
            return "I don't have your academic performance records available right now. How are you feeling about your current courses?"

        # 7. Emotional Support & Stress Guidance
        if any(k in user_msg for k in ["stress", "anxious", "anxiety", "depress", "depressed", "depression", "overwhelm", "overwhelmed", "worry", "scared", "tired", "hopeless"]):
            return (
                f"It's completely natural to feel challenged when working through demanding subjects{name_str}. "
                "Taking one manageable step at a time and focusing on regular practice will help you build momentum and confidence."
            )

        # 8. Student Self-Doubt, Purpose, Motivation & Open-Ended Conversation
        if any(k in user_msg for k in ["college", "university", "why study", "why will i study", "why am i studying", "worth it", "for me"]):
            return (
                "College can give you a foundation for the career and opportunities you want later, "
                "but it's also okay to question whether what you're studying feels meaningful to you. "
                "If you're unsure about your direction, we can figure out what you're hoping to get from college and work backward from there."
            )

        if any(k in user_msg for k in ["able to study", "capable", "can i improve", "can i really improve", "will i ever", "can i pass", "can i succeed", "can i still do well", "can i recover"]):
            return (
                "Yes, you can improve your ability to study and succeed in your courses. "
                "You don't need to become highly productive overnight—start with one manageable study session today and build consistency from there."
            )

        if any(k in user_msg for k in ["what if i fail", "fear of failing", "afraid of failing", "failing"]):
            return (
                "Worrying about failure is a common feeling when facing demanding academic coursework. "
                "Instead of focusing on the outcome, break down what you need to cover into small, specific topics and tackle them one step at a time."
            )

        if any(k in user_msg for k in ["motivation", "feel like studying", "lost", "don't know what to do", "difficult", "hard"]):
            return (
                f"It's completely natural to have times when studying feels tough or motivation is low{name_str}. "
                "Taking a short break and then restarting with just 15–20 minutes on a single manageable topic can help you regain momentum."
            )

        # 9. Word Count Constraint Fallback
        if constraints.exact_word_count and constraints.exact_word_count > 1:
            name_greeting = f"My name is {resolved_name}." if resolved_name else "I am delighted to stand before you today."
            if "speech" in user_msg or "introduction" in user_msg:
                return (
                    f"Good morning everyone, distinguished faculty members, guests, and fellow students. {name_greeting} "
                    "It is an absolute honor and a genuine privilege to stand before you today as we gather to celebrate new beginnings, academic milestones, and shared aspirations.\n\n"
                    "Education has always been the cornerstone of human progress and personal transformation. As university students, we are not merely here to attend lectures, complete assignments, or prepare for semester examinations. "
                    "Rather, we are here to expand our horizons, question assumptions, develop critical thinking skills, and cultivate the lifelong habits of curiosity, discipline, and perseverance. "
                    "Every lecture we attend, every laboratory experiment we perform, and every discussion we engage in brings us one step closer to mastering our chosen disciplines and contributing meaningfully to society.\n\n"
                    "Throughout our academic journey, we will undoubtedly encounter challenging moments, rigorous coursework, complex problem sets, and demanding deadlines. "
                    "During such times, it is essential to remember that growth occurs precisely at the boundary of our comfort zones. True academic excellence is not defined by effortless perfection, but by our willingness to persist through obstacles, learn from mistakes, and support one another as a cohesive learning community. "
                    "Collaboration, empathy, and mutual encouragement among peers are just as vital as individual study hours and technical acumen.\n\n"
                    "Beyond the classroom, university life presents endless opportunities to build lasting friendships, engage in innovative projects, participate in extracurricular initiatives, and develop leadership capabilities. "
                    "I encourage each of us to take full advantage of these rich resources, seek constructive mentorship from our professors, and remain open to diverse perspectives and innovative paradigms.\n\n"
                    "In closing, let us approach this academic year with enthusiasm, dedication, and an unwavering commitment to excellence. "
                    "Let us strive not only to succeed for ourselves, but to uplift our community and make our university proud. "
                    "Thank you very much for your kind attention, and I wish everyone an inspiring, productive, and memorable semester ahead!"
                )
            return (
                "I am here to assist you with comprehensive academic guidance, structured learning plans, and detailed subject explanations. "
                "Feel free to share your specific coursework topics or exam preparation goals so we can break them down into effective, step-by-step milestones."
            )

        # 10. Format Constraints
        if format_mod == "one_word":
            return resolved_name if (resolved_name and is_name_q) else "Understood."
        if format_mod == "one_sentence":
            return "I am here to support you with your academic questions, study planning, and learning goals."
        if format_mod == "three_points":
            return (
                "• Focus on consistent daily practice in your core courses.\n"
                "• Maintain regular attendance across all scheduled lectures.\n"
                "• Break complex assignments into small, manageable milestones."
            )

        # 11. Greeting Fallback
        if is_greeting or any(k in user_msg for k in ["hi", "hello", "hey", "good morning", "good evening", "greetings"]):
            return f"Hello{name_str}! I'm here to support you with your studies and answer any questions. How can I help you today?"

        # 12. General Student Question / Educational Query
        if is_educational or any(k in user_msg for k in ["study", "course", "subject", "exam", "class", "degree", "learn", "algorithm", "binary tree", "traversal", "sorting", "variable", "python", "data structure", "tree", "network", "system", "code", "explain", "what is"]):
            return "I'm here to support your learning journey, whether you're exploring concepts like data structures and algorithms, building study motivation, or working through your coursework. What specific topic would you like to explore?"

        # 13. Quiz Mode Fallback
        if is_quiz_mode:
            topic_str = request.quiz_state.get("topic", "your studies") if request.quiz_state else "your studies"
            return (
                f"Let's test your understanding of **{topic_str}**! 🧠\n\n"
                f"Question 1:\nWhat is a fundamental property of {topic_str}?\n\n"
                "A. It operates strictly in constant time\n"
                "B. It organizes and structures related computational data\n"
                "C. It only processes alphabetical characters\n"
                "D. It cannot be represented in program memory\n\n"
                "Your answer?"
            )

        # 14. Clarification Fallback (only when truly uninterpretable)
        return "I didn't quite understand what you mean. Are you asking about studying, your academic progress, or something else?"


# ── LangGraph Node Wrapper (for orchestrator execution) ───────────────────────

async def recovery_coach_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node execution wrapper for RecoveryCoachAgent."""
    agent = RecoveryCoachAgent()

    # Adapt GraphState to CoachRequest
    history = state.get("conversation_history", [])
    adapted_history = []
    for m in history:
        role = getattr(m, "role", "user")
        content = getattr(m, "content", str(m))
        adapted_history.append(CoachMessageItem(role=str(role), content=content))

    request = CoachRequest(
        student_id=state.get("student_id", "unknown"),
        user_message=state.get("user_message", ""),
        student_context=state.get("student_context"),
        conversation_history=adapted_history,
        student_insight=state.get("insight_response") or state.get("student_insight"),
        study_plan=state.get("plan_response") or state.get("study_plan"),
        response_mode=state.get("response_mode"),
        conversational_name=state.get("conversational_name"),
        user_facts=state.get("user_facts"),
    )

    response = await agent.generate_response(request)

    return {
        **state,
        "final_response": response,
        "agents_used": state.get("agents_used", []) + ["recovery_coach"],
    }
