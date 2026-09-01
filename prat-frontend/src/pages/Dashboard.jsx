import React, { useCallback, useEffect, useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  TrendingDown,
  TrendingUp,
  Activity,
  Target,
  Sparkles,
  Award,
  BookOpen,
  FileText,
  Minus,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { studentService } from "../services/studentService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import { deriveAcademicStanding } from "../utils/academicStanding";

function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedSemester, setExpandedSemester] = useState(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const result = await studentService.getDashboard();
      setData(result);
      if (result?.historical_semesters && result.historical_semesters.length > 0) {
        setExpandedSemester(result.historical_semesters[0].semester);
      }
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

  const isPortal = data?.data_source === "student_portal";
  const identity = data?.identity || {};
  const histPerf = data?.historical_academic_performance || {};
  const studentName = identity.name || user?.name || user?.full_name || "Student";
  const studentUSN = identity.usn || user?.usn;
  const currentSem = identity.semester || user?.semester || 5;

  const cgpaDisplay = histPerf.cgpa !== null && histPerf.cgpa !== undefined ? Number(histPerf.cgpa).toFixed(2) : null;
  const sgpaDisplay = histPerf.latest_sgpa !== null && histPerf.latest_sgpa !== undefined ? Number(histPerf.latest_sgpa).toFixed(2) : null;
  const trend = histPerf.sgpa_trend || "stable";
  const completedSems = histPerf.completed_semesters || (data.historical_semesters?.length || 0);
  const totalCredits = histPerf.total_credits_earned || (completedSems * 21) || 84;

  // Dynamic Academic Standing & Supportive Guidance
  const academicStanding = deriveAcademicStanding(histPerf, data.academic_guidance);

  return (
    <div className="dashboard-page">
      {/* Header */}
      <div className="dashboard-welcome">
        <div>
          <h2>Welcome back, {studentName}</h2>
          <p>
            {isPortal
              ? `Academic status synchronized with University Solutions Student Portal (USN: ${studentUSN || "—"}).`
              : "Comprehensive overview of your cumulative academic progress and performance."}
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          {isPortal && (
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                fontSize: "var(--font-xs)",
                fontWeight: 600,
                padding: "6px 14px",
                borderRadius: "20px",
                background: "rgba(6,214,160,0.12)",
                color: "var(--primary)",
                border: "1px solid rgba(6,214,160,0.25)",
              }}
            >
              <CheckCircle2 size={13} />
              Portal Synchronized
            </span>
          )}

          <button
            className="dashboard-action"
            onClick={() => navigate("/profile")}
          >
            View Full Records
            <ArrowRight size={14} />
          </button>
        </div>
      </div>

      {/* CORE 4 ACADEMIC METRICS */}
      <div className="dashboard-stats">
        {/* Metric 1: Cumulative CGPA */}
        <div className="dashboard-stat-card">
          <div className="stat-card-top">
            <div className="stat-icon">
              <Award size={18} />
            </div>
            <span
              style={{
                fontSize: "var(--font-xs)",
                fontWeight: 600,
                padding: "3px 8px",
                borderRadius: "12px",
                background:
                  academicStanding.badgeTone === "warning"
                    ? "rgba(255,209,102,0.15)"
                    : "rgba(6,214,160,0.12)",
                color:
                  academicStanding.badgeTone === "warning"
                    ? "#ffd166"
                    : "var(--primary)",
              }}
            >
              {academicStanding.standingLabel || "Active Standing"}
            </span>
          </div>
          <div className="stat-value">
            {cgpaDisplay || "—"}
            <small>/ 10.0</small>
          </div>
          <div className="stat-label">Cumulative CGPA</div>
        </div>

        {/* Metric 2: Latest SGPA */}
        <div className="dashboard-stat-card">
          <div className="stat-card-top">
            <div className="stat-icon">
              <TrendingUp size={18} />
            </div>
            <span style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", fontWeight: 500 }}>
              {completedSems > 0 ? `Sem ${completedSems}` : "Exam Result"}
            </span>
          </div>
          <div className="stat-value">
            {sgpaDisplay || "—"}
            <small>/ 10.0</small>
          </div>
          <div className="stat-label">
            {completedSems > 0 ? `Semester ${completedSems} SGPA` : "Latest SGPA"}
          </div>
        </div>

        {/* Metric 3: Active Academic Term */}
        <div className="dashboard-stat-card">
          <div className="stat-card-top">
            <div className="stat-icon">
              <Target size={18} />
            </div>
            <span style={{ fontSize: "var(--font-xs)", color: "var(--primary)", fontWeight: 600 }}>
              Enrolled Term
            </span>
          </div>
          <div className="stat-value" style={{ color: "var(--text)" }}>
            Semester {currentSem}
            <small>{identity.department || "ISE"}</small>
          </div>
          <div className="stat-label">Active Academic Enrollment</div>
        </div>

        {/* Metric 4: Total Credits Earned */}
        <div className="dashboard-stat-card">
          <div className="stat-card-top">
            <div className="stat-icon">
              <BookOpen size={18} />
            </div>
            <span style={{ fontSize: "var(--font-xs)", color: "var(--primary)", fontWeight: 600 }}>
              {completedSems} Sems
            </span>
          </div>
          <div className="stat-value">
            {totalCredits}
            <small>Credits</small>
          </div>
          <div className="stat-label">Total Credits Earned</div>
        </div>
      </div>

      {/* ACADEMIC STANDING & GUIDANCE */}
      <div
        className="support-card"
        style={{
          marginBottom: "20px",
          padding: "22px 24px",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          background: "var(--surface)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <h3 style={{ fontSize: "var(--font-lg)", fontWeight: 600, color: "var(--text)", margin: 0 }}>
              {academicStanding.headline}
            </h3>
            <p style={{ fontSize: "var(--font-base)", color: "var(--text-secondary)", marginTop: "6px", lineHeight: 1.5 }}>
              {academicStanding.message}
            </p>
          </div>

          <span
            style={{
              fontSize: "var(--font-xs)",
              fontWeight: 700,
              padding: "6px 14px",
              borderRadius: "20px",
              background:
                academicStanding.badgeTone === "warning"
                  ? "rgba(255,209,102,0.15)"
                  : "rgba(6,214,160,0.12)",
              color:
                academicStanding.badgeTone === "warning"
                  ? "#ffd166"
                  : "var(--primary)",
              border:
                academicStanding.badgeTone === "warning"
                  ? "1px solid rgba(255,209,102,0.3)"
                  : "1px solid rgba(6,214,160,0.25)",
            }}
          >
            {academicStanding.badge}
          </span>
        </div>
      </div>

      {/* COMPLETE MARKS CARDS (SEMESTERS 1–4) */}
      {data.historical_semesters && data.historical_semesters.length > 0 && (
        <section
          style={{
            marginBottom: "20px",
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "12px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "18px 22px",
              borderBottom: "1px solid var(--border)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <div>
              <h3 style={{ margin: 0, fontSize: "var(--font-md)", fontWeight: 600, color: "var(--text)" }}>
                Semester Results &amp; Marks Breakdown
              </h3>
              <p style={{ margin: "4px 0 0", fontSize: "var(--font-sm)", color: "var(--text-muted)" }}>
                Official subject-level evaluation from university examination records.
              </p>
            </div>

            <button
              onClick={() => navigate("/profile")}
              style={{
                border: "none",
                background: "transparent",
                color: "var(--primary)",
                cursor: "pointer",
                fontSize: "var(--font-sm)",
                fontWeight: 600,
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              Full Profile
              <ArrowRight size={13} />
            </button>
          </div>

          <div style={{ padding: "16px 20px" }}>
            {data.historical_semesters.map((sem, i) => {
              const isExpanded = expandedSemester === sem.semester;
              const subjs = sem.subject_results || [];

              return (
                <div
                  key={i}
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: "10px",
                    marginBottom: "10px",
                    overflow: "hidden",
                    background: isExpanded ? "var(--surface-soft)" : "transparent",
                  }}
                >
                  {/* Clickable Semester Header */}
                  <div
                    onClick={() => setExpandedSemester((prev) => (prev === sem.semester ? null : sem.semester))}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "14px 18px",
                      cursor: "pointer",
                      userSelect: "none",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                      <FileText size={18} style={{ color: "var(--primary)" }} />
                      <div>
                        <strong style={{ fontSize: "var(--font-base)", color: "var(--text)" }}>
                          Semester {sem.semester}
                        </strong>
                        {sem.exam_name && (
                          <div style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", marginTop: "2px" }}>
                            {typeof sem.exam_name === "string"
                              ? sem.exam_name.replace(/<br\s*\/?>/gi, " — ")
                              : sem.exam_name}
                          </div>
                        )}
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                      <div style={{ fontSize: "var(--font-sm)" }}>
                        <span style={{ color: "var(--text-muted)" }}>SGPA: </span>
                        <strong style={{ color: "var(--text)", fontWeight: 700 }}>
                          {sem.sgpa !== null && sem.sgpa !== undefined ? Number(sem.sgpa).toFixed(2) : "—"}
                        </strong>
                      </div>

                      {sem.cgpa !== null && sem.cgpa !== undefined && (
                        <div style={{ fontSize: "var(--font-sm)" }}>
                          <span style={{ color: "var(--text-muted)" }}>CGPA: </span>
                          <strong style={{ color: "var(--primary)", fontWeight: 700 }}>
                            {Number(sem.cgpa).toFixed(2)}
                          </strong>
                        </div>
                      )}

                      <span
                        style={{
                          fontSize: "var(--font-xs)",
                          fontWeight: 700,
                          padding: "3px 10px",
                          borderRadius: "6px",
                          background: sem.result?.toLowerCase().includes("pass")
                            ? "rgba(6,214,160,0.12)"
                            : "rgba(231,111,111,0.12)",
                          color: sem.result?.toLowerCase().includes("pass")
                            ? "var(--primary)"
                            : "var(--danger)",
                        }}
                      >
                        {sem.result || "PASS"}
                      </span>

                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                  </div>

                  {/* Expanded Subject-Level Marks Card Table */}
                  {isExpanded && (
                    <div style={{ padding: "16px 18px", borderTop: "1px solid var(--border)", background: "var(--surface)" }}>
                      {subjs.length > 0 ? (
                        <div style={{ overflowX: "auto" }}>
                          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "var(--font-sm)" }}>
                            <thead>
                              <tr
                                style={{
                                  borderBottom: "1px solid var(--border)",
                                  color: "var(--text-muted)",
                                  fontSize: "var(--font-xs)",
                                  fontWeight: 600,
                                }}
                              >
                                <th style={{ textAlign: "left", padding: "8px 10px" }}>COURSE CODE</th>
                                <th style={{ textAlign: "left", padding: "8px 10px" }}>SUBJECT TITLE</th>
                                <th style={{ textAlign: "center", padding: "8px 10px" }}>IA</th>
                                <th style={{ textAlign: "center", padding: "8px 10px" }}>SEE</th>
                                <th style={{ textAlign: "center", padding: "8px 10px" }}>TOTAL</th>
                                <th style={{ textAlign: "center", padding: "8px 10px" }}>GRADE</th>
                                <th style={{ textAlign: "center", padding: "8px 10px" }}>GRADE POINT</th>
                                <th style={{ textAlign: "center", padding: "8px 10px" }}>CREDITS</th>
                                <th style={{ textAlign: "right", padding: "8px 10px" }}>RESULT</th>
                              </tr>
                            </thead>
                            <tbody>
                              {subjs.map((sub, sIdx) => (
                                <tr
                                  key={sIdx}
                                  style={{
                                    borderBottom:
                                      sIdx < subjs.length - 1 ? "1px solid var(--border)" : "none",
                                  }}
                                >
                                  <td style={{ padding: "10px", fontWeight: 600, color: "var(--primary)" }}>
                                    {sub.subject_code || "—"}
                                  </td>
                                  <td style={{ padding: "10px", fontWeight: 500 }}>
                                    {sub.subject_name || "—"}
                                  </td>
                                  <td style={{ padding: "10px", textAlign: "center", color: "var(--text-muted)" }}>
                                    {sub.internal_marks ?? "—"}
                                  </td>
                                  <td style={{ padding: "10px", textAlign: "center", color: "var(--text-muted)" }}>
                                    {sub.external_marks ?? "—"}
                                  </td>
                                  <td style={{ padding: "10px", textAlign: "center", fontWeight: 700 }}>
                                    {sub.marks_obtained ?? "—"}
                                    {sub.max_marks ? ` / ${sub.max_marks}` : ""}
                                  </td>
                                  <td style={{ padding: "10px", textAlign: "center", fontWeight: 700 }}>
                                    {sub.grade || "—"}
                                  </td>
                                  <td style={{ padding: "10px", textAlign: "center" }}>
                                    {sub.grade_point ?? "—"}
                                  </td>
                                  <td style={{ padding: "10px", textAlign: "center" }}>
                                    {sub.credits ?? "—"}
                                  </td>
                                  <td
                                    style={{
                                      padding: "10px",
                                      textAlign: "right",
                                      fontWeight: 600,
                                      color:
                                        sub.result?.toLowerCase().includes("fail") || sub.grade === "F"
                                          ? "var(--danger)"
                                          : "var(--primary)",
                                    }}
                                  >
                                    {sub.result || (sub.grade === "F" ? "FAIL" : "PASS")}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <div style={{ color: "var(--text-muted)", fontSize: "var(--font-sm)", padding: "10px 0" }}>
                          Marks card details not available for this semester.
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* QUICK ACTIONS */}
      <div className="dashboard-panel">
        <div className="panel-header">
          <div>
            <h3 style={{ margin: 0, fontSize: "var(--font-md)", fontWeight: 600 }}>Quick Actions</h3>
          </div>
        </div>

        <div className="quick-actions">
          <button onClick={() => navigate("/coach")}>
            <div className="quick-action-icon">
              <Sparkles size={18} />
            </div>
            <div>
              <strong>AI Academic Coach</strong>
              <span>Get personalized study strategies</span>
            </div>
            <ArrowRight size={14} />
          </button>

          <button onClick={() => navigate("/goals")}>
            <div className="quick-action-icon">
              <Target size={18} />
            </div>
            <div>
              <strong>Academic Goals</strong>
              <span>Track milestone completion</span>
            </div>
            <ArrowRight size={14} />
          </button>

          <button onClick={() => navigate("/profile")}>
            <div className="quick-action-icon">
              <FileText size={18} />
            </div>
            <div>
              <strong>Academic Records</strong>
              <span>Review detailed semester grades</span>
            </div>
            <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
