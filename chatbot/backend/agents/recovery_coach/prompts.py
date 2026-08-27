"""
Recovery Coach Agent — LLM Prompt Templates & Context Formatters.

This module governs the primary student-facing conversational voice of EduGuardian AI.
It implements strict response-mode dispatching, context isolation, and robust fact memory.
"""
from __future__ import annotations

import re
from typing import Any

from chatbot.backend.schemas.coach import CoachRequest, CoachMessageItem
from chatbot.backend.schemas.student import StudentContext
from chatbot.backend.schemas.insight import StudentInsight
from chatbot.backend.schemas.planner import StudyPlan
from chatbot.backend.schemas.routing import ResponseMode, ResponseConstraints
from chatbot.backend.orchestrator.router import detect_constraints
from chatbot.backend.core.memory import (
    UserFacts,
    resolve_user_facts,
    is_name_query,
    is_hometown_query,
    is_ai_origin_query,
    extract_name,
    extract_hometown,
    extract_location,
)


# ── System Prompt ──────────────────────────────────────────────────────────────

RECOVERY_COACH_SYSTEM_PROMPT = """\
You are the student-facing conversational coach for EduGuardian. Your role is to understand the student's actual question and respond naturally, supportively, and constructively. You can discuss academic learning, motivation, uncertainty, study difficulties, goals, confidence, planning, general student concerns, and other questions relevant to the student's situation. Use the student's provided context when it is relevant, but do not unnecessarily mention academic metrics or internal assessments. Never invent student information. Never expose internal risk classifications. Do not diagnose mental-health conditions. Answer the question the student actually asked.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORE BEHAVIOR RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ANSWER WHAT IS ASKED:
   • Factual questions (e.g. "What is the capital of India?") → Direct factual answer ("New Delhi.").
   • Identity/name questions (e.g. "Who am I?", "What's my name?"):
     - If name is known: Direct name ("Ajmal.").
     - If name is unknown: "I don't have your name saved yet." NEVER invent or guess a name.
   • Hometown/origin questions (e.g. "Where am I from?"):
     - If hometown is known: State it directly ("Mangalore." or "You're from Mangalore.").
     - If hometown is unknown: "I don't have your hometown information yet."
   • System capability / Agents questions (e.g. "Which agents do I have?"):
     - List the three agents: Student Insight Agent, Study Planner Agent, and Recovery Coach Agent.
   • General student conversation (e.g. "Why am I studying college?", "Will I be able to study?", "What if I fail?", "How do I stay motivated?"):
     - Respond naturally, empathetically, and constructively. Provide thoughtful perspective, encourage healthy study habits, and address the core concern without preaching or dumping metrics.
   • Concept questions (e.g. "What is an operating system?") → Direct educational explanation without unsolicited study plans.
   • Explicit task/plan requests (e.g. "Make me a study plan") → Provide structured schedule or learning steps.

2. CONTEXTUAL EMOJI USAGE & WARMTH:
   • You may use several contextually appropriate emojis throughout your response to make conversations warmer, friendlier, and more emotionally connected for students.
   • Place emojis naturally at meaningful points as visual anchors throughout your paragraphs rather than placing an emoji after every sentence or dumping them in clusters.
   • Target Emoji Frequency:
     - Normal conversational / multi-paragraph responses: ~3–6 contextual emojis.
     - Short responses: ~1–3 emojis.
     - Emotional / supportive conversations: ~2–5 warm, empathetic emojis (e.g., ❤️, 🌱, 🎯, 💪, ✨).
     - Educational explanations: ~1–3 relevant concept emojis (e.g., 🧠, 💡, 📚, ✍️, 🔍).
     - Celebrations / achievements: ~2–4 celebratory emojis (e.g., 🎉, 🥳, 🏆, ⭐).
     - Factual / direct identity questions: 0 emojis (clean, direct text).
   • Contextual Category Alignment:
     - Learning & Ideas: 📚, 🧠, 💡, ✍️, 🔍
     - Studying & Practice: 📖, 📚, 📝, ✏️
     - Planning & Time: 🎯, 🗓️, ⏰, ⏱️
     - Progress & Growth: 📈, 🌱, 💪, ⭐
     - Motivation & Confidence: 💪, 🔥, 🚀, ✨
     - Support & Empathy: ❤️, 🤝, 🌱
     - Rest & Breaks: ☕, 🌿, 😌
   • Boundaries & Quality Rules:
     - Emojis must directly match the sentence meaning:
       * "Let's create a study plan" → 🎯🗓️
       * "Practice problems" → 📝🧠
       * "You're making progress" → 📈🌱💪
       * "That's a great achievement!" → 🎉🏆⭐
       * "Take a short break" → ☕🌿
       * "I understand how you feel" → ❤️🤝
     - AVOID emoji clusters (never put 5+ emojis in a row like "📚🧠💪🌱✨🎯🔥🚀").
     - NEVER put an emoji after every single sentence.
     - NEVER use celebratory emojis for sad conversations or crying emojis simply because a student is discussing a difficulty.
     - NEVER use emojis for risk scores, failure labels, or internal assessments.
     - Serious emotional situations should remain warm and respectful rather than overly playful.

3. EXPLICIT FORMAT CONSTRAINTS OVERRIDE EVERYTHING:
   • "in 1 word" / "in one word" → Output EXACTLY 1 single word (NO emoji, NO extra text).
   • "no emojis" / "without emojis" → Output ZERO emojis.
   • "professional" / "formal" → Use minimal or ZERO emojis.
   • "just give me the answer" / direct → Keep response concise without unnecessary emoji decoration.
   • "in 1 line" / "in 1 sentence" → Output EXACTLY 1 single sentence.
   • "give me 3" / "3 points" → Output EXACTLY 3 bullet points / items.
   • "no extra text" / "don't bluff" / "links only" → Output ONLY the requested content with ZERO extra commentary.

4. CONVERSATION MEMORY & USER FACTS:
   • Remember user facts (name, hometown) when shared in conversation.
   • Questions NEVER overwrite or erase user facts.
   • NEVER invent or hallucinate student names.

5. ACADEMIC CONTEXT IS RELEVANCE-BASED:
   • Only refer to student grades, attendance, or course standing when it is directly relevant to answering the student's question.
   • Do NOT dump raw metrics on general questions or identity questions.

6. FORBIDDEN BEHAVIORS:
   • NEVER diagnose mental health conditions.
   • NEVER label the student ("weak", "at-risk", "failing", "incapable").
   • NEVER use generic canned brush-offs ("I'm here to help you with your academic questions, study planning, and coursework. What would you like to work on?").
   • Answer the student's actual question.

TONE: Natural, warm, empathetic, constructive, and direct.
"""


RECOVERY_COACH_INTENSIVE_PROMPT = RECOVERY_COACH_SYSTEM_PROMPT + """\

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADDITIONAL GUIDANCE FOR THIS STUDENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This student may be feeling overwhelmed.
- Acknowledge their feeling warmly in 1 short sentence.
- Give 1 small, manageable win to build momentum.
- Keep the response short (40–80 words).
"""


def resolve_student_name(request: CoachRequest) -> str:
    """Helper returning the resolved student name from request context or memory."""
    if request.conversational_name:
        return request.conversational_name
    if request.user_facts and request.user_facts.get("name"):
        return request.user_facts["name"]
    if request.student_context:
        name_val = (request.student_context.student_name or request.student_context.full_name or "").strip()
        if name_val and name_val.lower() not in {"student", "test student", "unknown", "there", ""}:
            return name_val.split()[0].capitalize()
    return ""


# ── Context Formatters ─────────────────────────────────────────────────────────

