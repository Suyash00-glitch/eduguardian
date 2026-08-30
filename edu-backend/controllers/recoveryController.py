import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException


# Official NMAMIT ISE Sem 5 Course Catalog with detailed academic modules
ISE_SEM5_CURRICULUM = {
    "Operating Systems": {
        "code": "IS2003-1",
        "name": "Operating Systems",
        "faculty": "Ms. Prathyakshini",
        "topics": [
            "Process Synchronization, Semaphores, and Classic IPC Problems",
            "CPU Scheduling Algorithms (FCFS, SJF, Round Robin) & Paging",
            "Deadlock Detection, Prevention & Banker's Algorithm",
            "Virtual Memory Management & Page Replacement (LRU, FIFO)"
        ]
    },
    "Database Management Systems": {
        "code": "IS2001-1",
        "name": "Database Management Systems",
        "faculty": "Dr. Preethi Salian K",
        "topics": [
            "Relational Algebra, Complex SQL Joins & Aggregate Queries",
            "Schema Normalization (1NF, 2NF, 3NF, BCNF) & Functional Dependencies",
            "Transaction Management, ACID Properties & Concurrency Control",
            "B+ Tree Indexing & Query Execution Optimization"
        ]
    },
    "Machine Learning Foundations": {
        "code": "IS2002-1",
        "name": "Machine Learning Foundations",
        "faculty": "Dr. Ramesh G",
        "topics": [
            "Supervised Learning: Linear Regression, Cost Function & Gradient Descent",
            "Classification: Logistic Regression, Decision Trees & Random Forests",
            "Support Vector Machines (SVM) & Kernel Functions",
            "Hands-on Jupyter Lab: Model Evaluation, Cross-Validation & ROC Curves"
        ]
    },
    "Computer Networks": {
        "code": "IS2004-1",
        "name": "Computer Networks & Data Communications",
        "faculty": "Faculty Mentor",
        "topics": [
            "TCP/IP and OSI Reference Models & Packet Flow",
            "IP Addressing, Subnet Masking (CIDR) & IPv6 Transitions",
            "Distance Vector & Link State Routing Algorithms (OSPF, BGP)",
            "Transport Layer Protocols: TCP Congestion Control vs UDP"
        ]
    },
    "Software Engineering": {
        "code": "IS2005-1",
        "name": "Software Engineering & Agile Methodologies",
        "faculty": "Faculty Mentor",
        "topics": [
            "Agile Scrum Framework, Sprint Planning & User Story Estimation",
            "Object-Oriented Design Patterns (Factory, Singleton, Observer)",
            "Automated Software Testing: Unit, Integration & CI/CD Pipelines"
        ]
    },
    "Universal Human Values": {
        "code": "HU2001-1",
        "name": "Universal Human Values & Professional Ethics",
        "faculty": "Dr. Preethi Salian K",
        "topics": [
            "Self-Exploration, Human Aspirations & Value Fulfillment",
            "Harmony in the Human Being & Society",
            "Professional Ethics and Holistic Living Guidelines"
        ]
    },
    "Discrete Mathematics": {
        "code": "22MAT31",
        "name": "Discrete Mathematical Structures (Remedial)",
        "faculty": "Mathematics Cell",
        "topics": [
            "Set Theory, Relations & Equivalence Classes",
            "Propositional Logic, Predicates & Quantifiers",
            "Graph Theory: Eulerian & Hamiltonian Paths, Trees & Spanning"
        ]
    }
}


def _extract_requested_subjects(prompt: str) -> List[str]:
    """
    Parses user query/prompt to detect if specific subjects are targeted.
    """
    if not prompt:
        return []
    p_lower = prompt.lower()
    matched = []
    
    keywords_map = {
        "Operating Systems": ["operating system", "os", "is2003", "semaphores", "deadlock", "paging"],
        "Database Management Systems": ["database", "dbms", "sql", "is2001", "normalization", "rdbms"],
        "Machine Learning Foundations": ["machine learning", "ml", "is2002", "regression", "svm", "dataset"],
        "Computer Networks": ["computer network", "networks", "cn", "is2004", "tcp", "ip", "routing", "subnet"],
        "Software Engineering": ["software engineering", "se", "is2005", "agile", "scrum", "design pattern"],
        "Universal Human Values": ["universal human values", "uhv", "ethics", "hu2001"],
        "Discrete Mathematics": ["math", "maths", "mathematics", "discrete", "22mat31", "calculus"]
    }
    
    for sub, kws in keywords_map.items():
        if any(kw in p_lower for kw in kws):
            matched.append(sub)
            
    return matched


