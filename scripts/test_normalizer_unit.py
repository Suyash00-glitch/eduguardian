import sys
sys.path.insert(0, "edu-backend")
from utils.portal_adapter import normalize_student_context

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

historical_mock = [
    {
        "fexamno": "A",
        "fexamname": "B.Tech (Information Science & Engineering) - Fourth Semester",
        "fresdate": "20/06/2026",
        "fresult": "Pass",
        "fsgpa": "8.42",
        "fcgpa": "8.15",
        "subject_results": [
            {"fsubcode": "22IS41", "subject": "Database Management Systems", "ia_exam": 45, "uni_exam": 48, "thtot": 93, "FMAXMARKS": 100, "FGRADE": "O", "FGP": 10, "FCREDITS": 4, "result": "PASS"}
        ]
    },
    {
        "fexamno": "B",
        "fexamname": "B.Tech (Information Science & Engineering) - Third Semester",
        "fresdate": "29/01/2026",
        "fresult": "Pass",
        "fsgpa": "7.85",
        "fcgpa": "8.05",
        "subject_results": []
    }
]

ctx = normalize_student_context("9110241337", profile_resp, [], None, None, historical_mock)
print("IDENTITY:")
for k, v in ctx["identity"].items():
    print(f"  {k}: {repr(v)}")
print("HISTORICAL SEMESTERS:", len(ctx["historical_semesters"]))
for s in ctx["historical_semesters"]:
    print(f"  Sem {s['semester']}: SGPA={s['sgpa']}, CGPA={s['cgpa']}, Subjs={len(s['subject_results'])}")
print("PERFORMANCE:", ctx["historical_academic_performance"])
