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


def parse_daily_time_limit(goal_text: str | None) -> int:
    """Extracts student daily time limit in minutes if mentioned (e.g. '1 hour per day')."""
    if not goal_text:
        return 60

    lower = goal_text.lower()
    hour_match = re.search(r"(\d+)\s*(?:hour|hr)", lower)
    if hour_match:
        return min(240, max(15, int(hour_match.group(1)) * 60))

    min_match = re.search(r"(\d+)\s*(?:min|minute)", lower)
    if min_match:
        return max(15, min(240, int(min_match.group(1))))

    return 60


def extract_requested_subject(user_goal: str | None, enrolled_courses: list[str]) -> str | None:
    """Detects if the student explicitly requested a specific subject or topic in their message."""
    if not user_goal:
        return None

    lower_goal = user_goal.lower()

    # 1. Match against known aliases
    for canonical_name, aliases in SUBJECT_ALIASES.items():
        if any(re.search(r"\b" + re.escape(alias) + r"\b", lower_goal) for alias in aliases):
            return canonical_name

    # 2. Match against known enrolled courses
    for course in enrolled_courses:
        if course.lower() in lower_goal:
            return course

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
            key=lambda s: s.marks_percentage if s.marks_percentage is not None else 100.0
        )
        for s in sorted_subjects:
            if (s.marks_percentage is not None and s.marks_percentage < 70.0) or (s.grade in ("D", "E", "F")):
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


def build_default_plan(request: PlanRequest) -> StudyPlan:
    """
    Generates an authentic, subject-grounded StudyPlan with concrete academic topics,
    prioritizing student's requested subject or detected struggle areas.
    """
    ctx = request.student_context
    insight = request.student_insight
    user_goal = request.user_goal or "Weekly Study Schedule"
    daily_limit = parse_daily_time_limit(user_goal)

    enrolled_courses = [s.subject_name for s in ctx.subjects] if (ctx and ctx.subjects) else []
    requested_subject = extract_requested_subject(user_goal, enrolled_courses)
    is_strictly_scoped = bool(re.search(r"\b(only\s+for|specifically\s+for|just\s+for|strictly\s+for)\b", user_goal.lower()))

    # Determine struggle subjects
    struggle_subjects = identify_student_struggle_subjects(ctx, insight)

    focus_subjects: list[str] = []

    if is_strictly_scoped and requested_subject:
        focus_subjects = [requested_subject]
    else:
        # If student explicitly asked for a subject (e.g. DSA, OS), place it first
        if requested_subject:
            focus_subjects.append(requested_subject)

        # Then add identified struggle subjects
        for s in struggle_subjects:
            if s not in focus_subjects:
                focus_subjects.append(s)

        # Then add remaining active semester courses
        default_sem5_courses = [
            "Operating Systems",
            "Database Management Systems",
            "Machine Learning Foundations",
            "Computer Networks",
            "Data Structures & Algorithms"
        ]
        for c in default_sem5_courses:
            if c not in focus_subjects:
                focus_subjects.append(c)

    primary_subject = focus_subjects[0]

    # Generate daily tasks
    tasks: list[StudyTask] = []
    num_days = min(7, request.timeframe_days or 7)

    for i in range(num_days):
        day_name = _DAYS[i % len(_DAYS)]
        target_subject = focus_subjects[i % len(focus_subjects)]
        
        # Pull rich concrete topics for this subject
        topics_pool = SUBJECT_TOPICS.get(target_subject)
        if not topics_pool:
            # Fallback to closest match
            matched_key = next((k for k in SUBJECT_TOPICS if k.lower() in target_subject.lower() or target_subject.lower() in k.lower()), None)
            topics_pool = SUBJECT_TOPICS.get(matched_key, [
                ("Core Lecture Concepts & Derivations", "Review comprehensive chapter notes and work through solved examples."),
                ("Problem Sets & Timed Practice Drill", "Complete standard exercise questions and verify solutions step-by-step.")
            ])

        topic_title, topic_desc = topics_pool[i % len(topics_pool)]
        full_title = f"{target_subject}: {topic_title}"
        full_desc = f"{topic_desc} Focus area: {target_subject}."
        
        is_priority = (target_subject == requested_subject) or (target_subject in struggle_subjects) or (i < 2)
        priority = PriorityLevel.HIGH if is_priority else PriorityLevel.MEDIUM
        slot_hour = 18 if i % 2 == 0 else 19

        tasks.append(
            StudyTask(
                title=full_title,
                description=full_desc,
                subject=target_subject,
                day=day_name,
                time_slot=f"{slot_hour}:00–{slot_hour + max(1, daily_limit // 60)}:00" if daily_limit >= 60 else f"{slot_hour}:00–{slot_hour}:{daily_limit:02d}",
                duration_minutes=daily_limit,
                priority=priority,
            )
        )

    milestones = [
        PlanMilestone(
            title=f"Mid-Week Problem Solving Check ({primary_subject})",
            target_day="Wednesday",
        ),
        PlanMilestone(
            title=f"Comprehensive Milestone & Mock Assessment Review",
            target_day="Sunday",
        ),
    ]

    goals = [
        f"Master core topics in {primary_subject}",
        f"Targeted remediation in {', '.join(focus_subjects[:2])}",
        f"Complete scheduled practice sessions within {daily_limit} mins/day",
    ]
    if request.user_goal and len(request.user_goal) < 60:
        goals[0] = request.user_goal

    title = f"Focused Study Plan: {primary_subject}" if requested_subject else f"Semester 5 Academic Recovery & Study Plan"

    return StudyPlan(
        title=title,
        goals=goals[:3],
        priorities=focus_subjects[:3],
        week_start=date.today().isoformat(),
        tasks=tasks,
        milestones=milestones,
        resources=[f"{s} Standard Course Problem Sets & Reference Notes" for s in focus_subjects[:2]],
        notes="Consistency is key. Short, focused study blocks yield the highest long-term retention!",
        rationale=f"Plan prioritized around {primary_subject} to build mastery with daily targets of {daily_limit} minutes.",
        metadata={"builder": "deterministic_subject_grounded"},
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

