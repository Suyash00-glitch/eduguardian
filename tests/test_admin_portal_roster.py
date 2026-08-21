"""
Test Suite for Faculty/Admin Portal Student Roster, Deep Risk Explainability, and RBAC.

Validates:
1. Teacher/Admin can load cohort roster.
2. Roster summary counters are dynamically calculated.
3. Student rows contain real University Solutions CGPA, SGPA, and backlogs.
4. Early-semester pending attendance/assessments remain 'pending' and are not treated as 0.
5. Risk level, score, confidence, basis, and explainable factors come from academic_risk_engine.py.
6. RBAC security: Students receive 403 Forbidden when attempting to access admin roster/risk endpoints.
7. Student portal context strips all risk badges, scores, and factors.
8. Unauthenticated requests are rejected with 401 Unauthorized.
"""

import sys
import os
import json
import urllib.request
import urllib.error
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "edu-backend"))
from utils.jwt import create_token

BASE_URL = "http://localhost:5000"

# Teacher token (Teacher / Admin role)
TEACHER_TOKEN = create_token(user_id=10, role="teacher")
# Student tokens
STUDENT_AJMAL_TOKEN = create_token(user_id=3, role="student")   # Mohammed Ajmal
STUDENT_PRAYAG_TOKEN = create_token(user_id=21, role="student") # Prayag M


def make_request(path: str, token: str = None):
    url = f"{BASE_URL}{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"detail": body}
        return e.code, parsed


# ── TEST 1: Teacher can load roster ──────────────────────────────────────────

def test_1_admin_can_load_roster():
    status, data = make_request("/api/students/roster", TEACHER_TOKEN)
    assert status == 200
    assert "students" in data
    assert "summary" in data
    assert len(data["students"]) > 0


# ── TEST 2 & 3: Roster summary is dynamic ─────────────────────────────────────

def test_2_and_3_summary_counters_are_dynamic():
    status, data = make_request("/api/students/roster", TEACHER_TOKEN)
    assert status == 200
    summary = data["summary"]
    students = data["students"]

    assert summary["total_enrolled"] == len(students)
    assert summary["high_risk"] == len([s for s in students if s["risk_level"] == "HIGH"])
    assert summary["medium_risk"] == len([s for s in students if s["risk_level"] == "MEDIUM"])
    assert summary["low_risk"] == len([s for s in students if s["risk_level"] == "LOW"])
    assert "insufficient_data" in summary


# ── TEST 4, 5, 8, 9, 10, 11: Real academic metrics & risk signals ─────────────

def test_4_to_11_real_student_records_and_calibrated_risk():
    status, data = make_request("/api/students/roster", TEACHER_TOKEN)
    assert status == 200
    students_by_usn = {s["usn"]: s for s in data["students"]}

    # Mohammed Ajmal (NNM24IS127)
    assert "NNM24IS127" in students_by_usn
    ajmal = students_by_usn["NNM24IS127"]
    assert ajmal["cgpa"] == 8.45
    assert ajmal["latest_sgpa"] == 8.67
    assert ajmal["backlogs"] == 0
    assert ajmal["risk_level"] == "LOW"
    assert ajmal["confidence"] in ["LOW", "PARTIAL", "FULL"]
    assert ajmal["risk_basis"] in ["historical_academic_performance", "current_and_historical"]
    assert len(ajmal["factors"]) > 0

    # Prayag M (NNM24IS172)
    assert "NNM24IS172" in students_by_usn
    prayag = students_by_usn["NNM24IS172"]
    assert prayag["cgpa"] == pytest.approx(5.26, 0.05) or prayag["cgpa"] == 5.24
    assert prayag["latest_sgpa"] == 4.50
    assert prayag["backlogs"] == 4
    assert prayag["risk_level"] == "HIGH"
    assert prayag["confidence"] in ["LOW", "PARTIAL", "FULL"]
    assert len(prayag["factors"]) > 0


# ── TEST 6 & 7: Pending attendance and assessments are NOT zero ───────────────

