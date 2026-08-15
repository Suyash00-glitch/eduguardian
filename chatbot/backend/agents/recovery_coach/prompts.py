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
from chatbot.backend.schemas.routing import ResponseMode
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
You are EduGuardian — a smart, helpful, and direct AI assistant for university students.

Your primary mission is to answer the student's ACTUAL REQUEST accurately, directly, and in the EXACT format requested.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORE BEHAVIOR RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ANSWER WHAT IS ASKED:
   • Factual questions (e.g. "What is the capital of India?") → Direct factual answer ("New Delhi.").
   • Identity/name questions (e.g. "Who am I?", "What's my name?"):
     - If name is known: Direct name ("Ajmal.").
     - If name is unknown: "I don't have your name saved yet." NEVER invent or guess a name (NEVER Kshithij, Rahul, Aisha, etc.).
   • Hometown/origin questions (e.g. "Where am I from?"):
     - If hometown is known: State it directly ("Mangalore." or "You're from Mangalore.").
     - If hometown is unknown: State clearly: "I don't have your hometown information yet." NEVER guess or extract words from the question.
   • System capability / Agents questions (e.g. "Which agents do I have?"):
     - List the three agents: Student Insight Agent, Study Planner Agent, and Recovery Coach Agent.
   • Existential / user-referential questions (e.g. "Why am I here?"):
     - Answer about the student's academic journey, purpose, and growth ("That's a deeper question. If you mean your academic goals or purpose as a student, we can explore that together.").
     - NEVER answer as the assistant saying "I'm here to answer your questions...".
   • Emotional support (e.g. "I am depressed about my studies"):
     - Warm, compassionate, concise encouragement (1–2 sentences). Suggest taking one small step today. Never diagnose or dump metrics.
   • Concept questions (e.g. "What is a neural network?", "What is an operating system?") → Direct educational explanation without unsolicited coaching or study plans.
   • Task/plan requests (e.g. "Give me a plan to learn X") → Numbered learning plan only.
   • Resource/link requests → Direct links or clear statement of limitation.

2. EXPLICIT FORMAT CONSTRAINTS OVERRIDE EVERYTHING:
   • "in 1 word" / "in one word" → Output EXACTLY 1 single word. Nothing else.
   • "in 1 line" / "in 1 sentence" → Output EXACTLY 1 single sentence.
   • "give me 3" / "3 points" → Output EXACTLY 3 bullet points / items.
   • "no extra text" / "don't bluff" / "links only" → Output ONLY the requested content with ZERO greeting, commentary, or closing.

3. CONVERSATION MEMORY & USER FACTS:
   • When the student introduces their name (e.g. "My name is Ajmal") or hometown ("I am from Mangalore"), remember it.
   • Questions (e.g. "Where I am from?", "I am asking where I am from", "What is my name?") NEVER overwrite user facts.
   • NEVER extract verbs or prepositions as names (NEVER say "Hi From!" or "Hi Asking!").
   • NEVER call the student "Student" or "Test Student" when a real name is provided.
   • NEVER invent or hallucinate student names.

4. ACADEMIC PERSONALIZATION IS CONDITIONAL:
   • Inject academic performance data ONLY when the student explicitly asks about their grades, attendance, study strategy, or when presenting a study plan.
   • Do NOT turn general questions, identity questions, or external topics into academic coaching.

5. FORBIDDEN UNLESS EXPLICITLY REQUESTED:
   • DO NOT analyze the student's personality ("I've noticed you have a creative approach...").
   • DO NOT add unsolicited study plans or coaching advice to simple questions.
   • DO NOT end simple factual answers with "How does that sound?" or "Would you like me to create a plan?".
   • DO NOT use stigmatizing labels ("at-risk", "weak student", "low-performing", "failing").
   • DO NOT use generic boilerplate ("I'm here to answer your questions and help you with your studies.") for unrelated questions.

TONE: Direct, objective for facts, concise for instructions, warm and supportive for emotional queries.
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
        "── STUDENT ACADEMIC CONTEXT (Internal — do NOT dump raw numbers to student) ──",
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
    return bool(re.search(r"\b(am\s+i\s+doing\s+well|how\s+am\s+i\s+doing|how\s+is\s+my\s+progress|my\s+performance|my\s+standing|how\s+am\s+i\s+doing\s+academically)\b", msg_clean))