def get_default_recovery_plan_for_student(
    student_context: Optional[Dict[str, Any]],
    user_info: Optional[Dict[str, Any]],
    custom_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates an authentic, subject-grounded AI academic study & recovery plan
    tailored to the student's active semester curriculum, risk profile, and specific requests.
    """
    risk_eval = (student_context or {}).get("risk_evaluation", {})
    risk_level = (risk_eval.get("risk_level") or "low").lower()
    hist_perf = (student_context or {}).get("historical_academic_performance", {})
    cgpa = hist_perf.get("cgpa", 7.5)
    cleared_backlogs = hist_perf.get("cleared_backlogs", [])
    name = (student_context or {}).get("identity", {}).get("name") or (user_info or {}).get("full_name") or "Student"
    
    # Check if user specifically requested targeted subjects in their prompt
    requested_subjects = _extract_requested_subjects(custom_prompt or "")
    
    # Target subject selection
    if requested_subjects:
        selected_subjects = requested_subjects
    else:
        # Default distribution across core 5th Sem ISE active courses
        if risk_level == "high" or (cgpa and cgpa < 6.0):
            # Prioritize core analytical courses + remediation
            selected_subjects = [
                "Operating Systems",
                "Database Management Systems",
                "Machine Learning Foundations",
                "Computer Networks"
            ]
            if len(cleared_backlogs) > 0:
                selected_subjects.append("Discrete Mathematics")
        elif risk_level == "medium":
            selected_subjects = [
                "Machine Learning Foundations",
                "Operating Systems",
                "Database Management Systems",
                "Computer Networks"
            ]
        else:
            selected_subjects = [
                "Machine Learning Foundations",
                "Operating Systems",
                "Database Management Systems",
                "Software Engineering"
            ]

    now = datetime.now()
    goals = []

    for idx, sub_name in enumerate(selected_subjects):
        course_info = ISE_SEM5_CURRICULUM.get(sub_name, {
            "code": f"IS{2001+idx}-1",
            "name": sub_name,
            "faculty": "Department Faculty",
            "topics": ["Core module lecture review", "Problem-solving drill", "Lab assignment completion"]
        })
        
        code = course_info["code"]
        topics = course_info["topics"]
        topic_primary = topics[0] if len(topics) > 0 else "Core Concept Review"
        topic_secondary = topics[1] if len(topics) > 1 else "Question Bank Practice"
        
        target_date = (now + timedelta(days=(idx * 2) + 2)).strftime("%b %d, %Y")
        
        if risk_level == "high" or (cgpa and cgpa < 6.0):
            goal_title = f"{code} · {course_info['name']} (High-Priority Revision)"
            category = "Remediation & Exam Prep"
            description = (
                f"Master key fundamentals for {course_info['name']} ({code}). "
                f"Focus on {topic_primary} and complete solved examples for {topic_secondary}."
            )
            time_est = "45–60 mins"
            priority = "high" if idx < 2 else "medium"
            impact = "High Impact (CIE Target: 40+/50)"
            steps = [
                f"Work through textbook derivations and solved problems on {topic_primary}",
                f"Solve 2 previous CIE exam question papers under timed conditions",
                f"Verify doubts with course instructor {course_info.get('faculty', 'Faculty Mentor')}"
            ]
        elif risk_level == "medium":
            goal_title = f"{code} · {course_info['name']} (Concept & Practice Drill)"
            category = "Academic Strengthening"
            description = (
                f"Consolidate weekly module notes for {course_info['name']} ({code}). "
                f"Cover {topic_primary} and practice analytical questions on {topic_secondary}."
            )
            time_est = "45 mins"
            priority = "medium"
            impact = "Score Booster"
            steps = [
                f"Synthesize 1-page summary sheet covering {topic_primary}",
                f"Implement practice algorithms and solve numerical exercises on {topic_secondary}",
                "Review assignment specifications 24 hours prior to submission"
            ]
        else:
            goal_title = f"{code} · {course_info['name']} (Advanced Mastery & Lab)"
            category = "Distinction Track"
            description = (
                f"Advanced mastery in {course_info['name']} ({code}). "
                f"Implement hands-on lab code for {topic_primary} and optimize problem sets."
            )
            time_est = "45 mins"
            priority = "medium"
            impact = "Distinction Maintenance"
            steps = [
                f"Implement clean code repository covering {topic_primary}",
                f"Tackle challenging conceptual problems on {topic_secondary}",
                "Prepare comprehensive lab observation and viva documentation"
            ]

        goals.append({
            "id": f"task-sem5-{idx+1}",
            "title": goal_title,
            "category": category,
            "description": description,
            "dueDate": target_date,
            "completed": (idx == 0 and risk_level == "low"),
            "priority": priority,
            "impact": impact,
            "timeEstimate": time_est,
            "steps": steps
        })

    # Add Attendance / Faculty Mentorship Milestone for at-risk students
    if risk_level == "high" or (cgpa and cgpa < 6.0):
        goals.append({
            "id": f"task-sem5-{len(goals)+1}",
            "title": "Semester 5 Attendance & CIE Eligibility Safeguard",
            "category": "Attendance & Mentorship",
            "description": (
                "Maintain 100% lecture attendance across all 5th Semester ISE theory and lab sessions "
                "to meet the mandatory institutional 75% cutoff and avoid examination detention."
            ),
            "dueDate": (now + timedelta(days=12)).strftime("%b %d, %Y"),
            "completed": False,
            "priority": "critical",
            "impact": "Mandatory University Cutoff",
            "timeEstimate": "Daily Habit",
            "steps": [
                "Attend all scheduled morning theory sessions punctually",
                "Submit lab records and observation logs at end of each lab class",
                "Schedule weekly progress check-in with Faculty Advisor (Dr. Preethi Salian K)"
            ]
        })

    completed_count = sum(1 for g in goals if g.get("completed"))
    total_count = len(goals)
    progress_pct = int(round((completed_count / total_count) * 100)) if total_count > 0 else 0

    custom_label = f" · {', '.join(requested_subjects)}" if requested_subjects else ""
    if custom_prompt:
        title = f"AI Semester 5 Study Blueprint{custom_label}"
        summary = f"AI-synthesized study & recovery schedule for {name} focusing on {', '.join(selected_subjects)}."
    elif risk_level == "high":
        title = "Semester 5 Academic Recovery & Remediation Blueprint"
        summary = f"Custom-tailored academic recovery strategy for {name} (Sem 5 ISE). Focuses on active semester subjects ({', '.join(selected_subjects[:3])}) and attendance recovery."
    else:
        title = "Semester 5 Academic Strengthening & Exam Readiness Plan"
        summary = f"Curriculum-aligned milestone plan for {name} (Sem 5 ISE) covering {', '.join(selected_subjects[:3])}."

    return {
        "title": title,
        "summary": summary,
        "progress": progress_pct,
        "goals": goals,
        "active_subjects": selected_subjects,
        "last_updated": now.isoformat(),
        "generated_by": "EduGuardian AI Academic Coach"
    }


def get_student_recovery_plan(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Fetches the student's active recovery plan from persistent storage or
    generates a personalized default plan using their active semester subjects.
    """
    # 1. Check if custom plan exists in database table
    try:
        row = db.execute(
            text("SELECT plan_data FROM student_recovery_plans WHERE user_id = :uid"),
            {"uid": user_id}
        ).mappings().first()
        if row and row["plan_data"]:
            plan = row["plan_data"]
            if isinstance(plan, str):
                plan = json.loads(plan)
            # Recompute progress
            goals = plan.get("goals", [])
            completed = sum(1 for g in goals if g.get("completed"))
            total = len(goals)
            plan["progress"] = int(round((completed / total) * 100)) if total > 0 else 0
            return plan
    except Exception as e:
        # Table might not exist yet; will create on save
        pass

    # 2. Fetch student context for personalized generation
    from controllers.portalController import get_authenticated_student_context, _PORTAL_CONTEXT_CACHE
    ctx = _PORTAL_CONTEXT_CACHE.get(user_id)
    if not ctx:
        try:
            ctx = get_authenticated_student_context(db, user_id)
        except Exception:
            ctx = None

    user_row = db.execute(
        text("SELECT full_name, email FROM users WHERE id = :uid"),
        {"uid": user_id}
    ).mappings().first()

    default_plan = get_default_recovery_plan_for_student(ctx, user_row)
    save_student_recovery_plan(db, user_id, default_plan)
    return default_plan


def save_student_recovery_plan(db: Session, user_id: int, plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Saves or updates the student's recovery plan in database.
    """
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS student_recovery_plans (
            id serial primary key,
            user_id int unique not null references users(id) on delete cascade,
            plan_data jsonb not null,
            created_at timestamp default current_timestamp,
            updated_at timestamp default current_timestamp
        )
    """))

    goals = plan.get("goals", [])
    completed = sum(1 for g in goals if g.get("completed"))
    total = len(goals)
    plan["progress"] = int(round((completed / total) * 100)) if total > 0 else 0
    plan["last_updated"] = datetime.now().isoformat()

    db.execute(
        text("""
            INSERT INTO student_recovery_plans (user_id, plan_data, updated_at)
            VALUES (:uid, :pdata, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id)
            DO UPDATE SET plan_data = :pdata, updated_at = CURRENT_TIMESTAMP
        """),
        {"uid": user_id, "pdata": json.dumps(plan)}
    )
    db.commit()
    return plan


