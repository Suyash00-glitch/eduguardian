"""
Machine Learning Extension Point for Student Insight Agent.

Provides a clean interface for integrating future trained ML models
(e.g., LightGBM, XGBoost, or SHAP-based feature importance explainers)
without coupling the agent to a specific ML framework.

ARCHITECTURE:
- FeatureExtractor: Extracts a standardized numerical/categorical feature vector from StudentContext.
- MLPredictorInterface: Abstract contract for model scoring and feature attribution.
- BaselineRulePredictor: Default baseline implementation used until trained model weights are provided.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field

from chatbot.backend.schemas.student import StudentContext


class AcademicFeatureVector(BaseModel):
    """Normalized tabular feature vector for ML model scoring."""
    attendance_rate: float = 85.0
    attendance_is_declining: float = 0.0
    average_subject_marks: float = 70.0
    failing_subjects_count: int = 0
    assignment_completion_rate: float = 0.85
    pending_assignments_count: int = 0
    gpa: float = 7.0
    lms_logins_30d: int = 15
    trend_is_downward: float = 0.0


class MLPredictionResult(BaseModel):
    """Output from ML model inference with explainability attributions."""
    support_intensity: str = "standard"  # 'standard' | 'guided' | 'intensive'
    risk_score: float = 0.2  # 0.0 (low) to 1.0 (high)
    feature_attributions: dict[str, float] = Field(
        default_factory=dict,
        description="SHAP-equivalent feature contribution values",
    )
    predicted_focus_domains: list[str] = Field(default_factory=list)


class FeatureExtractor:
    """Extracts machine learning features from raw StudentContext."""

    @staticmethod
    def extract_features(context: StudentContext) -> AcademicFeatureVector:
        # Attendance features
        att_rate = 85.0
        att_declining = 0.0
        if context.attendance and context.attendance.overall_percentage is not None:
            att_rate = context.attendance.overall_percentage
            trend = str(context.attendance.trend or context.attendance.recent_trend or "").lower()
            if trend == "declining":
                att_declining = 1.0

        # Course marks features
        avg_marks = 70.0
        failing_count = 0
        if context.subjects:
            marks_list = [
                s.current_marks_percentage if s.current_marks_percentage is not None else s.marks_percentage
                for s in context.subjects
                if (s.current_marks_percentage is not None or s.marks_percentage is not None)
            ]
            if marks_list:
                avg_marks = sum(marks_list) / len(marks_list)
                failing_count = sum(1 for m in marks_list if m < 50.0)

        # Assignment features
        asg_rate = 0.85
        pending_count = 0
        if context.assignments:
            if context.assignments.total_assigned > 0:
                asg_rate = context.assignments.total_submitted / context.assignments.total_assigned
            pending_count = context.assignments.pending_count

        # GPA
        gpa = 7.0
        if context.assessments and context.assessments.gpa is not None:
            gpa = context.assessments.gpa

        # LMS
        lms_logins = 15
        if context.engagement and context.engagement.lms_logins_last_30_days is not None:
            lms_logins = context.engagement.lms_logins_last_30_days

        # Trend
        trend_down = 0.0
        if context.trends and context.trends.grade_trajectory:
            if context.trends.grade_trajectory.lower() in ("downward", "declining"):
                trend_down = 1.0

        return AcademicFeatureVector(
            attendance_rate=att_rate,
            attendance_is_declining=att_declining,
            average_subject_marks=avg_marks,
            failing_subjects_count=failing_count,
            assignment_completion_rate=asg_rate,
            pending_assignments_count=pending_count,
            gpa=gpa,
            lms_logins_30d=lms_logins,
            trend_is_downward=trend_down,
        )


class MLPredictorInterface(ABC):
    """Abstract interface for student academic performance prediction."""

    @abstractmethod
    def predict(self, features: AcademicFeatureVector) -> MLPredictionResult:
        """Score feature vector and return predictions with feature attributions."""
        pass


class BaselineRulePredictor(MLPredictorInterface):
    """
    Default baseline predictor.
    Uses explainable heuristics matching trained model thresholds.
    Replaceable by LightGBMPredictor or XGBoostPredictor when weights are loaded.
    """

    def predict(self, features: AcademicFeatureVector) -> MLPredictionResult:
        attributions: dict[str, float] = {}
        focus_domains: list[str] = []

        # Feature contribution weighting (heuristic baseline)
        if features.attendance_rate < 75.0:
            attributions["attendance_gap"] = (75.0 - features.attendance_rate) * 0.02
            focus_domains.append("Attendance Consistency")

        if features.attendance_is_declining > 0.5:
            attributions["attendance_trajectory"] = 0.15

        if features.assignment_completion_rate < 0.75:
            attributions["missing_assignments"] = (0.75 - features.assignment_completion_rate) * 0.5
            focus_domains.append("Coursework Submissions")

        if features.failing_subjects_count > 0:
            attributions["subject_drag"] = features.failing_subjects_count * 0.25
            focus_domains.append("Subject Revision")

        if features.trend_is_downward > 0.5:
            attributions["trend_momentum"] = 0.10

        total_risk = min(1.0, sum(attributions.values()))

        if total_risk >= 0.50:
            intensity = "intensive"
        elif total_risk >= 0.20 or len(focus_domains) > 0:
            intensity = "guided"
        else:
            intensity = "standard"

        return MLPredictionResult(
            support_intensity=intensity,
            risk_score=total_risk,
            feature_attributions=attributions,
            predicted_focus_domains=focus_domains,
        )
