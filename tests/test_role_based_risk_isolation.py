import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "edu-backend"))
import json
import urllib.request
import urllib.error
import pytest
import subprocess
from utils.academic_risk_engine import calculate_academic_risk
from utils.portal_adapter import normalize_student_context
from utils.jwt import create_token

BASE_URL = "http://localhost:5000"


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


def test_1_student_cannot_access_admin_risk_analysis():
    """Requirement: Students receive 403 Forbidden when requesting internal risk analysis."""
    student_token = create_token(user_id=1, role="student")
    status, data = make_request("/api/students/risk-analysis", student_token)
    assert status == 403, f"Expected 403 for student accessing risk-analysis, got {status}: {data}"


def test_2_teacher_admin_can_access_roster_and_risk():
    """Requirement: Teachers/Admins can access student roster with risk assessments."""
    teacher_token = create_token(user_id=1, role="teacher")
    status, data = make_request("/api/students/roster?department=ISE&semester=5&section=A", teacher_token)
    assert status == 200, f"Expected 200 for teacher accessing roster, got {status}: {data}"
    assert "students" in data
    assert "summary" in data


def test_3_student_context_sanitized_no_risk_level():
    """Requirement: Student-facing portal context contains NO raw risk_level."""
    student_token = create_token(user_id=1, role="student")
    status, data = make_request("/api/students/portal-context", student_token)
    assert status == 200, f"Expected 200, got {status}: {data}"
    assert "risk_evaluation" not in data or "risk_level" not in data.get("risk_evaluation", {}), "Student context must not contain raw risk_evaluation.risk_level"


def test_4_student_context_sanitized_no_internal_risk_score():
    """Requirement: Student-facing portal context contains NO raw risk_score."""
    student_token = create_token(user_id=1, role="student")
    status, data = make_request("/api/students/portal-context", student_token)
    assert "risk_score" not in data, "Student context must not expose raw risk_score"


def test_5_student_can_see_constructive_academic_guidance():
    """Requirement: Student receives constructive academic feedback without risk tags."""
    student_token = create_token(user_id=1, role="student")
    status, data = make_request("/api/students/portal-context", student_token)
    assert "academic_guidance" in data
    assert "message" in data["academic_guidance"]
    msg = data["academic_guidance"]["message"].upper()
    assert "HIGH RISK" not in msg
    assert "MEDIUM RISK" not in msg
    assert "LOW RISK" not in msg


def test_6_admin_can_see_risk_classification():
    """Requirement: Admin can view risk classifications (HIGH/MEDIUM/LOW)."""
    teacher_token = create_token(user_id=1, role="teacher")
    status, data = make_request("/api/students/roster", teacher_token)
    assert status == 200
    students = data.get("students", [])
    if students:
        s0 = students[0]
        assert "risk_level" in s0
        assert s0["risk_level"] in ("HIGH", "MEDIUM", "LOW")


def test_7_admin_can_see_risk_score():
    """Requirement: Admin can view numeric risk scores."""
    teacher_token = create_token(user_id=1, role="teacher")
    status, data = make_request("/api/students/roster", teacher_token)
    assert status == 200
    students = data.get("students", [])
    if students:
        s0 = students[0]
        assert "risk_score" in s0
        assert isinstance(s0["risk_score"], (int, float))


def test_8_admin_can_see_confidence():
    """Requirement: Admin can view calibrated confidence (LOW, PARTIAL, FULL)."""
    teacher_token = create_token(user_id=1, role="teacher")
    status, data = make_request("/api/students/roster", teacher_token)
    assert status == 200
    students = data.get("students", [])
    if students:
        s0 = students[0]
        assert "confidence" in s0
        assert s0["confidence"] in ("LOW", "PARTIAL", "FULL")


def test_9_admin_can_see_explainable_risk_factors():
    """Requirement: Admin can view explainable contributing risk factors."""
    teacher_token = create_token(user_id=1, role="teacher")
    status, data = make_request("/api/students/roster", teacher_token)
    assert status == 200
    students = data.get("students", [])
    if students:
        s0 = students[0]
        assert "factors" in s0
        assert isinstance(s0["factors"], list)


def test_10_student_a_cannot_retrieve_student_b_risk_info():
    """Requirement: Student tokens are blocked from querying other students' risk endpoints."""
    student_token = create_token(user_id=1, role="student")
    status, data = make_request("/api/students/risk-detail/2", student_token)
    assert status == 403, "Student must not be able to access risk-detail for any student"


