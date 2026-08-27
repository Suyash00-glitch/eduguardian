import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

pdf_path = r"c:\hackthon_2\eduguardian\EduGuardian_Student_Risk_Calculation_Framework.pdf"
doc = SimpleDocTemplate(
    pdf_path,
    pagesize=letter,
    rightMargin=36, leftMargin=36,
    topMargin=36, bottomMargin=36
)

styles = getSampleStyleSheet()

primary_color = colors.HexColor("#0F172A")   # Slate 900
accent_teal = colors.HexColor("#0D9488")     # Teal 600
accent_indigo = colors.HexColor("#4F46E5")   # Indigo 600
bg_light = colors.HexColor("#F8FAFC")        # Slate 50

title_style = ParagraphStyle(
    "DocTitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=20,
    leading=24,
    textColor=primary_color,
    alignment=TA_LEFT
)

subtitle_style = ParagraphStyle(
    "DocSubtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=10.5,
    leading=14,
    textColor=colors.HexColor("#64748B"),
    alignment=TA_LEFT
)

h1_style = ParagraphStyle(
    "H1",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=16,
    textColor=primary_color,
    spaceBefore=12,
    spaceAfter=5
)

body_style = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=13,
    textColor=colors.HexColor("#334155"),
    alignment=TA_LEFT
)

table_header_style = ParagraphStyle(
    "TH",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8.5,
    leading=11,
    textColor=colors.white,
    alignment=TA_CENTER
)

table_cell_style = ParagraphStyle(
    "TC",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=11,
    textColor=colors.HexColor("#1E293B"),
    alignment=TA_LEFT
)

table_cell_center = ParagraphStyle(
    "TCC",
    parent=table_cell_style,
    alignment=TA_CENTER
)

code_style = ParagraphStyle(
    "CodeStyle",
    parent=styles["Normal"],
    fontName="Courier",
    fontSize=7.5,
    leading=10,
    textColor=colors.HexColor("#0F172A"),
    backColor=colors.HexColor("#F1F5F9"),
    borderPadding=5
)

story = []

# Header
story.append(Paragraph("EduGuardian AI — Academic Risk Intelligence", title_style))
story.append(Spacer(1, 2))
story.append(Paragraph("Student Academic Risk Calculation Framework & Multi-Agent Early Detection Architecture", subtitle_style))
story.append(Spacer(1, 6))
story.append(HRFlowable(width="100%", thickness=2, color=accent_teal, spaceBefore=2, spaceAfter=8))

# 1. Executive Summary
story.append(Paragraph("1. Executive Overview", h1_style))
story.append(Paragraph(
    "The EduGuardian Risk Intelligence Engine continuously analyzes real-time behavioral signals across "
    "four core academic dimensions to proactively detect student academic distress before failure occurs. "
    "Students are categorized into <b>High Risk</b>, <b>Medium Risk</b>, and <b>Low Risk</b> tiers, "
    "providing live visibility for class admins while automatically steering adaptive AI coaching.",
    body_style
))
story.append(Spacer(1, 8))

# 2. Four Core Signal Dimensions
story.append(Paragraph("2. Four Core Signal Dimensions & Formulas", h1_style))
signals_data = [
    [
        Paragraph("Signal Dimension", table_header_style),
        Paragraph("Data Source", table_header_style),
        Paragraph("Calculation Formula", table_header_style),
        Paragraph("Critical Threshold", table_header_style),
        Paragraph("Weight", table_header_style)
    ],
    [
        Paragraph("<b>1. Attendance Rate</b>", table_cell_style),
        Paragraph("attendance_records", table_cell_style),
        Paragraph("(Classes Attended / Classes Held) * 100", table_cell_style),
        Paragraph("&lt; 65.0%", table_cell_center),
        Paragraph("35%", table_cell_center)
    ],
    [
        Paragraph("<b>2. Quiz / Exam Score</b>", table_cell_style),
        Paragraph("quiz_results", table_cell_style),
        Paragraph("(Total Marks / Max Marks) * 100", table_cell_style),
        Paragraph("&lt; 50.0%", table_cell_center),
        Paragraph("30%", table_cell_center)
    ],
    [
        Paragraph("<b>3. Assignment Health</b>", table_cell_style),
        Paragraph("assignment_submissions", table_cell_style),
        Paragraph("Count of Overdue / Missed Submissions", table_cell_style),
        Paragraph("&gt;= 2 Missed", table_cell_center),
        Paragraph("20%", table_cell_center)
    ],
    [
        Paragraph("<b>4. LMS Engagement</b>", table_cell_style),
        Paragraph("lms_activity", table_cell_style),
        Paragraph("Session frequency & total active study minutes", table_cell_style),
        Paragraph("Inactivity &gt; 10 days", table_cell_center),
        Paragraph("15%", table_cell_center)
    ]
]

