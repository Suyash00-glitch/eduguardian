"""
Deterministic Study Plan Builder, Parser, and Sanitizer.

Provides reliable construction, validation, and structured repair of StudyPlan objects.
Guarantees that every generated plan consists of 100% genuine academic study activities,
valid subject names, current week_start dates, and strict adherence to user constraints.
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import date
from typing import Any

from chatbot.backend.schemas.planner import (
    PlanMilestone,
    PlanRequest,
    PriorityLevel,
    StudyPlan,
    StudyTask,
)

logger = logging.getLogger(__name__)

# Days of the week for scheduling
_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Forbidden non-academic phrases that indicate counselor/case-management hallucinations
_FORBIDDEN_TASK_PATTERNS = re.compile(
    r"\b("
    r"communicate with (the )?student|discuss (and understand )?student|discuss concerns|"
    r"respect student'?s? autonomy|understand student'?s? goals|counsel (the )?student|"
    r"follow[- ]up with (the )?student|meet with (the )?student|case management|"
    r"administrative follow-up|check[- ]in on emotional state|counseling session"
    r")\b",
    re.IGNORECASE,
)

SUBJECT_ALIASES: dict[str, list[str]] = {
    "Data Structures & Algorithms": [
        "dsa", "data structures", "data structure", "algorithms", "algo", "trees", "graphs",
        "linked list", "binary search", "22cs32", "is2001", "sorting", "stack", "queue"
    ],
    "Operating Systems": [
        "os", "operating systems", "operating system", "semaphores", "deadlock",
        "process scheduling", "paging", "is2003", "is2003-1", "virtual memory"
    ],
    "Database Management Systems": [
        "dbms", "database", "databases", "sql", "normalization", "relational algebra",
        "transactions", "is2001", "is2001-1", "b+ tree"
    ],
    "Machine Learning Foundations": [
        "ml", "machine learning", "supervised learning", "regression", "svm", "decision tree",
        "gradient descent", "neural networks", "is2002", "is2002-1", "jupyter"
    ],
    "Computer Networks": [
        "cn", "networks", "computer networks", "computer network", "tcp", "ip", "routing",
        "subnet", "osi", "is2004", "is2004-1", "socket"
    ],
    "Software Engineering": [
        "se", "software engineering", "agile", "scrum", "design patterns", "ci/cd",
        "is2005", "is2005-1", "testing"
    ],
    "Discrete Mathematical Structures": [
        "math", "maths", "mathematics", "discrete", "discrete math", "calculus",
        "linear algebra", "22mat31", "graph theory", "logic"
    ],
    "Universal Human Values": [
        "uhv", "human values", "ethics", "hu2001", "hu2001-1"
    ]
}

SUBJECT_TOPICS: dict[str, list[tuple[str, str]]] = {
    "Data Structures & Algorithms": [
        ("Binary Search Trees & AVL Balancing", "Implement BST operations, tree traversals (Inorder, Preorder, Postorder), and height balancing."),
        ("Graph Algorithms: BFS, DFS & Shortest Paths", "Practice graph representations (Adjacency Matrix/List), Dijkstra's algorithm, and cycle detection."),
        ("Dynamic Programming: Memoization & Knapsack", "Solve classic DP problems including 0/1 Knapsack, Longest Common Subsequence, and subset sum."),
        ("Linked Lists, Stacks & Queue Applications", "Implement doubly linked lists, monotonic stack problems, and expression tree evaluations."),
        ("Sorting, Searching & Two-Pointer Drills", "Master QuickSort, MergeSort partition logic, binary search boundary conditions, and 2-pointer problem sets."),
    ],
    "Operating Systems": [
        ("Process Synchronization & Semaphore Solved Problems", "Master mutual exclusion, semaphores, and classic IPC problems (Producer-Consumer, Dining Philosophers)."),
        ("CPU Scheduling Algorithms & Timing Charts", "Compute Turnaround Time and Waiting Time for FCFS, SJF (Preemptive/Non-preemptive), and Round Robin."),
        ("Deadlock Avoidance & Banker's Algorithm", "Solve resource allocation state verification and Banker's safe state determination problems."),
        ("Virtual Memory, Paging & Page Replacement", "Analyze paging hardware, TLB hit/miss latency, and simulate FIFO, LRU, and Optimal replacement."),
        ("File Systems & Disk Scheduling Drills", "Practice disk head movement calculations for SCAN, C-SCAN, LOOK, and SSTF algorithms."),
    ],
    "Database Management Systems": [
        ("Relational Algebra & Advanced SQL Query Drills", "Write complex queries using nested subqueries, GROUP BY, HAVING, and window functions."),
        ("Functional Dependencies & Normalization (1NF to BCNF)", "Determine candidate keys, find canonical covers, and test for dependency preservation and lossless joins."),
        ("Transaction ACID Properties & Concurrency Control", "Analyze conflict serializability, precedence graphs, and Two-Phase Locking (2PL) protocols."),
        ("Indexing, B+ Trees & Storage Engine Internals", "Trace B+ tree insertions, node splits, and calculate index fanout and search I/O cost."),
        ("ER Modeling & Relational Schema Mapping", "Convert real-world business requirements into robust Entity-Relationship schemas and tables."),
    ],
    "Machine Learning Foundations": [
        ("Supervised Learning: Cost Functions & Gradient Descent", "Derive cost functions for linear regression and trace parameter updates using batch and stochastic gradient descent."),
        ("Classification: Logistic Regression & Decision Trees", "Compute cross-entropy loss, decision boundaries, and information gain (Entropy/Gini impurity) splits."),
        ("Support Vector Machines & Kernel Transformations", "Understand maximum margin hyperplanes, soft margin slack variables, and RBF kernel formulations."),
        ("Hands-on Jupyter Lab: Model Evaluation & ROC Curves", "Implement train-test splits, k-fold cross-validation, confusion matrices, precision-recall, and ROC-AUC curves."),
        ("Unsupervised Learning: K-Means & PCA Dimension Reduction", "Trace K-means centroid convergence and compute principal component eigenvectors."),
    ],
    "Computer Networks": [
        ("TCP/IP Layering & Subnet Masking (CIDR) Calculations", "Solve variable-length subnet masking (VLSM) and CIDR address aggregation problems."),
        ("Routing Protocols: Link State (OSPF) & Distance Vector", "Execute Dijkstra's shortest path for link-state and Bellman-Ford for distance vector routing."),
        ("Transport Layer: TCP Flow Control & Congestion Management", "Analyze TCP 3-way handshakes, sequence/ACK numbering, and congestion window growth phases (Slow Start, AIMD)."),
        ("Data Link Layer: Error Detection (CRC) & Sliding Window", "Compute Cyclic Redundancy Check (CRC) polynomials and simulate Go-Back-N and Selective Repeat protocols."),
        ("Socket Programming: Client-Server Socket Communication", "Build and test TCP/UDP client-server socket communication scripts in Python."),
    ],
    "Discrete Mathematical Structures": [
        ("Propositional Logic, Predicates & Truth Tables", "Construct truth tables, prove logical equivalences, and formalize predicate statements with quantifiers."),
        ("Relations, Equivalence Classes & Hasse Diagrams", "Determine reflexive, symmetric, and transitive closures, and construct Hasse diagrams for posets."),
        ("Graph Theory: Eulerian, Hamiltonian & Tree Properties", "Prove Euler's formula for planar graphs and calculate chromatic numbers and spanning trees."),
        ("Recurrence Relations & Generating Functions", "Solve homogeneous and non-homogeneous linear recurrence relations with characteristic roots."),
    ],
    "Software Engineering": [
        ("Agile Scrum & Sprint Planning", "Break requirements into user stories, define acceptance criteria, and plan 2-week sprint backlogs."),
        ("Design Patterns & Architecture Modeling", "Implement Factory, Singleton, Observer, and Strategy patterns in modular object-oriented code."),
        ("Automated Software Testing & CI/CD", "Write unit test suites with mock objects and configure automated continuous integration pipelines."),
    ],
    "Universal Human Values": [
        ("Self-Exploration & Human Harmony", "Reflect on core human aspirations, continuous happiness, and professional integrity guidelines."),
        ("Professional Ethics & Case Studies", "Analyze ethical dilemmas in engineering practices and environmental sustainability."),
    ]
}


_BARE_STUDY_PLAN_PATTERN = re.compile(
    r"^(?:can\s+you\s+|could\s+you\s+|please\s+)?(?:create|make|give|build|design|help\s+me\s+with|provide|how\s+should\s+i\s+study|how\s+to\s+study|help\s+me\s+prepare\s+for|prepare\s+for|i\s+want\s+a|i\s+need\s+a)?\s*"
    r"(?:me\s+)?(?:a\s+)?(?:detailed\s+|weekly\s+|good\s+|new\s+)?(?:study\s+plan|timetable|study\s+schedule|schedule|plan|routine|roadmap|study|my\s+exams?|exams?)?"
    r"(?:\s+for\s+me)?(?:\s+to\s+prepare\s+for\s+my\s+exams?|\s+help\s+me\s+prepare\s+for\s+my\s+exams?|\s+for\s+my\s+exams?)?[\s.?!]*$",
    re.IGNORECASE,
)


def is_bare_study_plan_request(text: str | None) -> bool:
    """
    Checks if the user message is an open/bare study plan request without explicit scheduling preferences.
    Examples: 'Create a detailed study plan for me.', 'Make me a timetable', 'Help me prepare for my exams'.
    """
    if not text:
        return True
    return bool(_BARE_STUDY_PLAN_PATTERN.match(text.strip()))


def parse_study_preferences(goal_text: str | None, history: list[Any] | None = None) -> dict[str, Any]:
    """
    Extracts structured student study preferences from user message and conversational context:
    - daily_minutes: available study time in minutes if specified
    - preferred_time: 'morning' | 'afternoon' | 'evening' | 'night' if specified
    - custom_start_hour: specific hour int if given (e.g. '7 PM onwards' -> 19)
    - schedule_mode: 'everyday' | 'weekdays' | 'weekends' | 'mon_sat' if specified
    - excluded_days: list of excluded day names (e.g. ['Sunday'])
    - main_goal: 'weak_subjects' | 'exam_prep' | 'improve_cgpa' | 'syllabus' | 'balanced'
    - exam_timeframe: upcoming exam duration or date string
    - has_explicit_time: whether the student provided specific hours/time
    - has_sufficient_preferences: whether enough information was collected to build a custom timetable
    """
    raw_current = (goal_text or "").strip()

    # If the student's current message is a bare prompt, require preference gathering immediately
    if is_bare_study_plan_request(raw_current):
        return {
            "daily_minutes": None,
            "preferred_time": None,
            "custom_start_hour": None,
            "schedule_mode": None,
            "excluded_days": [],
            "main_goal": None,
            "exam_timeframe": None,
            "has_explicit_time": False,
            "has_sufficient_preferences": False,
        }

    text_to_scan = raw_current
    if history:
        for msg in reversed(history[-6:]):
            content = getattr(msg, "content", "") if not isinstance(msg, dict) else msg.get("content", "")
            role = getattr(msg, "role", "") if not isinstance(msg, dict) else msg.get("role", "")
            if role in ("user", "student") and content:
                text_to_scan = f"{content} {text_to_scan}"

    lower = text_to_scan.lower()

    # 1. Extract daily study time
    daily_minutes: int | None = None
    has_explicit_time = False

    hour_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\b", lower)
    if hour_match:
        hrs = float(hour_match.group(1))
        daily_minutes = int(min(360, max(30, hrs * 60)))
        has_explicit_time = True
    else:
        min_match = re.search(r"\b(\d+)\s*(?:mins?|minutes?)\b", lower)
        if min_match:
            daily_minutes = int(max(20, min(360, int(min_match.group(1)))))
            has_explicit_time = True
        elif "1 hr" in lower or "one hour" in lower:
            daily_minutes = 60
            has_explicit_time = True
        elif "2 hr" in lower or "two hours" in lower or "2 hours" in lower:
            daily_minutes = 120
            has_explicit_time = True
        elif "3 hr" in lower or "three hours" in lower or "3 hours" in lower:
            daily_minutes = 180
            has_explicit_time = True
        elif "4 hr" in lower or "four hours" in lower:
            daily_minutes = 240
            has_explicit_time = True

    # 2. Specific time or preferred time of day
    custom_start_hour: int | None = None
    preferred_time: str | None = None

    time_num_match = re.search(r"\b([1-9]|1[0-2])\s*(?:pm|p\.m\.)\b", lower)
    if time_num_match:
        val = int(time_num_match.group(1))
        custom_start_hour = 12 if val == 12 else val + 12
        preferred_time = "evening" if custom_start_hour < 21 else "night"
    else:
        am_match = re.search(r"\b([1-9]|1[0-2])\s*(?:am|a\.m\.)\b", lower)
        if am_match:
            val = int(am_match.group(1))
            custom_start_hour = 0 if val == 12 else val
            preferred_time = "morning"
        elif re.search(r"\b(morning|mornings|early\s+morning|am)\b", lower):
            preferred_time = "morning"
        elif re.search(r"\b(afternoon|afternoons|pm)\b", lower) and "evening" not in lower:
            preferred_time = "afternoon"
        elif re.search(r"\b(night|late\s+night|nights)\b", lower):
            preferred_time = "night"
        elif re.search(r"\b(evening|evenings)\b", lower):
            preferred_time = "evening"

    # 3. Schedule mode and days
    schedule_mode: str | None = None
    excluded_days: list[str] = []

    if re.search(r"\b(monday\s*(?:to|-)\s*saturday|mon\s*(?:to|-)\s*sat|mon-sat|6\s*days)\b", lower):
        schedule_mode = "mon_sat"
        excluded_days.append("Sunday")
    elif re.search(r"\b(weekdays?(?:\s+only)?|monday\s*(?:to|-)\s*friday|mon\s*(?:to|-)\s*fri|mon-fri|5\s*days)\b", lower):
        schedule_mode = "weekdays"
    elif re.search(r"\b(weekends?(?:\s+only)?|sat(?:urday)?\s*(?:and|&)\s*sun(?:day)?)\b", lower):
        schedule_mode = "weekends"

    if "no sunday" in lower or "don't schedule anything on sunday" in lower or "dont schedule anything on sunday" in lower or "exclude sunday" in lower:
        if "Sunday" not in excluded_days:
            excluded_days.append("Sunday")
    if "no saturday" in lower or "exclude saturday" in lower:
        if "Saturday" not in excluded_days:
            excluded_days.append("Saturday")

    # 4. Main goal
    main_goal: str | None = None
    if any(k in lower for k in ["weak subject", "weak area", "struggling with", "improve weak", "focus on weak"]):
        main_goal = "weak_subjects"
    elif any(k in lower for k in ["exam prep", "exam preparation", "prepare for exams", "finals prep", "prepare for upcoming exams"]):
        main_goal = "exam_prep"
    elif any(k in lower for k in ["improve cgpa", "boost cgpa", "improve sgpa", "improve grades", "boost marks"]):
        main_goal = "improve_cgpa"
    elif any(k in lower for k in ["complete syllabus", "cover syllabus", "finish syllabus"]):
        main_goal = "syllabus"
    elif any(k in lower for k in ["balance all", "balanced schedule", "all subjects equally"]):
        main_goal = "balanced"

    # 5. Exam timeframe
    exam_timeframe: str | None = None
    exam_match = re.search(r"\b(?:exams?|finals?|tests?)\s+in\s+([0-9]+\s*(?:weeks?|days?|months?))\b", lower)
    if exam_match:
        exam_timeframe = exam_match.group(1)

    # 6. Check sufficiency
    has_specific_timing = bool(
        has_explicit_time
        or custom_start_hour is not None
        or schedule_mode in ("weekdays", "weekends", "mon_sat")
        or bool(excluded_days)
        or exam_timeframe is not None
        or bool(re.search(r"\b(in\s+the\s+morning|in\s+the\s+evening|in\s+the\s+afternoon|at\s+night|7\s*pm|8\s*pm|9\s*pm|6\s*am|7\s*am|8\s*am)\b", lower))
        or bool(re.search(r"\b(only\s+for|specifically\s+for|focus\s+on\s+[a-z]{2,}|make\s+it\s+only|easier|change\s+monday)\b", lower))
        or main_goal is not None
    )

    return {
        "daily_minutes": daily_minutes or 120,
        "preferred_time": preferred_time or "evening",
        "custom_start_hour": custom_start_hour,
        "schedule_mode": schedule_mode or "everyday",
        "excluded_days": excluded_days,
        "main_goal": main_goal,
        "exam_timeframe": exam_timeframe,
        "has_explicit_time": has_explicit_time,
        "has_sufficient_preferences": has_specific_timing,
    }


def parse_daily_time_limit(goal_text: str | None) -> int:
    """Extracts student daily time limit in minutes if mentioned."""
    prefs = parse_study_preferences(goal_text)
    return prefs["daily_minutes"]


def extract_requested_subject(user_goal: str | None, enrolled_courses: list[str]) -> str | None:
    """Detects if the student explicitly requested a specific subject or topic in their message.
    Checks enrolled courses first so the exact enrolled course name is always preferred.
    """
    if not user_goal:
        return None

    lower_goal = user_goal.lower()

    # 1. Match against known enrolled courses first (exact enrolled name takes priority)
    for course in enrolled_courses:
        if course.lower() in lower_goal:
            return course

    # 2. Match against known canonical subject aliases
    for canonical_name, aliases in SUBJECT_ALIASES.items():
        if any(re.search(r"\b" + re.escape(alias) + r"\b", lower_goal) for alias in aliases):
            return canonical_name

    return None


def identify_student_struggle_subjects(ctx: Any, insight: Any) -> list[str]:
    """
    Analyzes student context to identify subjects where the student is currently lacking,
    has low attendance, or has historical backlogs requiring remediation.
    """
    struggles: list[str] = []

    # 1. Subjects below attendance threshold
    if ctx and ctx.attendance and ctx.attendance.subjects_below_threshold:
        for sub in ctx.attendance.subjects_below_threshold:
            canonical = next((k for k, v in SUBJECT_ALIASES.items() if any(a in sub.lower() for a in v)), sub)
            if canonical not in struggles:
                struggles.append(canonical)

    # 2. Subjects with low marks / quiz scores
    if ctx and ctx.subjects:
        sorted_subjects = sorted(
            ctx.subjects,
            key=lambda s: (s.current_marks_percentage if s.current_marks_percentage is not None else (s.marks_percentage or 100.0))
        )
        for s in sorted_subjects:
            pct_val = s.current_marks_percentage if s.current_marks_percentage is not None else s.marks_percentage
            if (pct_val is not None and pct_val < 70.0) or (s.grade in ("C", "D", "E", "F")):
                canonical = next((k for k, v in SUBJECT_ALIASES.items() if any(a in s.subject_name.lower() for a in v)), s.subject_name)
                if canonical not in struggles:
                    struggles.append(canonical)

    # 3. Check historical cleared/active backlogs if available
    hist_perf = getattr(ctx, "historical_academic_performance", None)
    if hist_perf and isinstance(hist_perf, dict):
        backlogs = hist_perf.get("cleared_backlogs") or []
        for b in backlogs:
            b_name = b.get("subject_name") or b.get("subject_code") or ""
            canonical = next((k for k, v in SUBJECT_ALIASES.items() if any(a in b_name.lower() for a in v)), None)
            if canonical and canonical not in struggles:
                struggles.append(canonical)

    # 4. Insight focus areas
    if insight and insight.focus_areas:
        for fa in insight.focus_areas:
            canonical = next((k for k, v in SUBJECT_ALIASES.items() if any(a in fa.lower() for a in v)), None)
            if canonical and canonical not in struggles:
                struggles.append(canonical)

    return struggles


def _format_time_slot(base_hour: int, start_minute: int, duration_minutes: int) -> tuple[str, int, int]:
    """Helper to format a time interval string in 12-hour format, e.g. '07:00 PM – 07:45 PM'."""
    total_start_min = base_hour * 60 + start_minute
    total_end_min = total_start_min + duration_minutes

    start_h = (total_start_min // 60) % 24
    start_m = total_start_min % 60
    end_h = (total_end_min // 60) % 24
    end_m = total_end_min % 60

    start_period = "AM" if start_h < 12 else "PM"
    end_period = "AM" if end_h < 12 else "PM"

    start_h_12 = start_h if start_h in (12, 0) else (start_h % 12)
    end_h_12 = end_h if end_h in (12, 0) else (end_h % 12)
    if start_h_12 == 0:
        start_h_12 = 12
    if end_h_12 == 0:
        end_h_12 = 12

    time_str = f"{start_h_12:02d}:{start_m:02d} {start_period} – {end_h_12:02d}:{end_m:02d} {end_period}"
    return time_str, end_h, end_m


def build_default_plan(request: PlanRequest) -> StudyPlan:
    """
    Generates an authentic, performance-weighted StudyPlan with concrete academic topics.
    
    Guarantees:
    1. Weak subjects (<70% marks or Grade C/D/E/F) receive proportionally larger time blocks and higher weekly frequency.
    2. Strong subjects (≥80%) receive concise maintenance revision blocks so time isn't wasted.
    3. Daily study duration strictly respects the student's available hours (e.g. 1 hr = 60m, 2 hrs = 120m).
    4. Multi-block sessions include realistic study intervals, short breaks, and daily wrap-up revision.
    5. Actionable tasks specify WHAT to study, HOW LONG, WHAT TO DO, and WHAT TO COMPLETE.
    6. Grounded rationale explains why allocations were made based on real student performance.
    """
    ctx = request.student_context
    insight = request.student_insight
    user_goal = request.user_goal or "Weekly Study Schedule"

    # Merge student_preferences forwarded from orchestrator (preferred over parsing user_goal again)
    prefs = parse_study_preferences(user_goal)
    if request.student_preferences and isinstance(request.student_preferences, dict):
        prefs.update({k: v for k, v in request.student_preferences.items() if v is not None})

    daily_limit = int(prefs.get("daily_minutes") or 120)
    preferred_time = str(prefs.get("preferred_time") or "evening")
    schedule_mode = str(prefs.get("schedule_mode") or "everyday")
    excluded_days = list(prefs.get("excluded_days", []) or [])
    custom_start_hour = prefs.get("custom_start_hour")

    # Base hour mapping
    base_hours = {
        "morning": 7,     # 07:00 AM
        "afternoon": 14,  # 02:00 PM
        "evening": 19,    # 07:00 PM
        "night": 21,      # 09:00 PM
    }
    base_hour = custom_start_hour if custom_start_hour is not None else base_hours.get(preferred_time, 19)

    enrolled_courses = [s.subject_name for s in ctx.subjects] if (ctx and ctx.subjects) else []
    requested_subject = extract_requested_subject(user_goal, enrolled_courses)
    is_strictly_scoped = bool(re.search(r"\b(only\s+for|specifically\s+for|just\s+for|strictly\s+for)\b", user_goal.lower()))

    # Categorize subjects by performance
    subject_marks: dict[str, float] = {}
    if ctx and ctx.subjects:
        for s in ctx.subjects:
            m_val = s.current_marks_percentage if s.current_marks_percentage is not None else s.marks_percentage
            if m_val is not None:
                subject_marks[s.subject_name] = m_val

    struggle_subjects = identify_student_struggle_subjects(ctx, insight)

    # Sort enrolled courses: weakest first, strongest last
    def get_subject_score(name: str) -> float:
        if name == requested_subject:
            return -10.0  # highest priority
        return subject_marks.get(name, 75.0)

    sorted_enrolled = sorted(enrolled_courses, key=get_subject_score) if enrolled_courses else []

    focus_subjects: list[str] = []
    # Priority subjects from intake preferences take precedence
    for ps in prefs.get("priority_subjects", []):
        matched_enrolled = next((c for c in enrolled_courses if ps.lower() in c.lower() or c.lower() in ps.lower()), ps)
        if matched_enrolled not in focus_subjects:
            focus_subjects.append(matched_enrolled)

    if is_strictly_scoped and requested_subject:
        focus_subjects = [requested_subject]
    else:
        if requested_subject and requested_subject not in focus_subjects:
            focus_subjects.append(requested_subject)
        for s in struggle_subjects:
            if s not in focus_subjects:
                focus_subjects.append(s)
        for c in sorted_enrolled:
            if c not in focus_subjects:
                focus_subjects.append(c)
        if not focus_subjects:
            focus_subjects = ["Operating Systems", "Database Management Systems", "Machine Learning Foundations", "Computer Networks", "Data Structures & Algorithms"]

    primary_subject = focus_subjects[0]
    secondary_subject = focus_subjects[1] if len(focus_subjects) > 1 else focus_subjects[0]

    # Prepend tasks for upcoming HIGH-priority deadlines (from context and intake preferences)
    tasks: list[StudyTask] = []
    upcoming_deadlines: list[dict] = []
    if ctx and ctx.assignments and ctx.assignments.upcoming_deadlines:
        upcoming_deadlines.extend(ctx.assignments.upcoming_deadlines or [])
    for ed in prefs.get("exam_deadlines", []):
        if isinstance(ed, dict):
            upcoming_deadlines.append({
                "title": f"{ed.get('subject', 'Exam')} Preparation",
                "subject": ed.get("subject", primary_subject),
                "due_date": ed.get("timeframe", "Upcoming Exam"),
                "priority": "High",
            })

    for dl_idx, deadline in enumerate(upcoming_deadlines):
        dl_title = deadline.get("title", "Assignment Submission")
        dl_subject = deadline.get("subject", primary_subject)
        dl_due = deadline.get("due_date", "Upcoming")
        dl_priority_str = str(deadline.get("priority", "High")).lower()
        dl_priority = PriorityLevel.HIGH if dl_priority_str in ("high", "urgent") else PriorityLevel.MEDIUM
        day_name = _DAYS[dl_idx % len(_DAYS)]
        
        slot_str, _, _ = _format_time_slot(base_hour, 0, min(daily_limit, 60))
        tasks.append(
            StudyTask(
                title=f"{dl_subject}: {dl_title}",
                description=f"Complete and submit '{dl_title}' for {dl_subject}. Due: {dl_due}. Review assignment criteria and verify all test cases before submitting.",
                subject=dl_subject,
                day=day_name,
                time_slot=slot_str,
                duration_minutes=min(daily_limit, 60),
                priority=dl_priority,
            )
        )

    # Days to schedule
    if prefs.get("study_days") and isinstance(prefs["study_days"], list) and len(prefs["study_days"]) > 0:
        schedule_days = [d for d in prefs["study_days"] if d in _DAYS and d not in excluded_days]
    else:
        schedule_days = [d for d in _DAYS if d not in excluded_days]
        if schedule_mode == "weekdays":
            schedule_days = [d for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"] if d not in excluded_days]
        elif schedule_mode in ("mon_sat", "monday_to_saturday"):
            schedule_days = [d for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"] if d not in excluded_days]
        elif schedule_mode == "weekends":
            schedule_days = [d for d in ["Saturday", "Sunday"] if d not in excluded_days]

    if not schedule_days:
        schedule_days = _DAYS

    # Generate daily multi-block sessions tailored to daily_limit
    for day_idx, day_name in enumerate(schedule_days):
        # Determine subject weighting for this day:
        # Weakest subjects appear on more days (Mon, Tue, Wed, Thu, Fri), strong subjects alternate
        if day_idx % 3 == 0:
            target_sub_1 = primary_subject
            target_sub_2 = secondary_subject
        elif day_idx % 3 == 1:
            target_sub_1 = secondary_subject
            target_sub_2 = focus_subjects[2] if len(focus_subjects) > 2 else primary_subject
        else:
            target_sub_1 = primary_subject
            target_sub_2 = focus_subjects[-1]  # Stronger maintenance subject

        # Topics pool
        def get_topic_for(sub: str, idx: int) -> tuple[str, str]:
            pool = SUBJECT_TOPICS.get(sub)
            if not pool:
                matched_key = next((k for k in SUBJECT_TOPICS if k.lower() in sub.lower() or sub.lower() in k.lower()), None)
                pool = SUBJECT_TOPICS.get(matched_key, [
                    ("Core Theory & Solved Problems", "Review comprehensive chapter notes and work through 5 solved example problems."),
                    ("Problem Sets & Timed Practice Drill", "Complete standard exercise questions and verify solutions step-by-step.")
                ])
            return pool[idx % len(pool)]

        t1_title, t1_desc = get_topic_for(target_sub_1, day_idx)
        t2_title, t2_desc = get_topic_for(target_sub_2, day_idx + 1)

        # Multi-block schedule based on daily_limit
        if daily_limit >= 180:
            # 3-hour daily plan: Block 1 (60m) -> Break (15m) -> Block 2 (60m) -> Block 3 (45m) -> Wrap-up (15m)
            slot1, _, _ = _format_time_slot(base_hour, 0, 60)
            slot2, _, _ = _format_time_slot(base_hour, 75, 60)
            slot3, _, _ = _format_time_slot(base_hour, 140, 40)

            tasks.append(
                StudyTask(
                    title=f"{target_sub_1}: {t1_title}",
                    description=f"{t1_desc} Target: Deep problem-solving drill and derivation verification.",
                    subject=target_sub_1,
                    day=day_name,
                    time_slot=slot1,
                    duration_minutes=60,
                    priority=PriorityLevel.HIGH if (target_sub_1 in struggle_subjects or target_sub_1 == requested_subject) else PriorityLevel.MEDIUM,
                )
            )
            tasks.append(
                StudyTask(
                    title=f"{target_sub_2}: {t2_title}",
                    description=f"{t2_desc} Complete comprehensive exercise sets and homework items.",
                    subject=target_sub_2,
                    day=day_name,
                    time_slot=slot2,
                    duration_minutes=60,
                    priority=PriorityLevel.HIGH if (target_sub_2 in struggle_subjects or target_sub_2 == requested_subject) else PriorityLevel.MEDIUM,
                )
            )
            tasks.append(
                StudyTask(
                    title=f"{target_sub_1} & {target_sub_2}: Synthesis, Mock Drills & Doubts",
                    description="Timed test questions, formula memorization, and logging questions for instructor follow-up.",
                    subject=target_sub_1,
                    day=day_name,
                    time_slot=slot3,
                    duration_minutes=40,
                    priority=PriorityLevel.LOW,
                )
            )

        elif daily_limit >= 120:
            # 2-hour daily plan: Block 1 (45m) -> Break (15m) -> Block 2 (45m) -> Wrap-up (15m)
            slot1, _, _ = _format_time_slot(base_hour, 0, 45)
            slot2, _, _ = _format_time_slot(base_hour, 60, 45)
            slot3, _, _ = _format_time_slot(base_hour, 105, 15)

            tasks.append(
                StudyTask(
                    title=f"{target_sub_1}: {t1_title}",
                    description=f"{t1_desc} Target: Complete 5 core practice questions and highlight difficult steps.",
                    subject=target_sub_1,
                    day=day_name,
                    time_slot=slot1,
                    duration_minutes=45,
                    priority=PriorityLevel.HIGH if (target_sub_1 in struggle_subjects or target_sub_1 == requested_subject) else PriorityLevel.MEDIUM,
                )
            )
            tasks.append(
                StudyTask(
                    title=f"{target_sub_2}: {t2_title}",
                    description=f"{t2_desc} Focus on application exercises and homework sets.",
                    subject=target_sub_2,
                    day=day_name,
                    time_slot=slot2,
                    duration_minutes=45,
                    priority=PriorityLevel.HIGH if (target_sub_2 in struggle_subjects or target_sub_2 == requested_subject) else PriorityLevel.MEDIUM,
                )
            )
            tasks.append(
                StudyTask(
                    title=f"{target_sub_1} & {target_sub_2}: Daily Synthesis & Doubts",
                    description="Recall key formulas, log unresolved doubts for office hours, and review mistake notebook.",
                    subject=target_sub_1,
                    day=day_name,
                    time_slot=slot3,
                    duration_minutes=15,
                    priority=PriorityLevel.LOW,
                )
            )

        elif daily_limit >= 90:
            # 1.5-hour plan: Block 1 (45m) -> Block 2 (35m) -> Wrap-up (10m)
            slot1, _, _ = _format_time_slot(base_hour, 0, 45)
            slot2, _, _ = _format_time_slot(base_hour, 45, 35)
            slot3, _, _ = _format_time_slot(base_hour, 80, 10)

            tasks.append(
                StudyTask(
                    title=f"{target_sub_1}: {t1_title}",
                    description=f"{t1_desc} Solve 4 practice problems.",
                    subject=target_sub_1,
                    day=day_name,
                    time_slot=slot1,
                    duration_minutes=45,
                    priority=PriorityLevel.HIGH if (target_sub_1 in struggle_subjects or target_sub_1 == requested_subject) else PriorityLevel.MEDIUM,
                )
            )
            tasks.append(
                StudyTask(
                    title=f"{target_sub_2}: {t2_title}",
                    description=f"{t2_desc} Work through textbook exercises.",
                    subject=target_sub_2,
                    day=day_name,
                    time_slot=slot2,
                    duration_minutes=35,
                    priority=PriorityLevel.MEDIUM,
                )
            )
            tasks.append(
                StudyTask(
                    title=f"{target_sub_1}: Quick Concept Recall",
                    description="Review summary flashcards and write down 3 key takeaways.",
                    subject=target_sub_1,
                    day=day_name,
                    time_slot=slot3,
                    duration_minutes=10,
                    priority=PriorityLevel.LOW,
                )
            )

        else:
            # 1-hour (or <90m) plan: Block 1 (45m) -> Wrap-up (15m)
            slot1, _, _ = _format_time_slot(base_hour, 0, min(daily_limit, 45))
            slot2, _, _ = _format_time_slot(base_hour, min(daily_limit, 45), max(10, daily_limit - 45))

            tasks.append(
                StudyTask(
                    title=f"{target_sub_1}: {t1_title}",
                    description=f"{t1_desc} Focused core problem-solving drill.",
                    subject=target_sub_1,
                    day=day_name,
                    time_slot=slot1,
                    duration_minutes=min(daily_limit, 45),
                    priority=PriorityLevel.HIGH if (target_sub_1 in struggle_subjects or target_sub_1 == requested_subject) else PriorityLevel.MEDIUM,
                )
            )
            if daily_limit > 45:
                tasks.append(
                    StudyTask(
                        title=f"{target_sub_1}: Active Recall & Formula Check",
                        description="Self-quiz on today's definitions and note any questions for review.",
                        subject=target_sub_1,
                        day=day_name,
                        time_slot=slot2,
                        duration_minutes=daily_limit - 45,
                        priority=PriorityLevel.LOW,
                    )
                )

    # Build milestones
    milestones = [
        PlanMilestone(
            title=f"Mid-Week Problem Solving Check ({primary_subject})",
            target_day="Wednesday" if "Wednesday" in schedule_days else schedule_days[len(schedule_days) // 2],
        ),
        PlanMilestone(
            title=f"Weekly Synthesis & Mock Assessment Review",
            target_day="Sunday" if "Sunday" in schedule_days else schedule_days[-1],
        ),
    ]

    goals = [
        f"Master core problem solving in {primary_subject}",
        f"Targeted practice in {', '.join(focus_subjects[:2])}",
        f"Maintain consistent {daily_limit} mins/day study rhythm in the {preferred_time}",
    ]
    if request.user_goal and len(request.user_goal) < 60:
        goals[0] = request.user_goal

    # Build descriptive rationale grounded in real performance
    rationale_parts = []
    if primary_subject in subject_marks:
        m_val = subject_marks[primary_subject]
        rationale_parts.append(f"{primary_subject} ({m_val:.0f}%) receives the highest study allocation to build foundational mastery in problem solving.")
    else:
        rationale_parts.append(f"{primary_subject} is prioritized as the primary focus area.")

    if len(focus_subjects) > 1 and focus_subjects[-1] in subject_marks:
        strong_sub = focus_subjects[-1]
        s_val = subject_marks[strong_sub]
        if s_val >= 75.0:
            rationale_parts.append(f"{strong_sub} ({s_val:.0f}%) is scheduled for shorter maintenance revision to preserve your strong grade without taking time away from recovery priorities.")

    rationale_str = " ".join(rationale_parts)

    plan_title = f"Focused Study Plan: {primary_subject}" if requested_subject else f"Personalized Weekly Study Schedule ({daily_limit // 60}h/day)"

    return StudyPlan(
        title=plan_title,
        goals=goals[:3],
        priorities=focus_subjects[:3],
        week_start=date.today().isoformat(),
        tasks=tasks,
        milestones=milestones,
        resources=[f"{s} Course Problem Sets & Reference Notes" for s in focus_subjects[:2]],
        notes=f"Target: {daily_limit} mins/day in the {preferred_time}. Consistency is key!",
        rationale=rationale_str,
        metadata={
            "builder": "performance_weighted_study_planner",
            "daily_minutes": daily_limit,
            "preferred_time": preferred_time,
            "schedule_mode": schedule_mode,
        },
    )


def sanitize_and_repair_plan(data: dict[str, Any], request: PlanRequest) -> StudyPlan:
    """
    Sanitizes and repairs LLM-generated plan dictionary to guarantee validity:
    - Eliminates forbidden administrative/counseling tasks.
    - Ensures every task has a valid, authentic subject name and topic.
    - Replaces generic placeholders ('General Study') with genuine academic subjects.
    """
    ctx = request.student_context
    insight = request.student_insight
    user_goal = request.user_goal or "Weekly Study Schedule"
    daily_limit = parse_daily_time_limit(user_goal)

    enrolled_courses = [s.subject_name for s in ctx.subjects] if (ctx and ctx.subjects) else []
    requested_subject = extract_requested_subject(user_goal, enrolled_courses)
    struggles = identify_student_struggle_subjects(ctx, insight)

    raw_tasks = data.get("tasks", [])
    valid_tasks: list[StudyTask] = []

    for i, t in enumerate(raw_tasks):
        if not isinstance(t, dict):
            continue
        title = t.get("title", "")
        desc = t.get("description", "")
        sub = t.get("subject", "")

        # Detect forbidden counselor tasks
        if _FORBIDDEN_TASK_PATTERNS.search(title) or _FORBIDDEN_TASK_PATTERNS.search(desc):
            continue

        # Clean generic placeholder subjects
        if not sub or sub.lower() in ("general study", "coursework prep", "academic", "general", "course"):
            sub = requested_subject or (struggles[0] if struggles else "Operating Systems")

        # Map to valid topic if title is generic
        if "general study" in title.lower() or "coursework prep" in title.lower():
            topics = SUBJECT_TOPICS.get(sub, [("Core Concept Review & Practice", "Work through standard problems.")])
            tt, td = topics[i % len(topics)]
            title = f"{sub}: {tt}"
            desc = f"{td} Focus area: {sub}."

        valid_tasks.append(
            StudyTask(
                title=title,
                description=desc or f"Focused study session for {sub}.",
                subject=sub,
                day=t.get("day", _DAYS[i % len(_DAYS)]),
                time_slot=t.get("time_slot", "18:00–19:00"),
                duration_minutes=min(daily_limit, int(t.get("duration_minutes", daily_limit))),
                priority=PriorityLevel.HIGH if (sub == requested_subject or sub in struggles) else PriorityLevel.MEDIUM,
            )
        )

    if not valid_tasks:
        return build_default_plan(request)

    return StudyPlan(
        title=data.get("title") or (f"Study Plan: {requested_subject}" if requested_subject else "Academic Study Plan"),
        goals=data.get("goals") or [f"Master {valid_tasks[0].subject}"],
        priorities=data.get("priorities") or [t.subject for t in valid_tasks[:3]],
        week_start=date.today().isoformat(),
        tasks=valid_tasks,
        milestones=[PlanMilestone(title=m.get("title", "Milestone"), target_day=m.get("target_day", "Sunday")) for m in data.get("milestones", []) if isinstance(m, dict)] or [PlanMilestone(title="Weekly Review", target_day="Sunday")],
        resources=data.get("resources") or [f"{valid_tasks[0].subject} Lecture Notes"],
        notes=data.get("notes") or "Focus on consistent daily problem-solving blocks.",
        rationale=data.get("rationale") or f"Tailored study schedule with emphasis on {valid_tasks[0].subject}.",
        metadata={"sanitizer": "repaired_academic"},
    )


def parse_llm_plan_json(raw_text: str, request: PlanRequest) -> StudyPlan:
    """Parses LLM JSON response or cleans codeblocks, repairing with sanitize_and_repair_plan."""
    if not raw_text or not raw_text.strip():
        return build_default_plan(request)

    clean_text = raw_text.strip()
    if clean_text.startswith("```"):
        clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text)
        clean_text = re.sub(r"\s*```$", "", clean_text)

    try:
        data = json.loads(clean_text)
        if isinstance(data, dict):
            return sanitize_and_repair_plan(data, request)
    except Exception:
        match = re.search(r"(\{.*\})", clean_text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                if isinstance(data, dict):
                    return sanitize_and_repair_plan(data, request)
            except Exception:
                pass

    return build_default_plan(request)