def format_student_context_section(
    context: StudentContext | None,
    inject: bool = True,
    resolved_name: str = "",
    user_facts: UserFacts | None = None,
) -> str:
    """Formats student academic context for the LLM when relevant."""
    if not context or not inject:
        return (
            "STUDENT ACADEMIC CONTEXT: Not injected for this request type.\n"
            "Answer the student's question directly without referencing academic records."
        )

    display_name = resolved_name or (context.student_name or context.full_name or "Student")
    lines = [
        "── STUDENT ACADEMIC CONTEXT (Ground Truth from University Portal) ──",
        f"Name: {display_name}",
    ]

    if user_facts and user_facts.hometown:
        lines.append(f"Hometown / Origin: {user_facts.hometown}")
    if user_facts and user_facts.location:
        lines.append(f"Current Location: {user_facts.location}")

    if context.department:
        lines.append(f"Program/Department: {context.department}")
    if context.year_of_study:
        lines.append(f"Year of Study: Year {context.year_of_study}")

    if context.attendance and context.attendance.overall_percentage is not None:
        pct = context.attendance.overall_percentage
        trend = context.attendance.trend or "stable"
        lines.append(f"Attendance: {pct:.1f}% (trend: {trend})")
        if context.attendance.subjects_below_threshold:
            lines.append(f"  Courses with low attendance: {', '.join(context.attendance.subjects_below_threshold)}")

    if context.subjects:
        lines.append("Subject Performance:")
        for s in context.subjects:
            pct_val = s.current_marks_percentage or s.marks_percentage
            info = f"  {s.subject_name}"
            if pct_val is not None:
                info += f": {pct_val:.0f}%"
                if s.grade:
                    info += f" (Grade: {s.grade})"
            lines.append(info)

    if context.assignments:
        total = context.assignments.total_assigned or 1
        submitted = context.assignments.total_submitted or 0
        rate = (submitted / total) * 100
        pending = context.assignments.pending_count or 0
        lines.append(f"Assignments: {submitted}/{total} submitted ({rate:.0f}% completion, {pending} pending)")

    if context.historical_academic_performance:
        hp = context.historical_academic_performance
        cgpa = hp.get("cgpa")
        latest_sgpa = hp.get("latest_sgpa")
        trend = hp.get("sgpa_trend")
        sems = hp.get("total_semesters_completed")
        credits_earned = hp.get("total_credits_earned")
        arrears = hp.get("arrears_count") or 0

        lines.append("Authoritative Historical Academic Performance (Student Portal Ground Truth):")
        if cgpa is not None:
            lines.append(f"  • Cumulative GPA (CGPA): {cgpa}")
        if latest_sgpa is not None:
            sem_note = f" (from Semester {sems})" if sems else ""
            lines.append(f"  • Latest Semester SGPA: {latest_sgpa}{sem_note}")
        if trend:
            lines.append(f"  • Academic Trajectory: {trend}")
        if sems:
            lines.append(f"  • Completed Semesters: {sems}")
        if credits_earned is not None:
            lines.append(f"  • Total Credits Earned: {credits_earned}")
        lines.append(f"  • Active Backlogs / Arrears: {arrears}")

    return "\n".join(lines)


def format_student_insight_section(insight: StudentInsight | None, inject: bool = True) -> str:
    """Formats internal Student Insight Agent output as coaching guidance."""
    if not insight or not inject:
        return (
            "INTERNAL ACADEMIC INSIGHT: Not injected for this request type. "
            "Answer the student's question directly."
        )

    lines = [
        "── INTERNAL ACADEMIC INSIGHT (Use this to shape your response — do NOT quote directly) ──",
    ]
    if insight.overall_summary:
        lines.append(f"Internal summary: {insight.overall_summary}")
    if insight.strengths:
        lines.append(f"Student's STRENGTHS (celebrate these): {', '.join(insight.strengths)}")
    if insight.focus_areas:
        lines.append(f"FOCUS AREAS (prioritize 1–2 max): {', '.join(insight.focus_areas)}")
    if insight.recommended_areas_of_attention:
        lines.append(f"Recommended attention areas: {', '.join(insight.recommended_areas_of_attention)}")

    return "\n".join(lines)


def format_study_plan_section(plan: StudyPlan | None) -> str:
    """Formats structured study plan into context for natural introduction."""
    if not plan:
        return "STUDY PLAN: No structured plan generated for this turn."

    lines = [
        f"── GENERATED STUDY PLAN: \"{plan.title}\" ──",
        f"Tasks scheduled: {len(plan.tasks)}",
    ]
    if plan.goals:
        lines.append(f"Goals: {', '.join(plan.goals)}")
    if plan.priorities:
        lines.append(f"Priorities: {', '.join(plan.priorities)}")
    if plan.notes:
        lines.append(f"Strategy note: {plan.notes}")
    lines.append(
        "\n[Instruction: Introduce this plan warmly. Mention the first 1–2 tasks naturally. "
        "Encourage the student to open the plan and start with the first step.]"
    )
    return "\n".join(lines)


def format_conversation_history_section(history: list, resolved_name: str = "") -> str:
    """Formats recent message turns into conversation context with clear participant names."""
    if not history:
        return "CONVERSATION HISTORY: No prior messages in this session."

    user_label = resolved_name if resolved_name else "Student"
    lines = ["Recent Conversation History (for context continuity):"]
    for msg in history[-8:]:  # Last 4 turns
        role = getattr(msg, "role", "user")
        role_str = str(role).lower()
        speaker = user_label if ("user" in role_str) else "EduGuardian"
        content = getattr(msg, "content", str(msg))
        lines.append(f"  {speaker}: {content}")

    return "\n".join(lines)


def format_learning_context_section(
    learning_history: dict[str, Any] | None,
    user_message: str,
) -> str | None:
    """
    Constructs a compact, token-efficient learning context block (< 50 tokens)
    for Recovery Coach prompts. Only relevant topic signals and active preferences are injected.
    """
    if not learning_history or not isinstance(learning_history, dict):
        return None

    msg_lower = user_message.lower()
    mastered = learning_history.get("mastered_topics") or []
    needs_practice = learning_history.get("needs_practice_topics") or []
    prefs = learning_history.get("explicit_preferences") or {}

    lines = []

    # 1. Topic-Level Adaptation (Only if current question is relevant to known topics)
    matched_mastered = [t for t in mastered if str(t).lower() in msg_lower]
    matched_needs_practice = [t for t in needs_practice if str(t).lower() in msg_lower]

    if matched_mastered:
        lines.append(f"Mastered Topic Focus ({', '.join(matched_mastered)}): Student has solid foundation here. Feel free to include practical nuances, trade-offs, or deeper insights naturally.")
    elif matched_needs_practice:
        lines.append(f"Reinforcement Topic Focus ({', '.join(matched_needs_practice)}): Student is building confidence here. Explain core concepts simply with intuitive analogies and clear 1-line examples.")

    # 2. Explicit Preferences (Respected unless overridden by current request)
    is_detail_override = bool(re.search(r"\b(?:in\s+detail|detailed|elaborate|deep\s+dive|thorough|complete\s+guide|roadmap|explain\s+in\s+depth)\b", msg_lower))
    is_def_override = bool(re.search(r"\b(?:just\s+(?:give\s+me\s+)?(?:the\s+)?definition|definition\s+only|only\s+define|define\s+only|just\s+define)\b", msg_lower))

    pref_directives = []
    if "verbosity" in prefs:
        v = prefs["verbosity"]
        if v == "concise" and not is_detail_override:
            pref_directives.append("Keep response concise and direct.")
        elif v == "detailed":
            pref_directives.append("Provide a thorough, detailed explanation.")

    if "explanation_style" in prefs:
        style = prefs["explanation_style"]
        if style == "examples" and not is_def_override:
            pref_directives.append("Use concrete examples to explain concepts.")
        elif style == "step_by_step":
            pref_directives.append("Structure explanations sequentially step-by-step.")
        elif style == "simple":
            pref_directives.append("Use simple, accessible language.")

    if "code_language" in prefs:
        lang = prefs["code_language"]
        pref_directives.append(f"Use {lang} for code examples when code is helpful.")

    if pref_directives:
        lines.append("Active Learning Preferences: " + " ".join(pref_directives))

    if not lines:
        return None

    return (
        "── STUDENT LEARNING CONTEXT (Internal personalization — never quote verbatim) ──\n"
        + "\n".join(lines)
    )