t_signals = Table(signals_data, colWidths=[1.4*inch, 1.4*inch, 2.3*inch, 1.1*inch, 0.8*inch])
t_signals.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), primary_color),
    ("ALIGN", (0,0), (-1,-1), "LEFT"),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, bg_light]),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
]))
story.append(t_signals)
story.append(Spacer(1, 8))

# 3. Risk Classification Rules Table
story.append(Paragraph("3. Risk Classification Rules & Thresholds", h1_style))
risk_matrix_data = [
    [
        Paragraph("Risk Tier", table_header_style),
        Paragraph("Trigger Criteria & Academic Indicators", table_header_style),
        Paragraph("Recovery Probability", table_header_style),
        Paragraph("System Action & Interventions", table_header_style)
    ],
    [
        Paragraph("<font color=\"#DC2626\"><b>HIGH RISK</b></font>", table_cell_style),
        Paragraph("- Attendance &lt; 65% OR drop &gt; 15%<br/>- Quiz average &lt; 50%<br/>- Missed assignments &gt;= 2", table_cell_style),
        Paragraph("<b>&lt; 50%</b><br/>(e.g., 38%-48%)", table_cell_center),
        Paragraph("- Flagged on Class Admin Dashboard<br/>- Priority Mentor Assignment<br/>- Recovery Coach intervention triggered", table_cell_style)
    ],
    [
        Paragraph("<font color=\"#D97706\"><b>MEDIUM RISK</b></font>", table_cell_style),
        Paragraph("- Attendance 65% - 79%<br/>- Quiz average 50% - 74%<br/>- Missed assignments = 1", table_cell_style),
        Paragraph("<b>50% - 80%</b><br/>(e.g., 65%-78%)", table_cell_center),
        Paragraph("- Academic Watchlist monitoring<br/>- Study Planner catch-up roadmap<br/>- Automated remedial quiz suggestions", table_cell_style)
    ],
    [
        Paragraph("<font color=\"#16A34A\"><b>LOW RISK</b></font>", table_cell_style),
        Paragraph("- Attendance &gt;= 80%<br/>- Quiz average &gt;= 75%<br/>- Missed assignments = 0", table_cell_style),
        Paragraph("<b>&gt; 80%</b><br/>(e.g., 85%-98%)", table_cell_center),
        Paragraph("- Positive habit reinforcement<br/>- Advanced concept challenges<br/>- Standard progress tracking", table_cell_style)
    ]
]

t_risk = Table(risk_matrix_data, colWidths=[1.2*inch, 2.5*inch, 1.4*inch, 2.0*inch])
t_risk.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), primary_color),
    ("ALIGN", (0,0), (-1,-1), "LEFT"),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#FEF2F2"), colors.HexColor("#FFFBEB"), colors.HexColor("#F0FDF4")]),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
]))
story.append(t_risk)
story.append(Spacer(1, 8))

# 4. Database Schema
story.append(Paragraph("4. Explainable Persistence Schema (PostgreSQL)", h1_style))
story.append(Paragraph(
    "All risk computations are persisted in the <b>risk_predictions</b> table with human-readable support signals and SHAP feature importance:",
    body_style
))
story.append(Spacer(1, 3))
sql_snippet = """CREATE TABLE risk_predictions (
    student_id          INT REFERENCES students(id) ON DELETE CASCADE,
    risk_level          VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high')),
    recovery_probability DECIMAL(5,2),   -- e.g. 42.50%
    support_signal      TEXT,            -- Human-readable explainable trigger
    attendance_change   DECIMAL(6,2),    -- Delta percentage trend (e.g. -18.00%)
    lms_activity_change DECIMAL(6,2),    -- Delta LMS usage frequency
    missed_assignments  INT DEFAULT 0,   -- Count of overdue tasks
    shap_explanation    JSONB            -- Feature weight vector explaining decision
);"""
story.append(Paragraph(sql_snippet.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))
story.append(Spacer(1, 8))

# 5. Multi-Agent AI Coaching Workflow
story.append(Paragraph("5. AI Multi-Agent Coaching Integration", h1_style))
story.append(Paragraph(
    "• <b>Recovery Coach Agent (:8003)</b>: Reads student risk metrics and crafts non-stigmatizing, "
    "encouraging check-in messages tailored to rebuild confidence.<br/>"
    "• <b>Study Planner Agent (:8002)</b>: Dynamically recalculates study roadmaps and milestones "
    "when missed assignments or declining quiz trends are detected.<br/>"
    "• <b>Student Insight Agent (:8001)</b>: Adjusts teaching depth and generates scaffolded practice "
    "questions for topics where student scored below 50%.",
    body_style
))
story.append(Spacer(1, 8))

story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceBefore=4, spaceAfter=6))
story.append(Paragraph(
    "Generated by <b>EduGuardian AI Platform</b> · Confidential Academic Intelligence Report · 2026",
    ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7.5, textColor=colors.HexColor("#94A3B8"), alignment=TA_CENTER)
))

doc.build(story)
print("SUCCESS: PDF created at " + pdf_path)
