"""
EduGuardian AI 2.0 — Comprehensive Architecture & Concept Guide PDF Generator
=============================================================================
Generates an authoritative, beautifully typeset PDF documentation guide
explaining all concepts, architecture layers, algorithms, microservices,
guardrails, and operational workflows of the EduGuardian platform.
"""

import os
import sys
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and render total page count
    along with running header and running footer on every page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Skip header and footer on cover page (Page 1)
        if self._pageNumber > 1:
            # Header
            self.drawString(54, 11 * 72 - 36, "EduGuardian AI 2.0 — System Architecture & Concept Guide")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)

            # Footer
            self.line(54, 45, 8.5 * 72 - 54, 45)
            self.drawString(54, 32, "Confidential — NMAM Institute of Technology (Nitte) — Hackathon Edition")
            page_str = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(8.5 * 72 - 54, 32, page_str)

        self.restoreState()


def build_pdf(filename="EduGuardian_AI_Architecture_and_Concept_Guide.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0F172A")    # Dark Navy
    SECONDARY = colors.HexColor("#0D9488")  # Teal Accent
    TEXT_DARK = colors.HexColor("#1E293B")  # Slate 800
    TEXT_MUTED = colors.HexColor("#475569") # Slate 600
    BG_LIGHT = colors.HexColor("#F8FAFC")   # Slate 50
    BORDER_COLOR = colors.HexColor("#CBD5E1") # Slate 300
    ACCENT_WARN = colors.HexColor("#D97706") # Amber
    ACCENT_DANGER = colors.HexColor("#DC2626") # Red
    ACCENT_SUCCESS = colors.HexColor("#16A34A") # Green

    # Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        textColor=PRIMARY,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=SECONDARY,
        spaceAfter=15
    )

    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=TEXT_MUTED,
        spaceAfter=18
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_DARK,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        "Code_Custom",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#0F172A")
    )

    callout_style = ParagraphStyle(
        "Callout_Text",
        parent=body_style,
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor("#1E293B")
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=TEXT_DARK
    )

    story = []

    # ─────────────────────────────────────────────────────────────
    # COVER / HEADER SECTION
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("EduGuardian AI 2.0", title_style))
    story.append(Paragraph("Comprehensive System Architecture, AI Algorithms & Operational Guide", subtitle_style))
    story.append(Paragraph(
        f"<b>Version:</b> 2.0-Production &nbsp;|&nbsp; <b>Institution:</b> NMAM Institute of Technology (Nitte) &nbsp;|&nbsp; <b>Date:</b> {datetime.now().strftime('%B %d, %Y')}",
        meta_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceBefore=0, spaceAfter=12))

    # ─────────────────────────────────────────────────────────────
    # 1. EXECUTIVE SUMMARY & CORE MISSION
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("1. Executive Summary & Core Mission", h1_style))
    story.append(Paragraph(
        "<b>EduGuardian AI 2.0</b> is an enterprise-grade academic resilience and early intervention platform designed for higher education institutions. Traditional educational portals are passive repositories of examination marks and attendance logs. EduGuardian transforms raw institutional records into a <b>proactive, predictive, and multi-agent AI safety net</b> that detects academic vulnerability weeks before formal examinations.",
        body_style
    ))
    story.append(Paragraph(
        "The platform balances two foundational principles: <b>Deep Diagnostic Precision for Faculty</b> and <b>Psychological Safety for Students</b>. While educators gain access to explainable SHAP-grounded risk scores and intervention pipelines, students are protected from demoralizing risk labels, receiving instead personalized study plans, constructive guidance, and AI mentoring.",
        body_style
    ))

    # ─────────────────────────────────────────────────────────────
    # 2. SYSTEM ARCHITECTURE & 9-SERVICE DOCKER STACK
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("2. End-to-End System Architecture", h1_style))
    story.append(Paragraph(
        "EduGuardian is built as an orchestrated multi-service architecture running in fully isolated Docker containers. The stack coordinates authentication, live university portal adapters, asynchronous AI agent graphs, and specialized React dashboards.",
        body_style
    ))

    arch_data = [
        [
            Paragraph("Service", table_header_style),
            Paragraph("Port", table_header_style),
            Paragraph("Technology Stack", table_header_style),
            Paragraph("Core Functionality", table_header_style)
        ],
        [
            Paragraph("<b>db</b>", table_cell_style),
            Paragraph(":5432", table_cell_style),
            Paragraph("PostgreSQL 15 Alpine", table_cell_style),
            Paragraph("Multi-database engine (<code>eduguardian</code> & <code>eduguardian_chatbot</code>)", table_cell_style)
        ],
        [
            Paragraph("<b>edu-backend</b>", table_cell_style),
            Paragraph(":5000", table_cell_style),
            Paragraph("FastAPI, SQLAlchemy, PyJWT", table_cell_style),
            Paragraph("Main REST API, portal scraping adapter, risk calculation engine, faculty quotas", table_cell_style)
        ],
        [
            Paragraph("<b>gateway</b>", table_cell_style),
            Paragraph(":8000", table_cell_style),
            Paragraph("FastAPI, LangGraph, AsyncPG", table_cell_style),
            Paragraph("AI Chatbot orchestrator, multi-turn state graph, three-stage safety guardrails", table_cell_style)
        ],
        [
            Paragraph("<b>agent-insight</b>", table_cell_style),
            Paragraph(":8001", table_cell_style),
            Paragraph("FastAPI, official a2a-sdk", table_cell_style),
            Paragraph("A2A Microservice: Computes subject-level strengths, root weaknesses, and habits", table_cell_style)
        ],
        [
            Paragraph("<b>agent-planner</b>", table_cell_style),
            Paragraph(":8002", table_cell_style),
            Paragraph("FastAPI, official a2a-sdk", table_cell_style),
            Paragraph("A2A Microservice: Generates structured, day-by-day adaptive study schedules", table_cell_style)
        ],
        [
            Paragraph("<b>agent-coach</b>", table_cell_style),
            Paragraph(":8003", table_cell_style),
            Paragraph("FastAPI, official a2a-sdk", table_cell_style),
            Paragraph("A2A Microservice: Empathetic recovery tutor providing Socratic step-by-step guidance", table_cell_style)
        ],
        [
            Paragraph("<b>student-ui</b>", table_cell_style),
            Paragraph(":3001", table_cell_style),
            Paragraph("React, Vite, Nginx", table_cell_style),
            Paragraph("Student Portal: Marks cards, subject attendance, assignments, and guidance", table_cell_style)
        ],
        [
            Paragraph("<b>admin-ui</b>", table_cell_style),
            Paragraph(":3002", table_cell_style),
            Paragraph("React, Vite, Nginx", table_cell_style),
            Paragraph("Teacher & Admin Portal: Live risk roster, mentor assignment, resource dispatch", table_cell_style)
        ],
        [
            Paragraph("<b>chatbot-ui</b>", table_cell_style),
            Paragraph(":3000", table_cell_style),
            Paragraph("React, Vite, Nginx SSE Proxy", table_cell_style),
            Paragraph("AI Chat Interface: Real-time streaming conversational coaching and quiz sessions", table_cell_style)
        ]
    ]

    t_arch = Table(arch_data, colWidths=[1.1 * inch, 0.6 * inch, 1.8 * inch, 3.5 * inch])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────────
    # 3. LIVE UNIVERSITY SOLUTIONS PORTAL ADAPTER
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("3. Real-Time University Portal Data Integration", h1_style))
    story.append(Paragraph(
        "Unlike systems relying on static mock data, EduGuardian incorporates an asynchronous <b>Portal Adapter (<code>portal_adapter.py</code>)</b> that connects directly to the institutional <b>University Solutions Portal</b> over HTTPS.",
        body_style
    ))
    story.append(Paragraph("<b>Authentication & Data Extraction Pipeline:</b>", h2_style))
    story.append(Paragraph("• <b>Secure Handshake:</b> The student provides their mobile number and portal credentials. The backend initiates an HTTPS session, obtains session cookies, and handles portal redirects.", bullet_style))
    story.append(Paragraph("• <b>Deep HTML Scraper & Parser:</b> Extracts student enrollment (USN, Degree, Department, Semester, Section), verified subject registrations, continuous internal evaluation (IA) scores, real-time subject-wise attendance logs, and completed semester marks cards (Semesters 1 through 6).", bullet_style))
    story.append(Paragraph("• <b>Summer / Supplementary Examination Resolver:</b> Discovers historical supplementary exam sessions (e.g. <code>JUNE2024 (Summer)</code>), maps cleared subject codes back to their root semester, updates the effective SGPA, and tracks cleared failure counts.", bullet_style))
    story.append(Paragraph("• <b>Server-Side Caching & Zero-Password Persistence:</b> Extracted StudentContext is cached in PostgreSQL (<code>portal_student_contexts</code>) with 1-hour TTL. Passwords are never saved, logged, or exposed.", bullet_style))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────
    # 4. PREDICTIVE ACADEMIC RISK ENGINE
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("4. Predictive Academic Risk Engine (Multivariate Formulation)", h1_style))
    story.append(Paragraph(
        "The risk engine (<code>academic_risk_engine.py</code>) evaluates academic vulnerability using a multi-horizon synthesis that combines long-term historical marksheet resilience with short-term current-semester indicators.",
        body_style
    ))

    # Callout Box for Risk Equation
    formula_text = (
        "<b>Multi-Horizon Risk Synthesis Equation:</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>R_fused = (w_hist &times; S_foundation) + (w_live &times; S_live_velocity)</b><br/>"
        "• When only attendance is available: <b>w_hist = 0.70</b>, <b>w_live = 0.30</b> (prevents high attendance from masking prior failures).<br/>"
        "• When full signals (attendance, quizzes, assignments, LMS) exist: <b>w_hist = 0.45</b>, <b>w_live = 0.55</b>."
    )
    t_box = Table([[Paragraph(formula_text, callout_style)]], colWidths=[7.0 * inch])
    t_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, SECONDARY),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(t_box)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Quantitative Weighting Matrix & Indicators:</b>", h2_style))
    risk_weights_data = [
        [
            Paragraph("Category", table_header_style),
            Paragraph("Signal / Metric", table_header_style),
            Paragraph("Weight / Trigger", table_header_style),
            Paragraph("Risk Impact & Rule Description", table_header_style)
        ],
        [
            Paragraph("<b>Historical Foundation</b>", table_cell_style),
            Paragraph("Cumulative CGPA", table_cell_style),
            Paragraph("Baseline (0-100)", table_cell_style),
            Paragraph("&ge;8.5: 8 pts | 7.5-8.49: 16 pts | 6.5-7.49: 36 pts | 5.5-6.49: 56 pts | &lt;5.5: 78 pts", table_cell_style)
        ],
        [
            Paragraph("<b>Historical Foundation</b>", table_cell_style),
            Paragraph("SGPA Velocity Dip", table_cell_style),
            Paragraph("+30.0 / +18.0 pts", table_cell_style),
            Paragraph("Latest SGPA &lt;5.0 triggers +30 pts (Critical Dip); &lt;6.0 triggers +18 pts; Declining trend: +18 pts", table_cell_style)
        ],
        [
            Paragraph("<b>Historical Foundation</b>", table_cell_style),
            Paragraph("Active Backlogs", table_cell_style),
            Paragraph("+22.0 pts / arrear", table_cell_style),
            Paragraph("&ge;2 active backlogs escalates student directly to <b>HIGH RISK</b>", table_cell_style)
        ],
        [
            Paragraph("<b>Historical Foundation</b>", table_cell_style),
            Paragraph("Cleared Supplementary Arrears", table_cell_style),
            Paragraph("+8.0 pts / cleared", table_cell_style),
            Paragraph("Prior failures indicate conceptual prerequisites gap; &ge;2 cleared backlogs triggers Medium/High", table_cell_style)
        ],
        [
            Paragraph("<b>Historical Foundation</b>", table_cell_style),
            Paragraph("Borderline Grade Density", table_cell_style),
            Paragraph("+10.0 pts", table_cell_style),
            Paragraph("&ge;4 subject grades with D, E, P, or GP &le; 5.0 indicates marginal comprehension across semesters", table_cell_style)
        ],
        [
            Paragraph("<b>Live Semester Signals</b>", table_cell_style),
            Paragraph("Real-Time Attendance %", table_cell_style),
            Paragraph("40% live weight", table_cell_style),
            Paragraph("&lt;65%: 94 pts (Critical Shortage); 65-74%: 76 pts (Sub-75% Cutoff); 75-84%: 40 pts; &ge;85%: 10 pts", table_cell_style)
        ],
        [
            Paragraph("<b>Live Semester Signals</b>", table_cell_style),
            Paragraph("Internal Quiz Average", table_cell_style),
            Paragraph("30% live weight", table_cell_style),
            Paragraph("&lt;45%: 88 pts (Sub-passing internal score); 45-64%: 50 pts; &ge;65%: 10 pts", table_cell_style)
        ],
        [
            Paragraph("<b>Live Semester Signals</b>", table_cell_style),
            Paragraph("Missed Assignments", table_cell_style),
            Paragraph("15% live weight", table_cell_style),
            Paragraph("&ge;2 missed: 85 pts; 1 missed: 45 pts; 0 missed: 10 pts", table_cell_style)
        ],
        [
            Paragraph("<b>Live Semester Signals</b>", table_cell_style),
            Paragraph("LMS Digital Activity", table_cell_style),
            Paragraph("15% live weight", table_cell_style),
            Paragraph("&lt;40% portal activity: 75 pts; 40-69%: 40 pts; &ge;70%: 10 pts", table_cell_style)
        ]
    ]

    t_risk = Table(risk_weights_data, colWidths=[1.3 * inch, 1.4 * inch, 1.1 * inch, 3.2 * inch])
    t_risk.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_risk)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Three-Tier Risk Classification & Calibrated Recovery Probability:</b>", h2_style))
    story.append(Paragraph("• <b>HIGH RISK (R_fused &ge; 50.0 OR Latest SGPA &lt; 5.0 OR Backlogs &ge; 2 OR Att &lt; 65%):</b> Immediate faculty mentor assignment and structured intervention mandatory. Recovery probability: <b>30% – 60%</b>.", bullet_style))
    story.append(Paragraph("• <b>MEDIUM RISK (R_fused 26.0–49.9 OR Cleared Arrears &ge; 1 OR CGPA &lt; 6.8 OR Att 65–74%):</b> Targeted study plan and milestone check-in advised. Recovery probability: <b>62% – 80%</b>.", bullet_style))
    story.append(Paragraph("• <b>LOW RISK (R_fused &lt; 26.0, CGPA &ge; 7.0, SGPA &ge; 6.5, Att &ge; 75%):</b> On track for academic distinction. Recovery probability: <b>84% – 96%</b>.", bullet_style))

    # ─────────────────────────────────────────────────────────────
    # 5. ROLE-BASED RISK ISOLATION & PSYCHOLOGICAL PROTECTION
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("5. Role-Based Risk Isolation & Psychological Protection", h1_style))
    story.append(Paragraph(
        "A central design requirement of EduGuardian is the <b>strict segregation of risk metrics between faculty and student views</b>. Educational research demonstrates that displaying negative classifications (such as 'At Risk' or 'Declining Trajectory') creates student anxiety and self-fulfilling negative performance loops.",
        body_style
    ))

    iso_data = [
        [
            Paragraph("Portal / Perspective", table_header_style),
            Paragraph("What is Displayed (Allowed)", table_header_style),
            Paragraph("What is Strictly Masked (Forbidden)", table_header_style)
        ],
        [
            Paragraph("<b>Teacher & Admin Portal</b><br/>(:3002)", table_cell_style),
            Paragraph("• Full 3-Tier Risk Badges (High, Medium, Low)<br/>• Exact Risk Score (e.g. 68.8 / 100) & Confidence<br/>• SHAP Feature Attribution & Root Factors<br/>• Attendance Shortage Warnings (&lt;75% / &lt;65%)<br/>• Mentor Assignment & Resource Upload Controls", table_cell_style),
            Paragraph("<i>None. Faculty requires complete, transparent diagnostic data to make timely pedagogical interventions.</i>", table_cell_style)
        ],
        [
            Paragraph("<b>Student Portal</b><br/>(:3001)", table_cell_style),
            Paragraph("• Cumulative CGPA and Semester SGPAs<br/>• Verified Subject-wise Attendance Logs<br/>• Active Enrolled Term (e.g. Semester 5 ISE)<br/>• Total Credits Earned (e.g. 96 Credits)<br/>• Constructive Guidance & Mentoring Actions", table_cell_style),
            Paragraph("• <b>NO</b> Risk Scores or Risk Levels<br/>• <b>NO</b> 'Declining' Trajectory labels in red<br/>• <b>NO</b> SHAP mathematical breakdown<br/>• <b>NO</b> Demoralizing or punitive banners", table_cell_style)
        ]
    ]

    t_iso = Table(iso_data, colWidths=[1.8 * inch, 2.6 * inch, 2.6 * inch])
    t_iso.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_iso)
    story.append(Spacer(1, 10))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────
    # 6. MULTI-AGENT CHATBOT & A2A MICROSERVICES ARCHITECTURE
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("6. Multi-Agent Chatbot & A2A Microservices Architecture", h1_style))
    story.append(Paragraph(
        "EduGuardian's conversational intelligence is orchestrated by a <b>LangGraph StateGraph</b> in the FastAPI Gateway, delegating domain-specific tasks to specialized microservices over Google's official <b>Agent-to-Agent (A2A) SDK</b>.",
        body_style
    ))

    story.append(Paragraph("<b>The Three Autonomous A2A Agents:</b>", h2_style))
    story.append(Paragraph("1. <b>Student Insight Agent (<code>agent-insight:8001</code>):</b> Computes historical marksheet mastery, analyzes subject-level low grade patterns, and identifies root academic struggle areas.", bullet_style))
    story.append(Paragraph("2. <b>Adaptive Study Planner Agent (<code>agent-planner:8002</code>):</b> Synthesizes exam schedules and syllabus priorities to construct a milestone-driven, multi-week study timetable with realistic daily time budgets.", bullet_style))
    story.append(Paragraph("3. <b>Recovery Coach Agent (<code>agent-coach:8003</code>):</b> Acts as an empathetic Socratic tutor. It breaks down complex technical questions (e.g. Dijkstra algorithm, OS paging, ML cost functions) into bite-sized questions and evaluates student comprehension.", bullet_style))

    # ─────────────────────────────────────────────────────────────
    # 7. THREE-STAGE AI SAFETY & QUALITY GUARDRAILS
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("7. Three-Stage AI Safety & Grounding Guardrails", h1_style))
    story.append(Paragraph(
        "To ensure safe and reliable pedagogical interactions, every student query flows through a deterministic three-stage guardrail pipeline before and after LLM execution.",
        body_style
    ))

    guard_data = [
        [
            Paragraph("Guardrail Stage", table_header_style),
            Paragraph("Execution Point", table_header_style),
            Paragraph("Mechanism & Protections Applied", table_header_style)
        ],
        [
            Paragraph("<b>Stage 1: Input Guardrail</b>", table_cell_style),
            Paragraph("Pre-Orchestration<br/>(Immediate On Request)", table_cell_style),
            Paragraph("• <b>Jailbreak Defense:</b> Detects prompt injection, system prompt leakage, and role-override attempts.<br/>• <b>Off-Topic Deflection:</b> Refuses non-educational inquiries (entertainment, coding exploits).<br/>• <b>Mental Health Support:</b> Flags severe emotional distress and directs student to institutional counseling resources.", table_cell_style)
        ],
        [
            Paragraph("<b>Stage 2: Orchestration Guardrail</b>", table_cell_style),
            Paragraph("LangGraph Execution<br/>(During Agent Dispatch)", table_cell_style),
            Paragraph("• <b>Authoritative Context Injection:</b> Injects verified student marks and subjects from PostgreSQL.<br/>• <b>Tool Scope Verification:</b> Constrains A2A agent invocation to registered microservices.<br/>• <b>Multi-Turn Memory:</b> Preserves user facts across sessions without cross-tenant context leaks.", table_cell_style)
        ],
        [
            Paragraph("<b>Stage 3: Output Guardrail</b>", table_cell_style),
            Paragraph("Post-Generation<br/>(Prior to Client Streaming)", table_cell_style),
            Paragraph("• <b>Factual Grounding:</b> Validates that cited course codes, marks, and attendance match DB records.<br/>• <b>Tone & Empathy Verification:</b> Rejects punitive language; enforces constructive Socratic guidance.<br/>• <b>Zero Risk Exposure:</b> Strips any accidental leaks of internal risk scores or danger labels.", table_cell_style)
        ]
    ]

    t_guard = Table(guard_data, colWidths=[1.8 * inch, 1.7 * inch, 3.5 * inch])
    t_guard.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_guard)
    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────────
    # 8. DATABASE SCHEMA & DATA INTEGRITY
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("8. Database Schema & Data Integrity", h1_style))
    story.append(Paragraph(
        "EduGuardian maintains two isolated PostgreSQL databases: <code>eduguardian</code> (Academic ERP & Roster) and <code>eduguardian_chatbot</code> (Conversational State & Memory).",
        body_style
    ))
    story.append(Paragraph("<b>Primary Relational Entities:</b>", h2_style))
    story.append(Paragraph("• <code>users</code> & <code>teachers</code>: Faculty directory, departments, designations, and mentor capacities.", bullet_style))
    story.append(Paragraph("• <code>students</code>: Student records, USN, department, semester, section, and data source tracking.", bullet_style))
    story.append(Paragraph("• <code>mentor_assignments</code>: Tracks active faculty-student mentorship pairings with mentor capacity enforcement.", bullet_style))
    story.append(Paragraph("• <code>assignments</code> & <code>assignment_submissions</code>: Coursework deadlines, max marks, and student submission status.", bullet_style))
    story.append(Paragraph("• <code>attendance_records</code> & <code>quiz_results</code>: Subject-wise attendance % and continuous internal evaluation scores.", bullet_style))
    story.append(Paragraph("• <code>risk_predictions</code>: Historical audit log of calculated risk levels, recovery probabilities, and attribution factors.", bullet_style))
    story.append(Paragraph("• <code>student_resources</code>: Targeted PDFs and learning guides dispatched by teachers directly to students.", bullet_style))
    story.append(Paragraph("• <code>conversations</code> & <code>messages</code> (Chatbot DB): Multi-turn dialog histories with structured data and agent usage logs.", bullet_style))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────
    # 9. FACULTY WORKFLOWS & MENTORING PIPELINE
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("9. Key Faculty Workflows & Mentoring Pipeline", h1_style))
    story.append(Paragraph(
        "The Teacher & Admin Portal provides educators with an actionable command center to identify struggling students, manage mentoring workloads, and dispatch targeted resources.",
        body_style
    ))
    story.append(Paragraph("• <b>Hybrid Live Roster & Multi-Tier Filtering:</b> Faculty can filter students across <code>High Risk</code>, <code>Medium Risk</code>, and <code>Low Risk</code> tabs with live search by USN, name, or semester.", bullet_style))
    story.append(Paragraph("• <b>Deep Student Risk Dossier:</b> Clicking any student opens their complete academic dossier—showing their 6-semester SGPA curve, attendance history, cleared supplementary backlogs, and SHAP risk factor breakdown.", bullet_style))
    story.append(Paragraph("• <b>Strict Mentor Capacity Enforcement:</b> Teachers have designated student capacities (e.g. 10 or 15 mentees). The system prevents overloading faculty members by dynamically tracking active mentee counts.", bullet_style))
    story.append(Paragraph("• <b>Targeted Resource Dispatch:</b> Teachers can upload study materials and assign them either to the entire class or targeted specifically at High-Risk students.", bullet_style))

    # ─────────────────────────────────────────────────────────────
    # 10. DEPLOYMENT & VERIFICATION GUIDE
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("10. Production Deployment & Verification", h1_style))
    story.append(Paragraph(
        "EduGuardian 2.0 is packaged for instant zero-configuration deployment on any laptop or server running Docker Desktop.",
        body_style
    ))

    # Docker Run Box
    docker_cmd_text = (
        "<b>Single-Command Full Stack Startup:</b><br/>"
        "<code>git clone https://github.com/nnm24is127-droid/eduguardian.git</code><br/>"
        "<code>cd eduguardian</code><br/>"
        "<code>docker compose up --build</code>"
    )
    t_docker = Table([[Paragraph(docker_cmd_text, callout_style)]], colWidths=[7.0 * inch])
    t_docker.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, PRIMARY),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(t_docker)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Default Evaluation Accounts:</b>", h2_style))
    creds_data = [
        [
            Paragraph("Role", table_header_style),
            Paragraph("Portal URL", table_header_style),
            Paragraph("Login Email / Mobile", table_header_style),
            Paragraph("Default Password", table_header_style)
        ],
        [
            Paragraph("<b>Class Advisor / Teacher</b>", table_cell_style),
            Paragraph("http://localhost:3002", table_cell_style),
            Paragraph("<code>preethi.salian@nitte.edu.in</code>", table_cell_style),
            Paragraph("<code>123456</code>", table_cell_style)
        ],
        [
            Paragraph("<b>Subject Faculty (DCN)</b>", table_cell_style),
            Paragraph("http://localhost:3002", table_cell_style),
            Paragraph("<code>ravi.b@nitte.edu.in</code>", table_cell_style),
            Paragraph("<code>123456</code>", table_cell_style)
        ],
        [
            Paragraph("<b>Student (Portal Auth)</b>", table_cell_style),
            Paragraph("http://localhost:3001", table_cell_style),
            Paragraph("<code>nnm24is127@eduguardian.ai</code>", table_cell_style),
            Paragraph("<code>123456</code>", table_cell_style)
        ],
        [
            Paragraph("<b>AI Chatbot Standalone</b>", table_cell_style),
            Paragraph("http://localhost:3000", table_cell_style),
            Paragraph("<i>Auto-connects via Gateway</i>", table_cell_style),
            Paragraph("<i>Shared JWT Auth</i>", table_cell_style)
        ]
    ]

    t_creds = Table(creds_data, colWidths=[1.8 * inch, 1.6 * inch, 2.2 * inch, 1.4 * inch])
    t_creds.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_creds)
    story.append(Spacer(1, 14))

    story.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR, spaceBefore=4, spaceAfter=8))
    story.append(Paragraph(
        "<b>Conclusion:</b> EduGuardian AI 2.0 provides an end-to-end, ethically grounded, and algorithmically robust platform that turns institutional examination data into early warning safeguards and actionable student recovery pathways.",
        ParagraphStyle("Conclusion", parent=body_style, fontName="Helvetica-Oblique", fontSize=9, textColor=TEXT_MUTED)
    ))

    # Build PDF with two-pass canvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {filename}")


if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "c:\\hackthon_2\\eduguardian\\EduGuardian_AI_Architecture_and_Concept_Guide.pdf"
    build_pdf(out_file)