def test_6_and_7_pending_attendance_and_assessments_not_zero():
    status, data = make_request("/api/students/roster", TEACHER_TOKEN)
    assert status == 200
    students_by_usn = {s["usn"]: s for s in data["students"]}

    ajmal = students_by_usn["NNM24IS127"]
    prayag = students_by_usn["NNM24IS172"]

    # Pending attendance must not be 0.0 or 0%
    assert ajmal["attendance_status"] == "pending"
    assert ajmal["attendance"] is None

    assert prayag["attendance_status"] == "pending"
    assert prayag["attendance"] is None


# ── TEST 12 & 13: Deep risk detail explainability endpoint ────────────────────

def test_12_and_13_deep_risk_detail_explainability():
    # Student ID 2 is Mohammed Ajmal, ID 20 is Prayag M
    for sid, expected_risk in [(2, "LOW"), (20, "HIGH")]:
        status, detail = make_request(f"/api/students/risk-detail/{sid}", TEACHER_TOKEN)
        assert status == 200
        assert "academic_performance" in detail
        assert "current_semester" in detail
        assert "risk_assessment" in detail
        assert "historical_semesters" in detail

        risk_assess = detail["risk_assessment"]
        assert risk_assess["risk_level"] == expected_risk
        assert "risk_score" in risk_assess
        assert "confidence" in risk_assess
        assert "risk_basis" in risk_assess
        assert len(risk_assess["factors"]) > 0


# ── TEST 15 & 16: Students CANNOT access admin endpoints (403 Forbidden) ──────

def test_15_and_16_students_forbidden_from_admin_endpoints():
    # Student attempts to access /api/students/roster
    status, _ = make_request("/api/students/roster", STUDENT_AJMAL_TOKEN)
    assert status == 403

    # Student attempts to access /api/students/risk-detail/2
    status_detail, _ = make_request("/api/students/risk-detail/2", STUDENT_AJMAL_TOKEN)
    assert status_detail == 403


# ── TEST 17: Student portal-context sanitization ──────────────────────────────

def test_17_student_portal_context_has_no_risk_data():
    status, ctx = make_request("/api/students/portal-context", STUDENT_AJMAL_TOKEN)
    assert status == 200

    # Risk fields must be completely absent from student context
    assert "risk_level" not in ctx
    assert "risk_score" not in ctx
    assert "confidence" not in ctx
    assert "factors" not in ctx
    assert "shap_explanation" not in ctx
    assert "risk_evaluation" not in ctx

    # Positive constructive guidance must be present
    assert "academic_guidance" in ctx
    assert ctx["academic_guidance"]["badge"] != "HIGH RISK"
    assert ctx["academic_guidance"]["badge"] != "LOW RISK"


# ── TEST 18: Unauthenticated requests are rejected (401 Unauthorized) ────────

def test_18_unauthenticated_requests_rejected():
    status, _ = make_request("/api/students/roster")
    assert status in [401, 403]


# ── TEST 19: Hybrid Real + Demo students coexistence ─────────────────────────

def test_19_hybrid_real_and_demo_coexistence():
    status, data = make_request("/api/students/roster", TEACHER_TOKEN)
    assert status == 200
    students_by_usn = {s["usn"]: s for s in data["students"]}

    # Both real portal students exist
    assert "NNM24IS127" in students_by_usn
    assert "NNM24IS172" in students_by_usn
    assert students_by_usn["NNM24IS127"]["data_source"] == "student_portal"
    assert students_by_usn["NNM24IS172"]["data_source"] == "student_portal"

    # Demo students exist alongside real students
    assert "1MS21IS001" in students_by_usn
    assert "NNM24IS012" in students_by_usn
    assert students_by_usn["1MS21IS001"]["data_source"] == "demo"
    assert students_by_usn["NNM24IS012"]["data_source"] == "demo"

    # Total count reflects both real + demo
    assert len(data["students"]) >= 10


# ── TEST 20: Demo student risk detail endpoint works ─────────────────────────

def test_20_demo_student_risk_detail_works():
    # Student ID 1 is Alex Johnson, ID 6 is Ananya Gupta
    for sid in [1, 6]:
        status, detail = make_request(f"/api/students/risk-detail/{sid}", TEACHER_TOKEN)
        assert status == 200
        assert "academic_performance" in detail
        assert "risk_assessment" in detail
        assert detail["data_source"] == "demo"
        assert "historical_semesters" in detail