# ── Request Type Detectors ─────────────────────────────────────────────────────

def _detect_identity_request(message: str) -> bool:
    """Backwards-compatible helper returning True if user is asking for identity/profile info."""
    return is_name_query(message) or is_hometown_query(message)


def _detect_format_modifier(message: str) -> str | None:

    """Detects explicit format or brevity modifiers in user message."""
    msg_clean = message.lower().strip().rstrip(".?!")

    if re.search(r"\b(in\s+)?(1|one)\s+word\b|\bonly\s+the\s+name\b|\bjust\s+the\s+name\b|\bsingle\s+word\b", msg_clean):
        return "one_word"

    if re.search(r"\b(in\s+)?(1|one)\s+(sentence|line)\b|\bsingle\s+sentence\b", msg_clean):
        return "one_sentence"

    if re.search(r"\b(give\s+me\s+)?(3|three)\s+(points|ways|tips|steps|bullets|videos|links)\b", msg_clean):
        return "three_points"

    if re.search(r"\b(no\s+extra\s+text|don'?t\s+give\s+(me\s+)?extra\s+text|no\s+bluff|don'?t\s+bluff|links\s+only|just\s+the\s+links|without\s+extra\s+text)\b", msg_clean):
        return "no_extra"

    if re.search(r"\b(shorter|short\s+answer|briefly|just\s+the\s+answer|don'?t\s+explain|yes\s+or\s+no|just\s+answer|direct\s+answer)\b", msg_clean):
        return "short_direct"

    return None


def _detect_no_extra_constraint(message: str) -> bool:
    """Returns True if message explicitly forbids extra text/explanation."""
    msg_clean = message.lower()
    return bool(re.search(
        r"(no\s+extra\s+text|don'?t\s+give\s+(me\s+)?extra|no\s+bluff|don'?t\s+bluff|"
        r"no\s+explanation|links\s+only|without\s+extra|just\s+answer|direct\s+answer|"
        r"only\s+answer|nothing\s+else|no\s+other\s+text|don'?t\s+add\s+anything)",
        msg_clean,
    ))


def _detect_math_or_simple_qa(message: str) -> bool:
    """Returns True if the message is a simple arithmetic or direct educational definition question."""
    msg_clean = message.lower().strip().rstrip("?.!")
    if re.match(r"^(\d+\s*[\+\-\*\/]\s*\d+|what\s+is\s+\d+\s*[\+\-\*\/]\s*\d+)$", msg_clean):
        return True
    if re.search(r"\b(capital\s+of|what\s+is\s+the\s+capital\s+of|population\s+of)\b", msg_clean):
        return True
    if re.search(r"\b(what\s+is\s+a\s+stack|what\s+is\s+a\s+queue|what\s+is\s+recursion|define\s+recursion|define\s+stack)\b", msg_clean):
        return True
    return False


def _detect_academic_focus_request(message: str) -> bool:
    """Returns True if asking which subject or topic to prioritize."""
    msg_clean = message.lower().strip().rstrip("?.!")
    return bool(re.search(r"\b(which\s+subject(\s+should\s+i\s+focus\s+on)?|what\s+should\s+i\s+focus\s+on|where\s+should\s+i\s+focus|my\s+priority\s+subject|top\s+subject)\b", msg_clean))


def _detect_progress_request(message: str) -> bool:
    """Returns True if asking general status or how am I doing."""
    msg_clean = message.lower().strip().rstrip("?.!")
    if "study plan" in msg_clean or "plan" in msg_clean or "schedule" in msg_clean:
        return False
    return bool(re.search(r"\b(am\s+i\s+doing\s+well|how\s+am\s+i\s+doing|how\s+is\s+my\s+progress|my\s+performance|my\s+standing|how\s+am\s+i\s+performing|how\s+am\s+i\s+doing\s+academically|show\s+me\s+my\s+marks)\b", msg_clean))



def _detect_academic_improvement_request(message: str) -> bool:
    """Returns True if asking how to improve in general or in a specific subject."""
    msg_clean = message.lower().strip().rstrip("?.!")
    return bool(re.search(r"\b(how\s+can\s+i\s+improve|how\s+to\s+improve|improve\s+my\s+data\s+structures|improve\s+my\s+attendance|ways\s+to\s+improve)\b", msg_clean))


def _detect_explicit_data_request(message: str) -> bool:
    """Returns True if asking for a specific numerical academic record (CGPA, SGPA, attendance, marks)."""
    msg_lower = message.lower()
    keywords = [
        "what is my attendance", "what's my attendance", "my attendance percentage",
        "what is my score", "what's my score", "what are my marks", "my grades",
        "what is my cgpa", "what's my cgpa", "my cgpa", "tell me my cgpa",
        "what is my sgpa", "what's my sgpa", "my sgpa", "my latest sgpa", "latest sgpa",
        "my credits", "how many credits", "my backlogs", "do i have backlogs",
    ]
    return any(kw in msg_lower for kw in keywords)


def _detect_emotional_message(message: str) -> bool:
    """Returns True if student expresses emotional distress."""
    msg_lower = message.lower()
    keywords = [
        "stress", "anxious", "overwhelm", "worry", "scared", "tired",
        "not good at", "can't understand", "failing", "behind", "lost",
        "hopeless", "give up", "can't do this", "impossible", "stupid", "dumb",
        "feel like i'm not", "feel like i am not", "i am bad", "i'm bad", "hard time",
    ]
    return any(kw in msg_lower for kw in keywords)


def _detect_resource_link_request(message: str) -> bool:
    """Returns True if asking for video links or online resources."""
    msg_clean = message.lower()
    return bool(re.search(
        r"\b(youtube|yt|video|videos|link|links|url|urls|resource|resources|"
        r"give\s+me\s+link|send\s+me\s+link|find\s+me\s+link|playlist)\b",
        msg_clean,
    ))


def _detect_direct_task_request(message: str) -> bool:
    """Returns True if message is a learning plan or task request."""
    msg_clean = message.lower().strip()
    return bool(re.search(
        r"\b(give\s+me\s+a\s+plan|i\s+want\s+to\s+learn|help\s+me\s+learn|"
        r"teach\s+me|how\s+do\s+i\s+learn|learning\s+path|learning\s+plan|"
        r"roadmap|steps\s+to\s+learn|how\s+to\s+start|where\s+to\s+start|"
        r"list\s+the\s+steps|list\s+the\s+topics|break\s+it\s+down)\b",
        msg_clean,
    ))


def _detect_complex_detailed_request(message: str) -> bool:
    """Returns True if asking for a detailed/in-depth explanation."""
    msg_clean = message.lower().strip()
    return bool(re.search(
        r"\b(detailed|in\s+detail|comprehensive|deep\s+dive|in-depth|explain\s+.+\s+in\s+detail)\b",
        msg_clean,
    ))


def _detect_educational_concept(message: str) -> bool:
    """Returns True if message is asking to define or explain an academic or technical concept."""
    msg_clean = message.lower().strip()
    return bool(re.search(
        r"\b("
        r"what\s+is\s+(?!my\b|the\s+capital|attendance|score|grade|mark)|"
        r"what\s+are\s+(?!my\b)|"
        r"explain|how\s+does|how\s+do|define\s+(?!my)|"
        r"tell\s+me\s+about|describe|overview\s+of|"
        r"difference\s+between|compare|neural\s+network|operating\s+system"
        r")\b",
        msg_clean,
    ))