def toggle_recovery_task(db: Session, user_id: int, task_id: str) -> Dict[str, Any]:
    """
    Toggles completion status for a specific task inside the recovery plan.
    """
    plan = get_student_recovery_plan(db, user_id)
    goals = plan.get("goals", [])
    for g in goals:
        if str(g.get("id")) == str(task_id):
            g["completed"] = not bool(g.get("completed"))
            break

    completed = sum(1 for g in goals if g.get("completed"))
    total = len(goals)
    plan["progress"] = int(round((completed / total) * 100)) if total > 0 else 0

    return save_student_recovery_plan(db, user_id, plan)


def add_ai_study_plan(db: Session, user_id: int, ai_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes an AI-generated study/recovery plan (from chatbot, coach, or prompt)
    and automatically incorporates it into the student's active Recovery Plan.
    """
    existing_plan = get_student_recovery_plan(db, user_id)
    now = datetime.now()
    
    # If the AI plan provides structured tasks/milestones
    raw_tasks = ai_plan.get("tasks") or ai_plan.get("goals") or ai_plan.get("milestones") or []
    
    if isinstance(raw_tasks, list) and len(raw_tasks) > 0:
        formatted_goals = []
        for idx, t in enumerate(raw_tasks):
            if isinstance(t, str):
                formatted_goals.append({
                    "id": f"ai-task-{int(now.timestamp())}-{idx}",
                    "title": t,
                    "category": "AI Study Milestone",
                    "description": f"Targeted study milestone: {t}",
                    "dueDate": (now + timedelta(days=idx+2)).strftime("%b %d, %Y"),
                    "completed": False,
                    "priority": "high",
                    "impact": "High Impact",
                    "timeEstimate": "45 mins",
                    "steps": ["Review core lecture notes", "Complete practice problem set", "Check understanding"]
                })
            elif isinstance(t, dict):
                sub = t.get("subject") or t.get("title") or "Semester 5 Core Course"
                formatted_goals.append({
                    "id": t.get("id") or f"ai-task-{int(now.timestamp())}-{idx}",
                    "title": t.get("title") or f"{sub} · Practice Session",
                    "category": t.get("category") or "AI Study Plan",
                    "description": t.get("description") or t.get("notes") or f"Scheduled focus session for {sub}.",
                    "dueDate": t.get("dueDate") or t.get("due_date") or (now + timedelta(days=idx+2)).strftime("%b %d, %Y"),
                    "completed": bool(t.get("completed", False)),
                    "priority": t.get("priority") or "high",
                    "impact": t.get("impact") or "High Impact",
                    "timeEstimate": t.get("timeEstimate") or t.get("duration_minutes", "45 mins"),
                    "steps": t.get("steps") or ["Review concepts", "Solve practice problems", "Self-assess"]
                })

        new_plan = {
            "title": ai_plan.get("title") or "AI Active Semester Study Blueprint",
            "summary": ai_plan.get("summary") or "Tailored revision schedule generated by your AI Academic Coach.",
            "goals": formatted_goals,
            "progress": 0,
            "generated_by": "EduGuardian AI Academic Coach",
            "last_updated": now.isoformat()
        }
        return save_student_recovery_plan(db, user_id, new_plan)

    return existing_plan
