import React, { useCallback, useEffect, useState } from "react";
import { Users, AlertTriangle, TrendingDown, UserCheck, FileDown, ArrowRight, Shield, RefreshCw } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTeacher } from "../../context/TeacherContext";
import { StatCard, RiskDonut, EngagementChart, RiskBadge, EmptyState } from "../../components/shared/Shared";

// polling interval for "live" refresh — adjust or remove if you'd rather
// wire up websockets/SSE later instead
const REFRESH_INTERVAL_MS = 30000;

export default function Dashboard() {
  const { active } = useTeacher();
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

      // Backend contract expected here:
      // GET /api/dashboard/summary?department=&semester=&section=
      // -> {
      //      stats: { total_enrolled, high_risk, medium_risk, mentors_available, mentors_total },
      //      flagged_students: [{ id, name, risk, reason }],
      //      engagement_trend: [{ week, attendance, engagement }]   // last 4 weeks, % values
      //    }
      const res = await fetch(`http://127.0.0.1:8000/api/dashboard/summary?${params}`, {
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
      // only seed placeholders on the very first load, never overwrite real data on a failed refresh
      setStats((prev) => prev ?? { total_enrolled: 0, high_risk: 0, medium_risk: 0, mentors_available: 0, mentors_total: 0 });
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

  if (loading || !stats) return <div className="ui-state"><div className="ui-spinner">Loading dashboard...</div></div>;

  const riskData = [
    { label: "High Risk", value: stats.high_risk, color: "#e85c47" },
    { label: "Medium Risk", value: stats.medium_risk, color: "#e8c547" },
    { label: "Low Risk", value: Math.max(stats.total_enrolled - stats.high_risk - stats.medium_risk, 0), color: "var(--primary)" },
  ];

  return (
    <div className="teacher-dashboard">
      <div className="teacher-dashboard-header">
        <div>
          <span className="dashboard-eyebrow">EARLY DETECTION</span>
          <h2>Dashboard &amp; Analytics</h2>
          <p>Cohort-wide risk signals for {active.department} · Sem {active.semester} · Section {active.section}</p>
        </div>

        <div className="dashboard-live-status">
          {error && <span className="dashboard-live-error">{error}</span>}
          <span className="dashboard-live-updated">
            {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : ""}
          </span>
          <button className="dashboard-refresh-button" onClick={() => load(true)} disabled={refreshing}>
            <RefreshCw size={13} className={refreshing ? "spin" : ""} />
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      <div className="export-banner">
        <div>
          <strong>Cohort Health &amp; Export Center</strong>
          <span>Download full batch compliance or raw data reports for active students.</span>
        </div>
        <button className="export-banner-button" onClick={() => navigate("/reports")}>
          <FileDown size={14} />
          Go to Reports &amp; Download
        </button>
      </div>

      <div className="teacher-stats-grid">
        <StatCard label="Total Enrolled" value={stats.total_enrolled} icon={<Users size={16} />} tone="neutral" />
        <StatCard label="High Risk Flags" value={stats.high_risk} icon={<AlertTriangle size={16} />} tone="danger" />
        <StatCard label="Medium Risk" value={stats.medium_risk} icon={<TrendingDown size={16} />} tone="warning" />
        <StatCard
          label="Available Mentors"
          value={stats.mentors_available}
          suffix={`/ ${stats.mentors_total}`}
          icon={<UserCheck size={16} />}
          tone="primary"
        />
      </div>

      <div className="teacher-charts-grid">
        <div className="teacher-panel">
          <div className="teacher-panel-header"><h3>Cohort Risk Distribution</h3></div>
          <RiskDonut data={riskData} />
        </div>

        <div className="teacher-panel">
          <div className="teacher-panel-header">
            <h3>Cohort Engagement Trend</h3>
            <span className="teacher-panel-sub">Last 4 weeks</span>
          </div>
          {trend.length > 0 ? (
            <EngagementChart data={trend} />
          ) : (
            <EmptyState icon={<TrendingDown size={20} />} title="No trend data yet" message="Engagement history will appear here once attendance/LMS data comes in." />
          )}
        </div>
      </div>

      <div className="teacher-panel flagged-panel">
        <div className="teacher-panel-header">
          <h3>Flagged Students</h3>
          <button className="teacher-panel-link" onClick={() => navigate("/roster")}>
            View all <ArrowRight size={12} />
          </button>
        </div>

        {flagged.length === 0 ? (
          <EmptyState icon={<Users size={20} />} title="No flagged students right now" message="Nobody in this cohort currently needs intervention." />
        ) : (
          <div className="flagged-list">
            {flagged.map((s) => (
              <div className="flagged-row" key={s.id}>
                <div className={`flagged-risk-dot ${s.risk}`} />
                <div className="flagged-info">
                  <strong>{s.name}</strong>
                  <span>{s.reason}</span>
                </div>
                <RiskBadge risk={s.risk} />
                <button className="flagged-view-button" onClick={() => navigate("/roster")}>View</button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="human-loop-banner">
        <Shield size={15} />
        <span><strong>Human-in-the-loop:</strong> AI only suggests interventions. Staff decisions are final.</span>
      </div>
    </div>
  );
}