# ── Curated Educational Links ──────────────────────────────────────────────────

CURATED_TOPIC_RESOURCES = {
    "neural network": [
        "https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi (3Blue1Brown - Neural Networks)",
        "https://www.youtube.com/watch?v=VMj-3S1tku0 (Andrej Karpathy - Neural Networks: Zero to Hero)",
        "https://www.youtube.com/watch?v=CqOfi41LfDw (StatQuest - Neural Networks)",
    ],
    "data structures": [
        "https://www.youtube.com/watch?v=RBSGKlAnoiM (freeCodeCamp - Data Structures Course)",
        "https://www.youtube.com/watch?v=pkYVOmU3MgA (Abdul Bari - Algorithms & Data Structures)",
        "https://www.youtube.com/watch?v=8hly31xKli0 (CS50 - Data Structures)",
    ],
    "dbms": [
        "https://www.youtube.com/watch?v=HXV3zeQKqGY (freeCodeCamp - SQL & Database Design)",
        "https://www.youtube.com/watch?v=ztHopE5Wnpc (Kiran Academy - DBMS Full Course)",
    ],
    "operating systems": [
        "https://www.youtube.com/watch?v=26QPDBe-NB8 (Neso Academy - Operating Systems)",
        "https://www.youtube.com/watch?v=vBURTt97EkA (freeCodeCamp - Operating Systems)",
    ],
}


def get_curated_resources_for_text(text: str) -> list[str]:
    """Returns curated YouTube/resource links matching keywords in text."""
    text_lower = text.lower()
    for topic, links in CURATED_TOPIC_RESOURCES.items():
        if topic in text_lower:
            return links
    return [
        "https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi",
        "https://www.youtube.com/watch?v=VMj-3S1tku0",
        "https://www.youtube.com/watch?v=CqOfi41LfDw",
    ]


def _detect_celebration_message(msg: str) -> bool:
    """Detects student celebration, high marks, or academic achievements."""
    msg_l = msg.lower()
    return any(k in msg_l for k in [
        "good marks", "good score", "got good marks", "got great marks", "high marks",
        "passed my exam", "cleared my exam", "scored well", "highest marks",
        "aced the test", "aced my exam", "did well in exam", "did well in test",
        "i did great", "i succeeded"
    ])


def _detect_study_method_request(msg: str) -> bool:
    """Detects inquiries asking how to study, study techniques, tips, or study routines."""
    msg_l = msg.lower()
    return any(k in msg_l for k in [
        "how to study", "how should i study", "tips to study", "study technique",
        "best way to study", "study tips", "study advice", "how do i study",
        "how can i study", "effective studying", "study better", "study method"
    ])


# ── Main Prompt Builder ────────────────────────────────────────────────────────

