import sys
sys.path.insert(0, "edu-backend")
from utils.portal_adapter import normalize_student_context

# 1. Profile Mock
profile_resp = {
    "status": "success",
    "fname": "MOHAMMED AJMAL",
    "strRegno": "NNM24IS127",
    "strMobile": "9110241337",
    "strEmail": "nnm24is127@nmamit.in",
    "college": "1001 - NMAM Institute of Technology, Nitte",
    "fdegree": "BTIS24",
    "degree": "B.Tech (Information Science & Engineering)",
    "fcollcode": "1001",
    "funivcode": "049"
}

# 2. Detailed History Mock (simulating getResults for each semester)
historical_mock = [
    {
        "examname": "B.Tech (Information Science & Engineering)<br>Fourth Semester",
        "examdate": "MAY 2026",
        "resultdate": "20/06/2026",
        "class": "Pass",
        "year": "202605",
        "regno": "NNM24IS127",
        "fsgpa": 8.42,
        "fcgpa": 8.15,
        "fresult": "Pass",
        "subject_results": [
            {
                "fsubcode": "22IS41",
                "subject": "Database Management Systems",
                "ia_exam": 45,
                "uni_exam": 48,
                "thtot": 93,
                "FMAXMARKS": 100,
                "FGRADE": "O",
                "FGP": 10,
                "FCREDITS": 4,
                "result": "PASS"
            },
            {
                "fsubcode": "22IS42",
                "subject": "Design and Analysis of Algorithms",
                "ia_exam": 42,
                "uni_exam": 44,
                "thtot": 86,
                "FMAXMARKS": 100,
                "FGRADE": "A+",
                "FGP": 9,
                "FCREDITS": 4,
                "result": "PASS"
            }
        ]
    },
    {
        "examname": "B.Tech (Information Science & Engineering)<br>Third Semester",
        "examdate": "DECEMBER 2025",
        "resultdate": "29/01/2026",
        "class": "Pass",
        "year": "202512",
        "regno": "NNM24IS127",
        "fsgpa": 8.10,
        "fcgpa": 8.05,
        "fresult": "Pass",
        "subject_results": [
            {
                "fsubcode": "22IS31",
                "subject": "Data Structures and Applications",
                "ia_exam": 44,
                "uni_exam": 46,
                "thtot": 90,
                "FMAXMARKS": 100,
                "FGRADE": "O",
                "FGP": 10,
                "FCREDITS": 4,
                "result": "PASS"
            }
        ]
    },
    {
        "examname": "B.Tech (Information Science & Engineering)<br>Second Semester",
        "examdate": "MAY 2025",
        "resultdate": "25/06/2025",
        "class": "Pass",
        "year": "202505",
        "regno": "NNM24IS127",
        "fsgpa": 8.00,
        "fcgpa": 8.02,
        "fresult": "Pass",
        "subject_results": []
    },
    {
        "examname": "B.Tech (Information Science & Engineering)<br>First Semester",
        "examdate": "DECEMBER 2024",
        "resultdate": "23/01/2025",
        "class": "Pass",
        "year": "202412",
        "regno": "NNM24IS127",
        "fsgpa": 8.05,
        "fcgpa": 8.05,
        "fresult": "Pass",
        "subject_results": []
    }
]

ctx = normalize_student_context("9110241337", profile_resp, [], None, None, historical_mock)

print("=== IDENTITY ===")
print("  Name:", ctx["identity"]["name"])
print("  USN:", ctx["identity"]["usn"])
print("  Email:", ctx["identity"]["email"])
print("  Current Semester:", ctx["identity"]["semester"])
print("  Section:", ctx["identity"]["section"])

print("\n=== HISTORICAL SEMESTERS ===")
for sem in ctx["historical_semesters"]:
    print(f"  Sem {sem['semester']} ({sem['exam_name']}):")
    print(f"    SGPA: {sem['sgpa']}, CGPA: {sem['cgpa']}, Result: {sem['result']}, Date: {sem['result_date']}")
    print(f"    Subjects ({len(sem['subject_results'])}):")
    for s in sem["subject_results"]:
        print(f"      - {s['subject_code']}: {s['subject_name']} | IA: {s['internal_marks']}, Ext: {s['external_marks']}, Tot: {s['marks_obtained']}/{s['max_marks']}, Gr: {s['grade']}, GP: {s['grade_point']}, Cr: {s['credits']}, Res: {s['result']}")

print("\n=== ACADEMIC PERFORMANCE SUMMARY ===")
print("  Latest SGPA:", ctx["historical_academic_performance"]["latest_sgpa"])
print("  CGPA:", ctx["historical_academic_performance"]["cgpa"])
print("  SGPA Trend:", ctx["historical_academic_performance"]["sgpa_trend"])
print("  Total Credits:", ctx["historical_academic_performance"]["total_credits_earned"])
print("  Total Semesters:", ctx["historical_academic_performance"]["total_semesters_completed"])