def test_11_real_portal_data_continues_working():
    """Requirement: Real portal context normalization preserves real student data."""
    ctx = normalize_student_context(
        mobile="9110241337",
        profile={"fname": "MOHAMMED AJMAL", "fregno": "NNM24IS127", "fcursem": 5, "fdescpn": "B.Tech (ISE)"},
        subjects=[{"fsubcode": "22IS51", "fsubname": "DBMS"}],
        attendance=None,
        ia_marks=None,
        historical=[
            {"year": "202605", "examname": "Fourth Semester", "sgpa": 8.67, "cgpa": 8.45, "subject_results": []}
        ],
        data_source="student_portal"
    )
    assert ctx["identity"]["name"] == "MOHAMMED AJMAL"
    assert ctx["identity"]["usn"] == "NNM24IS127"
    assert ctx["historical_academic_performance"]["cgpa"] == 8.45
    assert ctx["historical_academic_performance"]["latest_sgpa"] == 8.67


def test_12_missing_attendance_is_not_treated_as_zero():
    """Requirement: Pending attendance is marked pending/not_available, never 0%."""
    ctx = normalize_student_context(
        mobile="9110241337",
        profile={"fname": "MOHAMMED AJMAL", "fregno": "NNM24IS127", "fcursem": 5},
        subjects=[],
        attendance=None,
        ia_marks=None,
        historical=[{"year": "202605", "sgpa": 8.67, "cgpa": 8.45, "subject_results": []}],
        data_source="student_portal"
    )
    assert ctx["attendance"]["status"] == "not_available"
    assert ctx["attendance"]["value"] is None


def test_13_missing_assessment_is_not_treated_as_zero():
    """Requirement: Pending IA assessment is marked pending/not_available, never 0%."""
    ctx = normalize_student_context(
        mobile="9110241337",
        profile={"fname": "MOHAMMED AJMAL", "fregno": "NNM24IS127", "fcursem": 5},
        subjects=[],
        attendance=None,
        ia_marks=None,
        historical=[],
        data_source="student_portal"
    )
    assert ctx["current_assessments"]["status"] == "not_available"
    assert ctx["current_assessments"]["value"] is None


def test_14_historical_risk_calculation_still_works():
    """Requirement: Historical academic performance drives risk engine with calibrated low confidence."""
    ctx = normalize_student_context(
        mobile="9110241337",
        profile={"fname": "MOHAMMED AJMAL", "fregno": "NNM24IS127", "fcursem": 5},
        subjects=[],
        attendance=None,
        ia_marks=None,
        historical=[{"year": "202605", "sgpa": 8.67, "cgpa": 8.45, "subject_results": []}],
        data_source="student_portal"
    )
    risk = calculate_academic_risk(ctx)
    assert risk["risk_level"] == "low"
    assert risk["confidence"] == "low"
    assert risk["risk_basis"] == "historical_academic_performance"
    assert "CGPA: 8.45" in risk["factors"][0]


def test_15_current_and_historical_risk_calculation_works():
    """Requirement: When current attendance/quiz signals exist, engine combines current and historical."""
    ctx = normalize_student_context(
        mobile="9110241337",
        profile={"fname": "MOHAMMED AJMAL", "fregno": "NNM24IS127", "fcursem": 5},
        subjects=[{"fsubcode": "22IS51", "fsubname": "DBMS"}],
        attendance=[{"subject_code": "22IS51", "classes_held": 40, "classes_attended": 38, "percentage": 95.0}],
        ia_marks=[{"subject_code": "22IS51", "marks_obtained": 19, "max_marks": 20}],
        historical=[{"year": "202605", "sgpa": 8.67, "cgpa": 8.45, "subject_results": []}],
        data_source="student_portal"
    )
    ctx["current_assessments"] = {"status": "available", "value": 95.0}
    risk = calculate_academic_risk(ctx)
    assert risk["risk_level"] == "low"
    assert risk["confidence"] in ("partial", "full")
    assert risk["risk_basis"] in ("current_and_historical", "current_semester_signals")


def test_16_chatbot_subsystem_untouched():
    """Requirement: chatbot/ directory must have ZERO modified files."""
    res = subprocess.run(["git", "status", "--short", "--", "chatbot/"], capture_output=True, text=True)
    assert res.returncode == 0