def build_recovery_coach_user_prompt(request: CoachRequest) -> str:
    """
    Constructs the target user prompt for the Recovery Coach LLM call.
    Applies strict context separation, fact memory, and mode-targeted instructions.
    """
    msg = (request.resolved_user_message or request.user_message).strip()
    msg_l = msg.lower()

    # 1. Resolve user facts from memory
    existing_name = (request.student_context.student_name or request.student_context.full_name or "").strip() if request.student_context else ""
    user_facts = resolve_user_facts(
        history=request.conversation_history,
        current_message=msg,
        known_name=existing_name or request.conversational_name,
    )
    if request.user_facts:
        for k, v in request.user_facts.items():
            if v and not getattr(user_facts, k, None):
                setattr(user_facts, k, v)

    resolved_name = user_facts.name or ""

    # Parse constraints
    constraints_dict = request.constraints or {}
    constraints = ResponseConstraints(**constraints_dict) if constraints_dict else detect_constraints(msg)

    # 2. Detect queries and modifiers
    format_modifier = _detect_format_modifier(msg)
    no_extra = _detect_no_extra_constraint(msg) or format_modifier == "no_extra" or constraints.no_extra_text

    is_name_q = is_name_query(msg)
    is_hometown_q = is_hometown_query(msg)
    is_ai_origin_q = is_ai_origin_query(msg)
    is_math = _detect_math_or_simple_qa(msg)
    is_celebration = _detect_celebration_message(msg)
    is_study_method = _detect_study_method_request(msg)
    is_focus = _detect_academic_focus_request(msg)
    is_progress = _detect_progress_request(msg)
    is_improvement = _detect_academic_improvement_request(msg)
    is_explicit_data = _detect_explicit_data_request(msg)
    is_emotional = _detect_emotional_message(msg)
    is_complex = _detect_complex_detailed_request(msg)
    is_educational = _detect_educational_concept(msg)
    is_resource_link = _detect_resource_link_request(msg)
    is_direct_task = _detect_direct_task_request(msg)
    is_compound_concept_name = ("operating system" in msg_l or "neural network" in msg_l) and ("name" in msg_l or "who am i" in msg_l)

    # General student conversation detector (motivation, purpose, doubt, study capability)
    student_keywords = [
        "study", "studying", "college", "classes", "class", "degree", "university",
        "coursework", "academics", "homework", "exam", "exams", "revision", "learn",
        "learning", "motivation", "motivated", "struggle", "struggling", "improve",
        "grades", "marks", "failing", "fail", "pass", "career", "future", "dropout",
        "progress", "syllabus"
    ]
    student_inquiry_markers = [
        "why", "how", "will i", "can i", "am i", "should i", "what if", "is it",
        "do you think", "wondering", "wonder", "worried", "anxious", "scared", "fear",
        "doubt", "lost", "unsure", "confused", "give up", "worth it", "for me",
        "get started", "getting started", "feel like"
    ]
    has_student_kw = any(k in msg_l for k in student_keywords)
    has_inquiry_marker = any(m in msg_l for m in student_inquiry_markers)
    is_general_student = has_student_kw and has_inquiry_marker

    # Greeting detection: MUST be an explicit greeting and NOT a question
    is_greeting = bool(re.search(r"^(?:hi|hii+|hello|helo|hlo|hey|heyy+|yo|hola|howdy|sup|what'?s\s+up|good\s+(?:morning|afternoon|evening))\b", msg_l)) and not (msg.endswith("?") or is_hometown_q or is_name_q or is_ai_origin_q or is_math)

    # 3. Determine whether academic context should be injected
    # Provide student context whenever available so the coach knows real subjects, courses, and student name
    needs_academic_context = bool(request.student_context)

    sections = [
        format_student_context_section(
            request.student_context,
            inject=needs_academic_context,
            resolved_name=resolved_name,
            user_facts=user_facts,
        ),
        format_student_insight_section(request.student_insight, inject=needs_academic_context),
        format_study_plan_section(request.study_plan),
        format_conversation_history_section(request.conversation_history, resolved_name=resolved_name),
    ]

    # Explicitly state resolved user facts if known
    fact_lines = []
    if user_facts.name:
        fact_lines.append(f"Student's Name: {user_facts.name}")
    if user_facts.hometown:
        fact_lines.append(f"Student's Hometown / Origin: {user_facts.hometown}")
    if user_facts.location:
        fact_lines.append(f"Student's Residence: {user_facts.location}")

    if fact_lines:
        sections.append("KNOWN USER IDENTITY CONTEXT:\n" + "\n".join(f"• {line}" for line in fact_lines))

    # Supplemental interaction-derived learning context (topic mastery & preferences)
    learning_context_sec = format_learning_context_section(request.learning_history, msg)
    if learning_context_sec:
        sections.append(learning_context_sec)

    sections.append(f"\nStudent's Current Message:\n\"{msg}\"")

    # ── Instruction Dispatching by Priority ───────────────────────────────────

    # 0. Word Count Constraint: Exact or Min/Max
    if constraints.exact_word_count and constraints.exact_word_count > 1:
        target_w = constraints.exact_word_count
        min_w = constraints.min_word_count or int(target_w * 0.90)
        max_w = constraints.max_word_count or int(target_w * 1.10)
        sections.append(
            f"\n[CRITICAL LENGTH REQUIREMENT — EXACT WORD COUNT]\n"
            f"• Target Length: EXACTLY {target_w} words (acceptable range: {min_w}–{max_w} words).\n"
            f"• You MUST write a detailed, thorough, multi-paragraph response that reaches at least {min_w} words and stays under {max_w} words.\n"
            f"• Develop complete paragraphs with structure, rich details, and natural flow.\n"
            f"• Do NOT summarize. Do NOT write a short draft.\n"
            f"• Output the content directly without meta-commentary like 'Here is your {target_w}-word speech:'."
        )

    # 1. Format Constraint: Exactly One Word
    elif format_modifier == "one_word" or constraints.one_word:
        target_val = resolved_name if (is_name_q or "name" in msg_l) else ""
        instruction = (
            "\n[CRITICAL OVERRIDE — EXACTLY ONE WORD]\n"
            "• Output EXACTLY ONE SINGLE WORD and ABSOLUTELY NOTHING ELSE.\n"
            "• Zero greeting, zero punctuation except maybe a period, zero explanation.\n"
        )
        if target_val:
            instruction += f"• The user's name is {target_val}. Output exactly: {target_val}\n"
        instruction += "Respond with ONLY 1 word:"
        sections.append(instruction)

    # 2. Format Constraint: Exactly One Sentence
    elif format_modifier == "one_sentence" or constraints.one_sentence:
        sections.append(
            "\n[CRITICAL OVERRIDE — EXACTLY ONE SENTENCE]\n"
            "• Output EXACTLY ONE SINGLE CONCISE SENTENCE and NOTHING ELSE.\n"
            "• Zero greetings, zero preamble, zero follow-up offers.\n"
            "• If the user asks for their name and what they like to study: mention both clearly in 1 sentence.\n"
            "Respond in 1 sentence:"
        )

    # 3. Format Constraint: Exactly Three Points / Links
    elif format_modifier == "three_points" or constraints.exact_items == 3:
        if is_resource_link:
            links = get_curated_resources_for_text(msg + " " + " ".join([getattr(m, "content", "") for m in request.conversation_history[-4:]]))
            links_str = "\n".join([f"{i+1}. {l}" for i, l in enumerate(links[:3])])
            sections.append(
                f"\n[CRITICAL OVERRIDE — EXACTLY 3 LINKS, NO EXTRA TEXT]\n"
                f"• Provide ONLY these 3 links without any explanation:\n"
                f"{links_str}\n"
                "Respond with the 3 links only:"
            )
        else:
            sections.append(
                "\n[CRITICAL OVERRIDE — EXACTLY 3 CONCISE BULLET POINTS]\n"
                "• Output EXACTLY 3 bullet points.\n"
                "• ZERO introductory sentence. ZERO concluding questions.\n"
                "Respond with 3 bullet points:"
            )

    # 4. User Hometown / Origin Query ("Where am I from?", "Where I am from?")
    elif is_hometown_q:
        if user_facts.hometown:
            sections.append(
                f"\n[CRITICAL INSTRUCTION — USER HOMETOWN QUERY]\n"
                f"• The user is asking where they are from.\n"
                f"• The user's known hometown is {user_facts.hometown}.\n"
                f"• State directly: \"{user_facts.hometown}.\" or \"You're from {user_facts.hometown}.\"\n"
                f"• DO NOT give a coaching essay.\n"
                "Respond directly:"
            )
        else:
            sections.append(
                "\n[CRITICAL INSTRUCTION — UNKNOWN USER HOMETOWN QUERY]\n"
                "• The user is asking where they are from, but their hometown is NOT in records or conversation.\n"
                "• State EXACTLY: \"I don't have your hometown information yet.\"\n"
                "• DO NOT guess, DO NOT infer, DO NOT say 'From' or 'Hi From!'.\n"
                "Respond directly:"
            )

    # 5. AI Origin Query ("Where are you from?")
    elif is_ai_origin_q:
        sections.append(
            "\n[CRITICAL INSTRUCTION — AI ORIGIN QUERY]\n"
            "• The user is asking where YOU (the AI) are from.\n"
            "• Answer: \"I am EduGuardian, an AI academic assistant built to support university students.\"\n"
            "• DO NOT treat 'you' as the student.\n"
            "Respond directly:"
        )

    # 5.5 Compound Concept & Name Query (e.g. "what is operating system and first tell me what is my name?")
    elif is_compound_concept_name:
        name_str = f"Your name is {resolved_name}." if resolved_name else "I don't have your name saved yet."
        sections.append(
            f"\n[CRITICAL INSTRUCTION — COMPOUND CONCEPT & NAME QUERY]\n"
            f"• Answer both parts directly in 1-2 sentences:\n"
            f"  1. Name: \"{name_str}\"\n"
            f"  2. Concept definition: 1 clear, educational sentence defining the requested concept.\n"
            f"• Output format: \"{name_str} An operating system is system software that manages computer hardware, software resources, and provides common services for computer programs.\"\n"
            "Respond directly:"
        )

    # 6. Identity Name Questions (who am I, what's my name, u dint say my name)
    elif is_name_q:
        if not resolved_name:
            sections.append(
                "\n[CRITICAL INSTRUCTION — UNKNOWN IDENTITY QUERY]\n"
                "• The student asked who they are or what their name is, but their name is not in memory or profile.\n"
                "• State clearly: \"I don't have your name saved yet.\"\n"
                "• NEVER invent or guess a name.\n"
                "Respond directly:"
            )
        elif any(k in msg_l for k in ["u dint say", "you didnt say", "you didn't say"]):
            sections.append(
                f"\n[CRITICAL INSTRUCTION — IDENTITY CORRECTION]\n"
                f"• The user noted that you didn't say their name.\n"
                f"• State: \"You're right — your name is {resolved_name}.\"\n"
                f"• DO NOT give a coaching essay.\n"
                "Respond directly:"
            )
        elif any(k in msg_l for k in ["but i said my name is", "i said my name is"]):
            sections.append(
                f"\n[CRITICAL INSTRUCTION — IDENTITY ACKNOWLEDGEMENT]\n"
                f"• The user reiterated their name.\n"
                f"• State: \"Yes, you said your name is {resolved_name}.\"\n"
                f"• DO NOT say 'You were introduced as Student'.\n"
                "Respond directly:"
            )
        else:
            sections.append(
                f"\n[CRITICAL INSTRUCTION — DIRECT IDENTITY QUERY]\n"
                f"• The student asked who they are or what their name is.\n"
                f"• Answer directly with ONLY their name: \"{resolved_name}.\"\n"
                f"• DO NOT say 'Hello again, [name]'.\n"
                f"• DO NOT give psychological interpretations, self-awareness advice, or journaling suggestions.\n"
                f"• DO NOT offer study plans.\n"
                "Respond with the direct answer:"
            )

    # 7. Greeting (e.g. "hi", "hii", "hello", "hlo", "hey buddy", "what's up")
    elif is_greeting:
        name_target = f" {resolved_name}" if resolved_name else ""
        sections.append(
            f"\n[RESPONSE INSTRUCTION — CONVERSATIONAL GREETING]\n"
            f"• Greet the student warmly, naturally, and supportively (e.g., \"Hey{name_target}! 👋 Great to connect. How's everything going with your studies today, or what would you like to explore?\" or \"Hi{name_target}! 😊 Ready to learn something new, work on a study plan, or just chat? What's on your mind?\").\n"
            f"• Keep the tone warm, welcoming, and conversational.\n"
            f"• Avoid cold, robotic responses like 'What can I help you with?' or 'How can I assist?'.\n"
            f"• DO NOT generate an unsolicited study plan or academic analysis.\n"
            "Respond as EduGuardian:"
        )

    # 7.5. Student Achievement / Good Marks Celebration
    elif is_celebration:
        name_target = f" {resolved_name}" if resolved_name else ""
        sections.append(
            f"\n[RESPONSE INSTRUCTION — CELEBRATION & ENCOURAGEMENT]\n"
            f"• The student is celebrating good marks or academic achievement.\n"
            f"• Congratulate and celebrate with them warmly in 1–2 encouraging sentences (using 2–4 celebratory emojis like 🎉, 🥳, 🏆, ⭐).\n"
            f"• Keep the tone joyful and encouraging: \"That's great to hear{name_target}! 🎉 Keep building on what you're already doing well. ⭐\"\n"
            "Respond as EduGuardian:"
        )

    # 7.8. Study Methods / How to Study
    elif is_study_method:
        name_target = f"{resolved_name}, " if resolved_name else ""
        sections.append(
            "\n[RESPONSE INSTRUCTION — STUDY METHODS & HABITS]\n"
            f"• The student is asking how to study effectively.\n"
            f"• Provide warm, practical, structured advice in 3–5 short actionable paragraphs.\n"
            f"• Use 3–6 contextual emojis naturally placed as visual anchors (e.g. 🌱📚 for building study skills, 🎯 for starting with one topic, ⏱️☕ for 25-30 min sessions/breaks, 🧠💡 for deep understanding over memorization, ✍️ for self-testing, and 💪📈 for small consistent sessions).\n"
            f"• Start warmly: \"{name_target}studying is a skill you build step by step...\"\n"
            "Respond as EduGuardian:"
        )

    # 8. Direct Factual / World Knowledge / Math
    elif is_math:
        sections.append(
            "\n[CRITICAL INSTRUCTION — DIRECT FACTUAL QA]\n"
            "• Answer the question directly in 1 sentence or number.\n"
            "• Example: 'what is capital of India?' → 'New Delhi.'\n"
            "• Example: '2 + 2?' → '4.'\n"
            "• ZERO coaching, ZERO personality advice.\n"
            "Respond directly:"
        )

    # 9. Resource / Link Request
    elif is_resource_link:
        hist_text = " ".join([getattr(m, "content", "") for m in request.conversation_history[-4:]])
        links = get_curated_resources_for_text(msg + " " + hist_text)
        links_str = "\n".join([f"{i+1}. {l}" for i, l in enumerate(links[:3])])
        sections.append(
            f"\n[RESPONSE INSTRUCTION — RESOURCE LINKS]\n"
            f"• Provide direct resource links for the topic:\n"
            f"{links_str}\n"
            f"• If no links apply, state: 'I cannot retrieve live web links in this environment.'\n"
            f"• DO NOT tell the user to search YouTube.\n"
            f"• DO NOT add academic coaching around the links.\n"
            "Respond with the resources:"
        )

    # 10. Direct Task / Learning Plan
    elif is_direct_task or (no_extra and not is_focus and not is_progress):
        sections.append(
            "\n[CRITICAL OVERRIDE — DIRECT LEARNING PLAN / TASK]\n"
            "• Provide ONLY the direct, numbered learning steps for the requested topic.\n"
            "• NO greeting. NO personality analysis. NO motivational statements.\n"
            "• NO closing questions ('How does that sound?').\n"
            "• Start immediately with step 1.\n"
            "Respond now:"
        )

    # 11. Explicit Academic Data (CGPA, SGPA, attendance, marks, credits)
    elif is_explicit_data:
        sections.append(
            "\n[CRITICAL INSTRUCTION — DIRECT FACTUAL ACADEMIC DATA (CGPA / SGPA / ATTENDANCE)]\n"
            "• If the student asks 'What is my CGPA?' or asks about their CGPA:\n"
            "  - State their current CGPA directly from the ground-truth context (e.g. 'Your current CGPA is 8.45. Your latest SGPA is 8.67 from Semester 4, and your academic trajectory is improving.').\n"
            "  - NEVER say you cannot calculate it or ask the student for credit weights when it is present in the context!\n"
            "• If the student asks for their latest SGPA: state the exact SGPA and semester directly from the ground-truth context.\n"
            "• If the student asks for attendance or marks: state the exact numbers directly in 1–2 clear, encouraging sentences.\n"
            "• Stop after answering the direct question without unsolicited study plans.\n"
            "Respond as EduGuardian:"
        )

    # 12. Academic Focus
    elif is_focus:
        sections.append(
            "\n[CRITICAL INSTRUCTION — SUBJECT PRIORITY RECOMMENDATION]\n"
            "• LENGTH: Exactly 1 sentence.\n"
            "• Recommend the top priority subject based on Student Insight.\n"
            "• Stop after 1 sentence.\n"
            "Respond as EduGuardian:"
        )

    # 13. Progress Status
    elif is_progress:
        sections.append(
            "\n[CRITICAL INSTRUCTION — PROGRESS SUMMARY]\n"
            "• LENGTH: Exactly 1 sentence.\n"
            "• Summarize status directly based on Student Insight.\n"
            "• Stop after 1 sentence.\n"
            "Respond as EduGuardian:"
        )

    # 14. Emotional Distress Support
    elif is_emotional or any(k in msg_l for k in ["discouraged", "don't feel like studying", "cant study", "can't study", "give up", "giving up", "feeling lost", "struggling with"]):
        name_target = f"{resolved_name}, " if resolved_name else ""
        sections.append(
            "\n[CRITICAL INSTRUCTION — EMOTIONAL SUPPORT & ENCOURAGEMENT]\n"
            "• LENGTH: 50–90 words.\n"
            f"• 1. Acknowledge their feelings with genuine empathy and warmth (e.g. \"{name_target}it's completely okay to have days when studying feels difficult ❤️🌱\").\n"
            "• 2. Reassure them that they don't have to fix everything at once and offer ONE small, manageable starting step (e.g. 🎯 or ⏱️).\n"
            "• 3. Remind them that small sessions count as real progress (e.g. 💪📚✨).\n"
            "• Use 2–5 supportive emojis naturally placed across your sentences.\n"
            "• Keep it grounded, reassuring, and deeply supportive.\n"
            "Respond as EduGuardian:"
        )

    # 15. Educational Concept Explanation
    elif is_complex or is_educational:
        sections.append(
            "\n[RESPONSE INSTRUCTION — EDUCATIONAL CONCEPT EXPLANATION]\n"
            "• Provide a clear, intuitive, engaging explanation matching what the user requested.\n"
            "• Use 1–3 relevant concept emojis naturally placed at key points (e.g., 🧠, 💡, 💻, ⚙️, 📚, ✍️).\n"
            "• If asked to explain in simple words, use clear analogies.\n"
            "• Keep explanations structured and engaging without unsolicited study plans.\n"
            "Respond as EduGuardian:"
        )

    # 16. Study Plan Presentation
    elif request.study_plan:
        sections.append(
            "\n[RESPONSE INSTRUCTION — STUDY PLAN PRESENTATION]\n"
            "• LENGTH: 40–70 words.\n"
            "• Warmly introduce the plan and highlight its core goal and first 1–2 tasks (e.g. using 🎯, 🗓️, or ⏰).\n"
            "• Encourage opening the plan card to begin.\n"
            "Respond as EduGuardian:"
        )

    # 17. Academic Improvement Advice
    elif is_improvement:
        sections.append(
            "\n[RESPONSE INSTRUCTION — ACADEMIC GUIDANCE]\n"
            "• LENGTH: 40–80 words (or 2–3 concise actionable tips).\n"
            "• Focus strictly on the subject asked about.\n"
            "• Give 1–2 practical study actions (e.g. 📝 or 🧠).\n"
            "Respond as EduGuardian:"
        )

    # 18. General Student Conversation (motivation, college purpose, study ability, self-doubt)
    elif is_general_student or getattr(request, "response_mode", None) == "general_student_conversation":
        name_target = f"{resolved_name}, " if resolved_name else ""
        sections.append(
            "\n[RESPONSE INSTRUCTION — GENERAL STUDENT CONVERSATION]\n"
            "• The student is asking an open-ended conversational question about their studies, college, motivation, uncertainty, self-doubt, or academic purpose.\n"
            f"• Respond naturally, supportively, and constructively with warmth (using 2–5 contextually appropriate emojis like 🌱, ✨, 🎯, 💪, or 🧠 where they naturally add emotional connection).\n"
            "• Provide encouraging, thoughtful perspective without lecturing, diagnosing mental-health conditions, or labeling the student.\n"
            "• Do NOT invent facts or dump unnecessary academic metrics/scores.\n"
            "• Do NOT automatically generate an unsolicited study plan or boilerplate closing.\n"
            "Respond as EduGuardian:"
        )

    # 19. Default Conversational QA
    else:
        sections.append(
            "\n[RESPONSE INSTRUCTION — GENERAL QUESTION]\n"
            "• Answer the student's question directly.\n"
            "• LENGTH: 1–2 sentences unless the question clearly requires more.\n"
            "• Do NOT add unsolicited coaching, personality analysis, or study plans.\n"
            "• Do NOT start with a greeting or end with 'How does that sound?'.\n"
            "Respond as EduGuardian:"
        )

    return "\n\n".join(sections)


