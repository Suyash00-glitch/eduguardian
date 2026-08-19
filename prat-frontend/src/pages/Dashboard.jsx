import React, { useCallback, useEffect, useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  TrendingDown,
  TrendingUp,
  Activity,
  Target,
  Sparkles,
  AlertTriangle,
} from "lucide-react";

import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

import { studentService } from "../services/studentService";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

function Dashboard() {
  const navigate = useNavigate();
const { user } = useAuth();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const result = await studentService.getDashboard();
      setData(result);
    } catch (err) {
      setError(err.message || "Unable to load dashboard.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (loading) {
    return <LoadingState message="Loading your academic overview..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Unable to load dashboard"
        message={error}
        onRetry={loadDashboard}
      />
    );
  }

  if (!data) {
    return (
      <ErrorState
        title="No dashboard data"
        message="We couldn't find your academic information."
        onRetry={loadDashboard}
      />
    );
  }

  const assignmentPercentage =
    data.assignments.total > 0
      ? Math.round((data.assignments.completed / data.assignments.total) * 100)
      : 0;

  return (
    <div className="dashboard-page">
      {/* Header */}

      <div className="dashboard-welcome">
        <div>
          <span className="dashboard-eyebrow">ACADEMIC OVERVIEW</span>

     <h2>
  Good afternoon, {user?.name || user?.full_name || "Student"}.
</h2>

          <p>Here's how your academic journey is looking right now.</p>
        </div>

        <button
          className="dashboard-action"
          onClick={() => navigate("/progress")}
        >
          View full progress
          <ArrowRight size={14} />
        </button>
      </div>

      {/* Main Stats */}

      <div className="dashboard-stats">
        {/* Attendance */}

        <div className="dashboard-stat-card">
          <div className="stat-card-top">
            <div className="stat-icon">
              <Activity size={17} />
            </div>

            <span className="stat-positive">+{data.attendanceChange}%</span>
          </div>

          <div className="stat-value">{data.attendance}%</div>

          <div className="stat-label">Overall Attendance</div>

          <div className="stat-progress">
            <span
              style={{
                width: `${data.attendance}%`,
              }}
            />
          </div>
        </div>

        {/* Average */}

        <div className="dashboard-stat-card">
          <div className="stat-card-top">
            <div className="stat-icon">
              <TrendingUp size={17} />
            </div>

            <span className="stat-positive">+{data.scoreChange}%</span>
          </div>

          <div className="stat-value">{data.averageScore}%</div>

          <div className="stat-label">Average Performance</div>

          <div className="stat-progress">
            <span
              style={{
                width: `${data.averageScore}%`,
              }}
            />
          </div>
        </div>

        {/* Assignments */}

        <div className="dashboard-stat-card">
          <div className="stat-card-top">
            <div className="stat-icon">
              <ClipboardCheck size={17} />
            </div>

            <span className="stat-neutral">
              {data.assignments.missed} missed
            </span>
          </div>

          <div className="stat-value">
            {data.assignments.completed}
            <small>/{data.assignments.total}</small>
          </div>

          <div className="stat-label">Assignments Completed</div>

          <div className="stat-progress">
            <span
              style={{
                width: `${assignmentPercentage}%`,
              }}
            />
          </div>
        </div>

        {/* LMS */}

        <div className="dashboard-stat-card">
          <div className="stat-card-top">
            <div className="stat-icon">
              <Clock3 size={17} />
            </div>

            <span className="stat-positive">Active</span>
          </div>

          <div className="stat-value">{data.lmsActivity}%</div>

          <div className="stat-label">LMS Engagement</div>

          <div className="stat-progress">
            <span
              style={{
                width: `${data.lmsActivity}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Middle */}

      <div className="dashboard-middle">
        {/* Recovery */}

        <div className="recovery-card">
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">AI RECOVERY ESTIMATE</span>

              <h3>Your recovery probability</h3>
            </div>

            <Sparkles size={17} className="section-ai-icon" />
          </div>

          <div className="recovery-content">
            <div className="recovery-circle">
              <div>
                <strong>{data.recoveryProbability}%</strong>

                <span>probability</span>
              </div>
            </div>

            <div className="recovery-description">
              <div className="recovery-status">
                <CheckCircle2 size={15} />

                <strong>Positive trajectory</strong>
              </div>

              <p>
                Your recent academic activity suggests that you're on a good
                path to maintaining your current performance.
              </p>

              <button onClick={() => navigate("/recovery")}>
                View recovery plan
                <ArrowRight size={13} />
              </button>
            </div>
          </div>
        </div>

        {/* Support Signal */}

        <div className="support-card">
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">AI SUPPORT SIGNAL</span>

              <h3>What EduGuardian sees</h3>
            </div>

            <div className="signal-status">
              <span />
              {data.supportSignal.status}
            </div>
          </div>

          <div className="support-message">
            <div className="support-icon">
              <Sparkles size={17} />
            </div>

            <p>{data.supportSignal.message}</p>
          </div>

          <div className="support-footer">
            <span>AI-generated insight</span>

            <button onClick={() => navigate("/insights")}>
              Understand why
              <ArrowRight size={12} />
            </button>
          </div>
        </div>
      </div>

      {/* Bottom */}

      <div className="dashboard-bottom">


        

        {/* Quick Actions */}

        <div className="dashboard-panel">
          <div className="panel-header">
            <div>
              <span className="section-eyebrow">NEXT STEPS</span>

              <h3>Quick actions</h3>
            </div>
          </div>

          <div className="quick-actions">
            <button onClick={() => navigate("/coach")}>
              <div className="quick-action-icon">
                <Sparkles size={16} />
              </div>

              <div>
                <strong>Talk to AI Coach</strong>

                <span>Get personalized guidance</span>
              </div>

              <ArrowRight size={13} />
            </button>

            <button onClick={() => navigate("/goals")}>
              <div className="quick-action-icon">
                <Target size={16} />
              </div>

              <div>
                <strong>Review your goals</strong>

                <span>Keep your academic targets on track</span>
              </div>

              <ArrowRight size={13} />
            </button>

            <button onClick={() => navigate("/insights")}>
              <div className="quick-action-icon">
                <LightbulbIcon />
              </div>

              <div>
                <strong>Explore your insights</strong>

                <span>Understand what affects your progress</span>
              </div>

              <ArrowRight size={13} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function LightbulbIcon() {
  return <span className="quick-lightbulb">✦</span>;
}

export default Dashboard;
