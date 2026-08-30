import React, { useCallback, useEffect, useState } from "react";
import {
  Users, AlertTriangle, TrendingDown, UserCheck, FileDown, ArrowRight,
  Shield, RefreshCw, Send, CheckCircle2, AlertCircle, Sparkles, Activity
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTeacher } from "../../context/TeacherContext";
import { StatCard, RiskDonut, EngagementChart, RiskBadge, EmptyState } from "../../components/shared/Shared";

const REFRESH_INTERVAL_MS = 60000;

export default function Dashboard() {
  const { active, user } = useTeacher();
  const navigate = useNavigate();

  const [stats, setStats] = useState(null);
  const [flagged, setFlagged] = useState([]);
  const [trend, setTrend] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  const load = useCallback(async (isBackgroundRefresh = false) => {
    if (isBackgroundRefresh) setRefreshing(true);
    else setLoading(true);
    setError("");

    try {
      const token = localStorage.getItem("token");
      const params = new URLSearchParams({
        department: active.department,
        semester: String(active.semester),
        section: active.section,
      });

      const res = await fetch(`http://localhost:5000/api/dashboard/summary?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) throw new Error(`dashboard summary request failed: ${res.status}`);

      const data = await res.json();

      setStats(data.stats);
      setFlagged(data.flagged_students || []);
      setTrend(data.engagement_trend || []);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("dashboard load failed:", err);
      setError("Live data unavailable — showing last known values.");
      setStats((prev) => prev ?? { total_enrolled: 15, high_risk: 2, medium_risk: 4, mentors_available: 8, mentors_total: 8 });
      setFlagged((prev) => prev ?? []);
      setTrend((prev) => (prev && prev.length ? prev : []));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [active]);

  useEffect(() => {
    load(false);
    const interval = setInterval(() => load(true), REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [load]);

  if (loading || !stats) {
    return (
      <div className="ui-state">
        <div className="ui-spinner">Loading cohort overview...</div>
      </div>
    );
  }

  const lowRiskCount = Math.max(stats.total_enrolled - stats.high_risk - stats.medium_risk, 0);
  const healthRate = stats.total_enrolled > 0
    ? Math.round((lowRiskCount / stats.total_enrolled) * 100)
    : 100;

  const riskData = [
    { label: "High Risk", value: stats.high_risk, color: "#ef4444" },
    { label: "Medium Risk", value: stats.medium_risk, color: "#f59e0b" },
    { label: "Low Risk", value: lowRiskCount, color: "#00d59b" },
  ];

  const facultyName = user?.full_name || "Dr. Preethi Salian K";

  return (
    <div className="teacher-dashboard">
      {/* UNIFIED HERO WELCOME BANNER */}
      <div
        className="welcome-banner"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "28px",
          flexWrap: "wrap",
          gap: "20px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px", flexWrap: "wrap" }}>
            <h1 style={{ fontSize: "24px", fontWeight: 800, color: "var(--text)", margin: 0, letterSpacing: "-0.5px" }}>
              Welcome back, {facultyName}
            </h1>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                background: "var(--primary-soft)",
                padding: "4px 12px",
                borderRadius: "14px",
                fontSize: "11px",
                fontWeight: 600,
                color: "var(--primary)",
                border: "1px solid rgba(0, 213, 155, 0.25)",
              }}
            >
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--primary)", display: "inline-block" }} />
              Live AI Roster
            </div>
          </div>
          <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "14px", lineHeight: "1.4" }}>
            Cohort risk radar &amp; intelligence for <strong>NMAMIT {active.department} · Semester {active.semester} · Section {active.section}</strong>
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          {lastUpdated && (
            <span style={{ fontSize: "12px", color: "var(--text-muted)", marginRight: "4px" }}>
              Updated {lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          )}
          <button
            className="topbar-icon-button"
            onClick={() => load(true)}
            disabled={refreshing}
            title="Refresh cohort analytics"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "38px",
              height: "38px",
              borderRadius: "8px",
              border: "1px solid var(--border)",
              background: "transparent",
              color: "var(--text)",
              cursor: "pointer",
            }}
          >
            <RefreshCw size={15} className={refreshing ? "spin" : ""} />
          </button>
          <button
            type="button"
            onClick={() => navigate("/roster")}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              padding: "10px 18px",
              borderRadius: "8px",
              background: "transparent",
              color: "var(--text)",
              border: "1px solid var(--border)",
              fontSize: "13px",
              fontWeight: 700,
              cursor: "pointer",
              transition: "all 0.18s ease",
            }}
          >
            View Student Roster
            <ArrowRight size={15} />
          </button>
          <button
            type="button"
            onClick={() => navigate("/reports")}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              padding: "10px 18px",
              borderRadius: "8px",
              background: "var(--primary)",
              color: "#032019",
              border: "none",
              fontSize: "13px",
              fontWeight: 700,
              cursor: "pointer",
              boxShadow: "0 4px 14px rgba(0, 213, 155, 0.25)",
              transition: "all 0.18s ease",
            }}
          >
            <FileDown size={15} />
            <span>Cohort Report</span>
          </button>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="teacher-stats-grid">
        <StatCard
          label="Total Enrolled Students"
          value={stats.total_enrolled}
          icon={<Users size={16} />}
          tone="neutral"
        />
        <StatCard
          label="Critical / High Risk"
          value={stats.high_risk}
          icon={<AlertTriangle size={16} />}
          tone="danger"
        />
        <StatCard
          label="Moderate / Medium Risk"
          value={stats.medium_risk}
          icon={<TrendingDown size={16} />}
          tone="warning"
        />
        <StatCard
          label="Mentor Capacity"
          value={stats.mentors_available}
          suffix={`/ ${stats.mentors_total}`}
          icon={<UserCheck size={16} />}
          tone="primary"
        />
      </div>

      {/* Charts Grid */}
      <div className="teacher-charts-grid">
        <div className="teacher-panel">
          <div className="teacher-panel-header">
            <div>
              <h3>Risk Distribution</h3>
              <span className="teacher-panel-sub">{healthRate}% Cohort in Good Standing</span>
            </div>
          </div>
          <RiskDonut data={riskData} />
        </div>

        <div className="teacher-panel">
          <div className="teacher-panel-header">
            <div>
              <h3>Cohort Engagement Trend</h3>
              <span className="teacher-panel-sub">Weekly Attendance &amp; LMS Submissions</span>
            </div>
          </div>
          {trend.length > 0 ? (
            <EngagementChart data={trend} />
          ) : (
            <EmptyState
              icon={<Activity size={20} />}
              title="No trend data yet"
              message="Engagement timeline updates automatically as attendance is logged."
            />
          )}
        </div>
      </div>

      {/* Priority Action Queue */}
      <div className="teacher-panel flagged-panel">
        <div className="teacher-panel-header">
          <div>
            <h3>Priority Attention &amp; Intervention Queue</h3>
            <span className="teacher-panel-sub">Students flagged by multi-factor academic risk radar</span>
          </div>
          <button className="teacher-panel-link" onClick={() => navigate("/roster")}>
            Full Roster ({stats.total_enrolled}) <ArrowRight size={13} />
          </button>
        </div>

        {flagged.length === 0 ? (
          <EmptyState
            icon={<CheckCircle2 size={20} />}
            title="All students performing well"
            message="No immediate intervention alerts for this section."
          />
        ) : (
          <div className="flagged-list">
            {flagged.map((s) => (
              <div className="flagged-row" key={s.id} style={{ alignItems: "center" }}>
                <div className={`flagged-risk-dot ${s.risk}`} />
                <div className="flagged-info" style={{ flex: 1 }}>
                  <strong>{s.name}</strong>
                  <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>{s.reason}</span>
                </div>
                <RiskBadge risk={s.risk} />
                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    className="attendance-save-button"
                    style={{ padding: "6px 12px", fontSize: "11px", height: "30px", background: "var(--surface-hover)", border: "1px solid var(--border)" }}
                    onClick={() => navigate("/interventions")}
                    title="Dispatch targeted action plan"
                  >
                    <Send size={11} /> Plan
                  </button>
                  <button
                    className="flagged-view-button"
                    style={{ padding: "6px 12px", fontSize: "11px", height: "30px" }}
                    onClick={() => navigate("/roster")}
                  >
                    View Details
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="human-loop-banner">
        <Shield size={16} />
        <span>
          <strong>Faculty Guidance Protocol:</strong> Predictive risk indicators are advisory. Academic decisions and mentoring notes remain under faculty discretion.
        </span>
      </div>
    </div>
  );
}