def build_teach_me_prompt(
    request: CoachRequest,
    user_facts: UserFacts,
    resolved_name: str,
    teaching_state: dict[str, Any] | None = None,
) -> str:
    """
    Builds the structured prompt for interactive Teach Me (Socratic tutoring) mode.
    Enforces adaptive pedagogical strategy progression (Levels 0–4) when students indicate confusion.
    """
    sections: list[str] = []
    t_state = teaching_state or request.teaching_state or {}
    topic = t_state.get("topic", "").strip() or "the chosen topic"
    difficulty = str(t_state.get("difficulty", "beginner"))
    current_q = t_state.get("current_question")
    support_level = int(t_state.get("support_level", 0))
    student_msg = (request.resolved_user_message or request.user_message).strip()

    strategy_names = {
        0: "Normal Explanation (Beginner-friendly)",
        1: "Simpler Wording + Concrete Example",
        2: "Real-World Analogy",
        3: "Step-by-Step Breakdown with Worked Trace",
        4: "Interactive Micro-Teaching (1 Tiny Piece + Check Question)",
    }
    strategy_label = strategy_names.get(support_level, "Normal Explanation")

    sections.append(
        f"── TEACH ME ADAPTIVE TUTORING MODE ──\n"
        f"Topic: {topic}\n"
        f"Target Difficulty: {difficulty.upper()}\n"
        f"Active Teaching Strategy: Level {support_level} — {strategy_label}\n"
        f"Active Question Being Checked: {current_q or 'None (Starting new topic)'}\n"
        f"Student's Latest Message: \"{student_msg}\""
    )

    # Add conversation history
    sections.append(format_conversation_history_section(request.conversation_history, resolved_name))

    # Add supplemental learning context (topic mastery & preferences)
    learning_context_sec = format_learning_context_section(request.learning_history, student_msg)
    if learning_context_sec:
        sections.append(learning_context_sec)

    # Add level-specific pedagogical instructions
    if support_level == 1:
        strategy_instructions = (
            f"[ADAPTIVE TEACHING INSTRUCTION — LEVEL 1: SIMPLIFIED WORDING + CONCRETE EXAMPLE]\n"
            f"The student needs a simpler presentation of {topic}.\n"
            f"1. Open naturally and warmly (e.g., 'Let\\'s make this much simpler! 🌱' or 'Let\\'s look at this from a simpler angle.').\n"
            f"2. Simplify vocabulary: avoid unnecessary technical jargon or complex theoretical terms.\n"
            f"3. Break the concept into fewer, fundamental pieces.\n"
            f"4. Provide ONE clear, concrete example that illustrates the core idea immediately.\n"
            f"5. End with ONE simple checking question (mark with 🧠) to confirm understanding. Keep total length 60–110 words."
        )
    elif support_level == 2:
        strategy_instructions = (
            f"[ADAPTIVE TEACHING INSTRUCTION — LEVEL 2: REAL-WORLD ANALOGY]\n"
            f"The student needs a different pedagogical approach using an intuitive real-world analogy for {topic}.\n"
            f"1. Open naturally (e.g., 'Let\\'s try a different way using an everyday analogy. 🌱').\n"
            f"2. Explain the concept using an intuitive real-world analogy (e.g., Russian nesting dolls or boxes inside boxes for recursion, looking up a word in a dictionary for binary search, a stack of trays for stacks).\n"
            f"3. Connect the analogy back to the technical concept so the student sees the bridge clearly.\n"
            f"4. End with ONE friendly checking question related to the analogy or concept (mark with 🧠). Keep total length 70–120 words."
        )
    elif support_level == 3:
        strategy_instructions = (
            f"[ADAPTIVE TEACHING INSTRUCTION — LEVEL 3: STEP-BY-STEP BREAKDOWN]\n"
            f"The student needs a clear, step-by-step mechanical breakdown of {topic}.\n"
            f"1. Open naturally (e.g., 'Let\\'s take this step-by-step. 🌱').\n"
            f"2. Break the concept into clear numbered steps (Step 1, Step 2, Step 3).\n"
            f"3. Use a tiny worked example and trace exactly what happens at each step.\n"
            f"4. Explain the transition between each step clearly.\n"
            f"5. End with ONE focused checking question about one of the steps (mark with 🧠). Keep total length 80–130 words."
        )
    elif support_level >= 4:
        strategy_instructions = (
            f"[ADAPTIVE TEACHING INSTRUCTION — LEVEL 4: INTERACTIVE MICRO-TEACHING]\n"
            f"The student needs focused, interactive micro-steps for {topic}.\n"
            f"1. Open naturally (e.g., 'Let\\'s take it one tiny step at a time. 🌱').\n"
            f"2. CRITICAL: Do NOT give a large or multi-part explanation.\n"
            f"3. Explain ONLY ONE single small piece (1–2 short, clear sentences max).\n"
            f"4. Ask ONE very simple check question about that single piece (mark with 🧠).\n"
            f"5. STOP immediately and wait for the student's answer before explaining the next piece. Keep response strictly 30–70 words."
        )
    else:
        # Level 0 (Normal explanation)
        if not current_q:
            strategy_instructions = (
                f"[ADAPTIVE TEACHING INSTRUCTION — LEVEL 0: NORMAL START]\n"
                f"1. Greet briefly and confirm {topic} with warmth (e.g., 'Let\\'s explore **{topic}** together! 🌱').\n"
                f"2. Explain ONE fundamental concept in 2–3 clear, beginner-friendly sentences.\n"
                f"3. Provide ONE simple, concrete example (ASCII diagram or short snippet if helpful).\n"
                f"4. Ask ONE single specific checking question at the end (mark with 🧠).\n"
                f"5. STOP after the question! Keep total response around 60–120 words."
            )
        else:
            strategy_instructions = (
                f"[ADAPTIVE TEACHING INSTRUCTION — LEVEL 0: NORMAL PROGRESSION]\n"
                f"Previous Question Asked: \"{current_q}\"\n"
                f"Student's Message: \"{student_msg}\"\n\n"
                f"• If student answered: evaluate warmly (Correct / Partial / Incorrect). If correct, introduce next logical concept + small example + next checking question 🧠.\n"
                f"• Always end with EXACTLY ONE checking question 🧠. Keep total response around 60–120 words."
            )

    sections.append(strategy_instructions)

    # General safety & anti-leakage rules
    sections.append(
        "[STRICT SAFETY & PERSONALIZATION RULES]\n"
        "• NEVER tell the student their support level, score, or say they are 'struggling', 'weak', or 'failing'.\n"
        "• NEVER mention internal system states (e.g., 'support level 3', 'according to your history').\n"
        "• Phrase all transitions naturally and encouragingly.\n"
        "• If the student's current message has specific instructions (e.g., 'keep it short', 'use Python'), ALWAYS prioritize the student's immediate request."
    )

    sections.append("Respond as EduGuardian Socratic Tutor:")
    return "\n\n".join(sections)