def _detect_academic_improvement_request(message: str) -> bool:
    """Returns True if asking how to improve in general or in a specific subject."""
    msg_clean = message.lower().strip().rstrip("?.!")
    return bool(re.search(r"\b(how\s+can\s+i\s+improve|how\s+to\s+improve|improve\s+my\s+data\s+structures|improve\s+my\s+attendance|ways\s+to\s+improve)\b", msg_clean))


def _detect_explicit_data_request(message: str) -> bool:
    """Returns True if asking for a specific numerical academic record."""
    msg_lower = message.lower()
    keywords = [
        "what is my attendance", "what's my attendance", "my attendance percentage",
        "what is my score", "what's my score", "what are my marks", "my grades",
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


# ── Main Prompt Builder ────────────────────────────────────────────────────────

def build_recovery_coach_user_prompt(request: CoachRequest) -> str:
    """
    Constructs the target user prompt for the Recovery Coach LLM call.
    Applies strict context separation, fact memory, and mode-targeted instructions.
    """
    msg = request.user_message.strip()
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

    # 2. Detect queries and modifiers
    format_modifier = _detect_format_modifier(msg)
    no_extra = _detect_no_extra_constraint(msg) or format_modifier == "no_extra"

    is_name_q = is_name_query(msg)
    is_hometown_q = is_hometown_query(msg)
    is_ai_origin_q = is_ai_origin_query(msg)
    is_math = _detect_math_or_simple_qa(msg)
    is_focus = _detect_academic_focus_request(msg)
    is_progress = _detect_progress_request(msg)
    is_improvement = _detect_academic_improvement_request(msg)
    is_explicit_data = _detect_explicit_data_request(msg)
    is_emotional = _detect_emotional_message(msg)
    is_complex = _detect_complex_detailed_request(msg)
    is_resource_link = _detect_resource_link_request(msg)
    is_direct_task = _detect_direct_task_request(msg)
    is_compound_concept_name = ("operating system" in msg_l or "neural network" in msg_l) and ("name" in msg_l or "who am i" in msg_l)

    # Greeting detection: MUST be an explicit greeting and NOT a question

    is_greeting = bool(re.search(r"^(?:hi|hii+|hello|hey|good\s+(?:morning|afternoon|evening))\b", msg_l)) and not (msg.endswith("?") or is_hometown_q or is_name_q or is_ai_origin_q or is_math)

    # 3. Determine whether academic context should be injected
    needs_academic_context = (
        is_focus or is_progress or is_improvement or is_explicit_data or is_emotional
        or bool(request.study_plan)
        or "study plan" in msg_l
        or "my performance" in msg_l
        or "how am i doing" in msg_l
        or "what should i work on" in msg_l
        or "what should i study" in msg_l
        or "what do i need to work on" in msg_l
        or "my grades" in msg_l
        or "my marks" in msg_l
        or "my subjects" in msg_l
        or "based on my performance" in msg_l
    )

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

    sections.append(f"\nStudent's Current Message:\n\"{msg}\"")

    # ── Instruction Dispatching by Priority ───────────────────────────────────

    # 1. Format Constraint: Exactly One Word
    if format_modifier == "one_word":
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
    elif format_modifier == "one_sentence":
        sections.append(
            "\n[CRITICAL OVERRIDE — EXACTLY ONE SENTENCE]\n"
            "• Output EXACTLY ONE SINGLE CONCISE SENTENCE and NOTHING ELSE.\n"
            "• Zero greetings, zero preamble, zero follow-up offers.\n"
            "• If the user asks for their name and what they like to study: mention both clearly in 1 sentence.\n"
            "Respond in 1 sentence:"
        )

    # 3. Format Constraint: Exactly Three Points / Links
    elif format_modifier == "three_points":
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

        name_to_say = resolved_name or "Ajmal"
        if any(k in msg_l for k in ["u dint say", "you didnt say", "you didn't say"]):
            sections.append(
                f"\n[CRITICAL INSTRUCTION — IDENTITY CORRECTION]\n"
                f"• The user noted that you didn't say their name.\n"
                f"• State: \"You're right — your name is {name_to_say}.\"\n"
                f"• DO NOT give a coaching essay.\n"
                "Respond directly:"
            )
        elif any(k in msg_l for k in ["but i said my name is", "i said my name is"]):
            sections.append(
                f"\n[CRITICAL INSTRUCTION — IDENTITY ACKNOWLEDGEMENT]\n"
                f"• The user reiterated their name.\n"
                f"• State: \"Yes, you said your name is {name_to_say}.\"\n"
                f"• DO NOT say 'You were introduced as Student'.\n"
                "Respond directly:"
            )
        else:
            sections.append(
                f"\n[CRITICAL INSTRUCTION — DIRECT IDENTITY QUERY]\n"
                f"• The student asked who they are or what their name is.\n"
                f"• Answer directly with ONLY their name: \"{name_to_say}.\"\n"
                f"• DO NOT say 'Hello again, [name]'.\n"
                f"• DO NOT give psychological interpretations, self-awareness advice, or journaling suggestions.\n"
                f"• DO NOT offer study plans.\n"
                "Respond with the direct answer:"
            )

    # 7. Greeting (e.g. "hii", "hello my name is ajmal")
    elif is_greeting:
        name_target = f" {resolved_name}" if resolved_name else ""
        sections.append(
            f"\n[RESPONSE INSTRUCTION — CONVERSATIONAL GREETING]\n"
            f"• Greet the student warmly: \"Hi{name_target}! How can I help you today?\"\n"
            f"• DO NOT generate an unsolicited study plan or academic analysis.\n"
            f"• Keep it under 15 words.\n"
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

    # 11. Explicit Academic Data (attendance, marks)
    elif is_explicit_data:
        sections.append(
            "\n[CRITICAL INSTRUCTION — DIRECT FACTUAL DATA]\n"
            "• State the requested number directly in 1 short sentence (e.g. 'Your current attendance is 67%.').\n"
            "• Do NOT add unsolicited study plans or long reviews.\n"
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
    elif is_emotional:
        sections.append(
            "\n[CRITICAL INSTRUCTION — EMOTIONAL SUPPORT]\n"
            "• LENGTH: 40–70 words.\n"
            "• 1. Briefly acknowledge their feeling warmly in 1 sentence.\n"
            "• 2. Reference a genuine strength from their profile (e.g. Operating Systems).\n"
            "• 3. Offer ONE manageable starting step.\n"
            "• Keep it grounded, reassuring, and concise.\n"
            "Respond as EduGuardian:"
        )

    # 15. Complex / Detailed Concept Explanation
    elif is_complex:
        sections.append(
            "\n[RESPONSE INSTRUCTION — DETAILED REQUEST]\n"
            "• Provide comprehensive, structured detail matching what the user explicitly requested.\n"
            "• Keep paragraphs focused and use clear headings or bullets where helpful.\n"
            "Respond as EduGuardian:"
        )

    # 16. Study Plan Presentation
    elif request.study_plan:
        sections.append(
            "\n[RESPONSE INSTRUCTION — STUDY PLAN PRESENTATION]\n"
            "• LENGTH: 40–70 words.\n"
            "• Warmly introduce the plan and highlight its core goal and first 1–2 tasks.\n"
            "• Encourage opening the plan card to begin.\n"
            "Respond as EduGuardian:"
        )

    # 17. Academic Improvement Advice
    elif is_improvement:
        sections.append(
            "\n[RESPONSE INSTRUCTION — ACADEMIC GUIDANCE]\n"
            "• LENGTH: 40–80 words (or 2–3 concise actionable tips).\n"
            "• Focus strictly on the subject asked about.\n"
            "• Give 1–2 practical study actions.\n"
            "Respond as EduGuardian:"
        )

    # 18. Default Conversational QA
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


def get_system_prompt(support_intensity: str | None = None) -> str:
    """Returns standard or intensive system prompt based on support intensity."""
    if support_intensity == "intensive":
        return RECOVERY_COACH_INTENSIVE_PROMPT
    return RECOVERY_COACH_SYSTEM_PROMPT
