import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "edu-backend"))
import pytest
from utils.academic_guidance import evaluate_student_academic_guidance


def test_prayag_m_foundation_building_guidance():
    """
    Test PRAYAG M: CGPA 5.24, SGPA 4.50, Backlogs 4.
    Must NEVER produce 'Distinction standing', 'Maintaining distinction', or 'strong academic performance'.
    Must produce foundation building guidance.
    """
    hist_perf = {
        "cgpa": 5.24,
        "latest_sgpa": 4.50,
        "sgpa_trend": "declining",
        "arrears_count": 4,
        "total_semesters_completed": 4
    }
    guidance = evaluate_student_academic_guidance(hist_perf)
    
    # 1. Negative assertions: MUST NOT have false distinction claims
    assert "Distinction standing" not in guidance["standing_label"]
    assert "Maintaining distinction" not in guidance["outlook_message"]
    assert "strong academic performance" not in guidance["message"].lower()
    
    # 2. Positive assertions: honest, encouraging guidance
    assert guidance["state"] == "foundation_building"
    assert "Strengthen" in guidance["headline"] or "Foundation" in guidance["headline"]
    assert "4 pending backlog(s)" in guidance["message"]
    assert "5.24" in guidance["message"]
    assert "4.50" in guidance["message"]
    
    # 3. No risk labels in guidance
    assert "HIGH RISK" not in guidance["message"]
    assert "MEDIUM RISK" not in guidance["message"]
    assert "LOW RISK" not in guidance["message"]


def test_mohammed_ajmal_strong_momentum_guidance():
    """
    Test MOHAMMED AJMAL: CGPA 8.45, SGPA 8.67, Backlogs 0, Improving.
    Must produce strong momentum / distinction standing guidance.
    """
    hist_perf = {
        "cgpa": 8.45,
        "latest_sgpa": 8.67,
        "sgpa_trend": "improving",
        "arrears_count": 0,
        "total_semesters_completed": 4
    }
    guidance = evaluate_student_academic_guidance(hist_perf)
    
    assert guidance["state"] == "strong_momentum"
    assert "Strong Academic Momentum" in guidance["headline"]
    assert "building strong momentum" in guidance["message"].lower()
    assert "8.45" in guidance["message"]
    assert "8.67" in guidance["message"]
    assert "Positive Trajectory" in guidance["outlook_status"]
    
    # No risk labels in guidance
    assert "HIGH RISK" not in guidance["message"]
    assert "MEDIUM RISK" not in guidance["message"]
    assert "LOW RISK" not in guidance["message"]


def test_steady_academic_progress_guidance():
    """
    Test Steady Progress: CGPA 6.80, SGPA 6.90, Backlogs 0, Stable.
    """
    hist_perf = {
        "cgpa": 6.80,
        "latest_sgpa": 6.90,
        "sgpa_trend": "stable",
        "arrears_count": 0,
        "total_semesters_completed": 4
    }
    guidance = evaluate_student_academic_guidance(hist_perf)
    
    assert guidance["state"] == "steady_progress"
    assert "Steady Academic Progress" in guidance["headline"]
    assert "steady academic path" in guidance["message"].lower()
    assert "First Class standing" in guidance["standing_label"]


def test_strengthening_required_with_moderate_backlogs():
    """
    Test Moderate Backlogs: CGPA 5.80, SGPA 5.50, Backlogs 2.
    Must NOT produce distinction standing.
    """
    hist_perf = {
        "cgpa": 5.80,
        "latest_sgpa": 5.50,
        "sgpa_trend": "declining",
        "arrears_count": 2,
        "total_semesters_completed": 3
    }
    guidance = evaluate_student_academic_guidance(hist_perf)
    
    assert guidance["state"] == "strengthening_required"
    assert "Focus on Strengthening Performance" in guidance["headline"]
    assert "Distinction standing" not in guidance["standing_label"]
    assert "2 pending subject(s)" in guidance["message"]


def test_sanitized_portal_context_has_zero_risk_tags():
    """
    Test that sanitized context delivered to students strips all internal risk fields.
    """
    from routes.student import sanitize_portal_context_for_student
    raw_ctx = {
        "identity": {"name": "PRAYAG M", "usn": "NNM24IS172"},
        "historical_academic_performance": {
            "cgpa": 5.24,
            "latest_sgpa": 4.50,
            "sgpa_trend": "declining",
            "arrears_count": 4,
            "total_semesters_completed": 4
        },
        "risk_evaluation": {
            "risk_level": "high",
            "risk_score": 73.0,
            "confidence": "low",
            "factors": ["Low CGPA", "4 backlogs"]
        }
    }
    
    sanitized = sanitize_portal_context_for_student(raw_ctx)
    assert "risk_evaluation" not in sanitized
    assert "risk_level" not in sanitized
    assert "risk_score" not in sanitized
    assert "confidence" not in sanitized
    assert "factors" not in sanitized
    assert "academic_guidance" in sanitized
    assert sanitized["academic_guidance"]["state"] == "foundation_building"