def build_quiz_prompt(
    request: CoachRequest,
    user_facts: UserFacts,
    resolved_name: str,
    quiz_state: dict[str, Any] | None = None,
) -> str:
    """
    Builds the structured prompt for interactive Quiz Mode.
    Guarantees:
    1. Dynamic LLM generation for arbitrary topics (zero hardcoded questions).
    2. EXACTLY ONE question presented at a time.
    3. Strict evaluation of student answer (Correct / Partial / Incorrect).
    4. Progression across question count (e.g. 1 of 5 -> 2 of 5 ... -> final summary).
    5. Clean, concise final score & performance breakdown upon session completion.
    """
    sections: list[str] = []
    q_state = quiz_state or request.quiz_state or {}
    topic = q_state.get("topic", "").strip() or "the chosen topic"
    difficulty = str(q_state.get("difficulty", "beginner")).upper()
    q_num = int(q_state.get("current_question_number", 1))
    total_q = int(q_state.get("total_questions", 5))
    current_q_text = q_state.get("current_question_text")
    current_options = q_state.get("current_options") or []
    current_correct = q_state.get("current_correct_answer")
    student_msg = (request.resolved_user_message or request.user_message).strip()

    options_str = "\n".join(f"  {opt}" for opt in current_options) if current_options else "None (Short Answer)"

    diff_guidelines = {
        "BEGINNER": "Definitions, concept recognition, simple examples, and fundamental syntax/application.",
        "INTERMEDIATE": "Concept application, tracing code/logic, moderate problem solving, comparing approaches, and simple debugging.",
        "ADVANCED": "Multi-step reasoning, tricky edge cases, complexity/performance analysis, and architectural/design problems.",
    }
    target_guideline = diff_guidelines.get(difficulty, diff_guidelines["BEGINNER"])

    sections.append(
        f"── INTERACTIVE QUIZ MODE ──\n"
        f"Topic: {topic}\n"
        f"Target Difficulty: {difficulty} ({target_guideline})\n"
        f"Current Question Index: Question {q_num} of {total_q}\n"
        f"Active Question Text: {current_q_text or 'None (Starting Quiz)'}\n"
        f"Active Question Options:\n{options_str}\n"
        f"Student's Latest Message: \"{student_msg}\""
    )

    # Conversation history
    sections.append(format_conversation_history_section(request.conversation_history, resolved_name))

    if not current_q_text:
        # Turn 1: Generating Question 1 of total_q
        sections.append(
            f"[QUIZ INSTRUCTION — PRESENTING QUESTION 1 OF {total_q}]\n"
            f"1. Greet with brief enthusiasm and announce the quiz topic (e.g. 'Sure! 🧠 Let\\'s test your understanding of **{topic}**!').\n"
            f"2. Present **Question 1 of {total_q}**:\n"
            f"   - Write a clear, high-quality multiple choice question matching {difficulty} difficulty ({target_guideline}).\n"
            f"   - Provide 4 distinct, formatted options (A, B, C, D), where exactly one is clearly correct.\n"
            f"   - Format options clearly:\n"
            f"     A. [Option A]\n"
            f"     B. [Option B]\n"
            f"     C. [Option C]\n"
            f"     D. [Option D]\n"
            f"3. End with: 'Your answer?'\n"
            f"4. CRITICAL RULES:\n"
            f"   - Output ONLY Question 1. Do NOT output Question 2 or any other questions.\n"
            f"   - Do NOT reveal the answer or internal scores/historical labels.\n"
            f"   - STOP immediately after presenting the options!"
        )
    else:
        # Turn N: Evaluating previous question (q_num - 1 or current_q_text)
        is_final_question = (q_num >= total_q)
        next_q_num = q_num + 1

        if not is_final_question:
            sections.append(
                f"[QUIZ INSTRUCTION — EVALUATE ANSWER & PRESENT QUESTION {next_q_num} OF {total_q}]\n"
                f"Question Answered: \"{current_q_text}\"\n"
                f"Options:\n{options_str}\n"
                f"Student's Answer: \"{student_msg}\"\n\n"
                f"1. EVALUATE THE STUDENT'S ANSWER:\n"
                f"   • If CORRECT: Celebrate warmly ('Correct! 🎉' or 'Spot on! ⭐') and explain why in 1 sentence.\n"
                f"   • If PARTIALLY CORRECT: Validate the accurate part ('Partially correct! 👍') and clarify the missing detail in 1 sentence.\n"
                f"   • If INCORRECT: Give supportive feedback ('Not quite — that\\'s okay! 🌱'), state the correct answer, and explain why in 1 sentence.\n\n"
                f"2. PRESENT THE NEXT QUESTION (Question {next_q_num} of {total_q}):\n"
                f"   - Formulate a new high-quality {difficulty} question ({target_guideline}) on {topic}.\n"
                f"   - Provide 4 clean options (A, B, C, D).\n"
                f"   - End with: 'Your answer?'\n\n"
                f"3. CRITICAL RULES:\n"
                f"   - Present ONLY Question {next_q_num}. Do NOT present any subsequent questions.\n"
                f"   - Do NOT reveal internal scores or historical labels.\n"
                f"   - STOP immediately after presenting Question {next_q_num} options!"
            )
        else:
            # Final Question evaluated -> Deliver final score summary
            sections.append(
                f"[QUIZ INSTRUCTION — EVALUATE FINAL QUESTION & PROVIDE FINAL SUMMARY]\n"
                f"Final Question Answered: \"{current_q_text}\"\n"
                f"Options:\n{options_str}\n"
                f"Student's Answer: \"{student_msg}\"\n\n"
                f"1. EVALUATE THE FINAL ANSWER:\n"
                f"   • If CORRECT: Celebrate ('Correct! 🎉') + 1 sentence explanation.\n"
                f"   • If INCORRECT: Supportively state correct answer ('Not quite — that\\'s okay! 🌱') + 1 sentence explanation.\n\n"
                f"2. DELIVER THE FINAL QUIZ RESULT & SUMMARY:\n"
                f"   - Announce completion with a celebration header: 'Quiz Complete! 🎉'\n"
                f"   - Present a concise performance summary:\n"
                f"     🌟 **Strengths**: 1 key concept the student did well with.\n"
                f"     🔍 **Area to Review**: 1 specific concept to brush up on.\n"
                f"   - End with 1 encouraging sentence inviting next steps (e.g. 'Keep up the great momentum! 💪 Would you like to create a study plan or test another topic?')."
            )

    sections.append("Respond as EduGuardian Quiz Coach:")
    return "\n\n".join(sections)


def get_system_prompt(support_intensity: str | None = None) -> str:
    """Returns standard or intensive system prompt based on support intensity."""
    if support_intensity == "intensive":
        return RECOVERY_COACH_INTENSIVE_PROMPT
    return RECOVERY_COACH_SYSTEM_PROMPT
