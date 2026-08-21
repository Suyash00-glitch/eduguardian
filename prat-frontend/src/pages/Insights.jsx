import React, { useCallback, useEffect, useState } from "react";

import {
  ArrowRight,
  CheckCircle2,
  Info,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import { useNavigate } from "react-router-dom";

import { studentService } from "../services/studentService";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

function Insights() {
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadInsights = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const result = await studentService.getInsights();

      setData(result);
    } catch (err) {
      setError(err.message || "Unable to load your insights.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInsights();
  }, [loadInsights]);

  if (loading) {
    return <LoadingState message="Analyzing your academic patterns..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Unable to load insights"
        message={error}
        onRetry={loadInsights}
      />
    );
  }

  if (!data) {
    return (
      <ErrorState
        title="No insights available"
        message="There isn't enough academic data to generate insights yet."
        onRetry={loadInsights}
      />
    );
  }

  return (
    <div className="insights-page">
      {/* Header */}

      <div className="insights-header">
        <div>
          <span className="dashboard-eyebrow">EXPLAINABLE AI</span>

          <h2>My Insights</h2>

          <p>Understand what is influencing your academic progress.</p>
        </div>

        <div className="ai-powered-label">
          <Sparkles size={13} />
          AI powered
        </div>
      </div>

      {/* Main AI Summary */}

      <section className="insight-summary">
        <div className="insight-summary-main">
          <div className="insight-summary-icon">
            <Sparkles size={19} />
          </div>

          <div>
            <span className="section-eyebrow">CURRENT SUPPORT SIGNAL</span>

            <h3>{data.signal}</h3>

            <p>{data.summary}</p>
          </div>
        </div>

        <div className="insight-momentum">
          <span>LEARNING TRAJECTORY</span>
          <strong>{data.recoveryProbability >= 80 ? "On Track" : (data.recoveryProbability >= 60 ? "Steady Momentum" : "Focus Recommended")}</strong>
        </div>
      </section>

      {/* Trajectory */}

      <section className="insight-recovery">
        <div>
          <span className="section-eyebrow">ACADEMIC TRAJECTORY</span>

          <h3>How likely are you to stay on track?</h3>

          <p>
            This estimate is based on recent academic engagement patterns. It is
            designed to provide support and constructive guidance.
          </p>
        </div>

        <div className="insight-probability">
          <div
            className="probability-ring"
            style={{
              "--progress": `${data.recoveryProbability * 3.6}deg`,
            }}
          >
            <strong>{data.recoveryProbability}%</strong>

            <span>on track</span>
          </div>
        </div>
      </section>

      {/* Factors */}

      <section className="insight-panel">
        <div className="insight-panel-header">
          <div>
            <span className="section-eyebrow">WHY THIS SIGNAL?</span>

            <h3>Factors influencing your progress</h3>
          </div>

          <div className="explainable-label">
            <Info size={12} />
            Explainable
          </div>
        </div>

        <div className="factor-list">
          {data.factors.map((factor) => {
            const positive = factor.impact === "positive";

            return (
              <div className="factor-row" key={factor.name}>
                <div
                  className={`factor-icon ${
                    positive ? "positive" : "negative"
                  }`}
                >
                  {positive ? (
                    <TrendingUp size={15} />
                  ) : (
                    <TrendingDown size={15} />
                  )}
                </div>

                <div className="factor-info">
                  <div className="factor-title">
                    <strong>{factor.name}</strong>

                    <span
                      className={
                        positive ? "factor-positive" : "factor-negative"
                      }
                    >
                      {factor.value}
                    </span>
                  </div>

                  <p>{factor.explanation}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Recent Changes */}

      <section className="insight-panel">
        <div className="insight-panel-header">
          <div>
            <span className="section-eyebrow">RECENT CHANGES</span>

            <h3>What changed recently?</h3>
          </div>
        </div>

        <div className="change-grid">
          {data.changes.map((change) => {
            const positive = change.direction === "up";

            return (
              <div className="change-card" key={change.label}>
                <div className="change-card-top">
                  <span>{change.label}</span>

                  {positive ? (
                    <TrendingUp size={14} className="change-positive" />
                  ) : (
                    <TrendingDown size={14} className="change-negative" />
                  )}
                </div>

                <strong
                  className={positive ? "change-positive" : "change-negative"}
                >
                  {change.value}
                </strong>

                <span className="change-period">
                  compared with previous period
                </span>
              </div>
            );
          })}
        </div>
      </section>

      {/* Action */}

      <section className="insight-action">
        <div className="insight-action-icon">
          <CheckCircle2 size={18} />
        </div>

        <div>
          <span className="section-eyebrow">NEXT STEP</span>

          <h3>Want to improve your academic trajectory?</h3>

          <p>
            EduGuardian can create a personalized recovery plan based on your
            current situation.
          </p>
        </div>

        <button onClick={() => navigate("/recovery")}>
          View my plan
          <ArrowRight size={13} />
        </button>
      </section>
    </div>
  );
}

export default Insights;
