import React, { useCallback, useEffect, useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
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
      <div className="insights-header" style={{ marginBottom: "24px" }}>
        <div>
          <h1 style={{ fontSize: "var(--font-2xl)", fontWeight: 700, margin: 0, color: "var(--text)" }}>
            Academic Insights
          </h1>
          <p style={{ margin: "6px 0 0", fontSize: "var(--font-base)", color: "var(--text-secondary)" }}>
            Explainable analysis and personalized patterns influencing your academic performance.
          </p>
        </div>

        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "var(--font-xs)",
            fontWeight: 600,
            padding: "6px 12px",
            borderRadius: "20px",
            background: "rgba(6,214,160,0.12)",
            color: "var(--primary)",
            border: "1px solid rgba(6,214,160,0.25)",
          }}
        >
          <Sparkles size={14} />
          Diagnostic Guidance
        </div>
      </div>

      {/* Main Support Signal Summary */}
      <section
        className="insight-summary"
        style={{
          padding: "22px 24px",
          borderRadius: "12px",
          border: "1px solid var(--border)",
          background: "var(--surface)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "16px",
          marginBottom: "20px",
        }}
      >
        <div style={{ display: "flex", alignItems: "flex-start", gap: "16px", flex: 1 }}>
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "10px",
              background: "var(--primary-soft)",
              color: "var(--primary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <Sparkles size={20} />
          </div>

          <div>
            <h3 style={{ fontSize: "var(--font-lg)", fontWeight: 600, margin: 0, color: "var(--text)" }}>
              {data.signal}
            </h3>
            <p style={{ margin: "6px 0 0", fontSize: "var(--font-base)", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              {data.summary}
            </p>
          </div>
        </div>

        <div
          style={{
            padding: "12px 18px",
            borderRadius: "10px",
            background: "var(--surface-soft)",
            border: "1px solid var(--border)",
            textAlign: "center",
          }}
        >
          <span style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", display: "block" }}>
            Current Standing
          </span>
          <strong style={{ fontSize: "var(--font-md)", color: "var(--primary)", fontWeight: 700, marginTop: "2px", display: "block" }}>
            {data.recoveryProbability >= 80 ? "On Track" : data.recoveryProbability >= 60 ? "Steady Momentum" : "Focus Recommended"}
          </strong>
        </div>
      </section>

      {/* Trajectory */}
      <section
        className="insight-recovery"
        style={{
          padding: "22px 24px",
          borderRadius: "12px",
          border: "1px solid var(--border)",
          background: "var(--surface)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "20px",
          marginBottom: "20px",
        }}
      >
        <div style={{ maxWidth: "600px" }}>
          <h3 style={{ fontSize: "var(--font-md)", fontWeight: 600, margin: 0, color: "var(--text)" }}>
            Academic Success Outlook
          </h3>
          <p style={{ margin: "6px 0 0", fontSize: "var(--font-sm)", color: "var(--text-secondary)", lineHeight: 1.5 }}>
            This projection is evaluated from semester examination trends and academic engagement to provide constructive guidance.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              fontSize: "var(--font-stat)",
              fontWeight: 800,
              color: data.recoveryProbability >= 75 ? "var(--primary)" : "#ffd166",
            }}
          >
            {data.recoveryProbability}%
          </div>
          <span style={{ fontSize: "var(--font-sm)", color: "var(--text-muted)", fontWeight: 500 }}>
            Success probability
          </span>
        </div>
      </section>

      {/* Factors */}
      <section
        className="insight-panel"
        style={{
          padding: "22px 24px",
          borderRadius: "12px",
          border: "1px solid var(--border)",
          background: "var(--surface)",
          marginBottom: "20px",
        }}
      >
        <div style={{ marginBottom: "16px" }}>
          <h3 style={{ fontSize: "var(--font-md)", fontWeight: 600, margin: 0, color: "var(--text)" }}>
            Key Academic Factors
          </h3>
          <p style={{ margin: "4px 0 0", fontSize: "var(--font-sm)", color: "var(--text-muted)" }}>
            Primary drivers influencing your semester performance.
          </p>
        </div>

        <div className="factor-list" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {data.factors.map((factor) => {
            const positive = factor.impact === "positive";

            return (
              <div
                className="factor-row"
                key={factor.name}
                style={{
                  padding: "14px 18px",
                  borderRadius: "10px",
                  background: "var(--surface-soft)",
                  border: "1px solid var(--border)",
                  display: "flex",
                  alignItems: "center",
                  gap: "14px",
                }}
              >
                <div
                  style={{
                    width: "34px",
                    height: "34px",
                    borderRadius: "8px",
                    background: positive ? "rgba(6,214,160,0.12)" : "rgba(231,111,111,0.12)",
                    color: positive ? "var(--primary)" : "var(--danger)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  {positive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <strong style={{ fontSize: "var(--font-base)", color: "var(--text)" }}>{factor.name}</strong>
                    <span
                      style={{
                        fontSize: "var(--font-xs)",
                        fontWeight: 600,
                        padding: "2px 8px",
                        borderRadius: "4px",
                        background: positive ? "rgba(6,214,160,0.12)" : "rgba(231,111,111,0.12)",
                        color: positive ? "var(--primary)" : "var(--danger)",
                      }}
                    >
                      {factor.value}
                    </span>
                  </div>
                  <p style={{ margin: "4px 0 0", fontSize: "var(--font-sm)", color: "var(--text-secondary)", lineHeight: 1.4 }}>
                    {factor.explanation}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Action Recommendation */}
      <section
        className="insight-action"
        style={{
          padding: "20px 24px",
          borderRadius: "12px",
          border: "1px solid var(--border)",
          background: "var(--surface)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "14px", flex: 1 }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "9px",
              background: "var(--primary-soft)",
              color: "var(--primary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <CheckCircle2 size={18} />
          </div>

          <div>
            <h3 style={{ fontSize: "var(--font-base)", fontWeight: 600, margin: 0, color: "var(--text)" }}>
              Recommended Study Strategies
            </h3>
            <p style={{ margin: "3px 0 0", fontSize: "var(--font-sm)", color: "var(--text-secondary)" }}>
              Explore actionable weekly routines and revision planning with your personalized coach.
            </p>
          </div>
        </div>

        <button
          onClick={() => navigate("/coach")}
          style={{
            height: "38px",
            padding: "0 18px",
            borderRadius: "8px",
            border: "none",
            background: "var(--primary)",
            color: "#061412",
            fontWeight: 700,
            fontSize: "var(--font-sm)",
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          Open AI Coach
          <ArrowRight size={14} />
        </button>
      </section>
    </div>
  );
}

export default Insights;
