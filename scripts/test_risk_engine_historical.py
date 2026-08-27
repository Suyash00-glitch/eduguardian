import sys
sys.path.insert(0, "edu-backend")
from utils.portal_adapter import normalize_student_context
from utils.academic_risk_engine import calculate_academic_risk

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
            {"fsubcode": "22IS41", "subject": "Database Management Systems", "ia_exam": 45, "uni_exam": 48, "thtot": 93, "FMAXMARKS": 100, "FGRADE": "O", "FGP": 10, "FCREDITS": 4, "result": "PASS"}
        ]
    }
]

ctx = normalize_student_context("9110241337", profile_resp, [], None, None, historical_mock)
risk = calculate_academic_risk(ctx)

print("=== RISK CALCULATION OUTPUT ===")
print("  Risk Level:", risk["risk_level"])
print("  Recovery Probability:", risk["recovery_probability"])
print("  Confidence:", risk["confidence"])
print("  Evaluation Mode:", risk["evaluation_mode"])
print("  Plain Rationale:", risk["plain_rationale"])
print("  Signals Evaluated:", risk["signals_evaluated"])
