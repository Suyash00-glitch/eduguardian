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
  FileText,
  Minus,
  ShieldCheck,
  ShieldAlert,
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

  const identity = data?.identity || {};
  const histPerf = data?.historical_academic_performance || {};
  const studentName = identity.name || user?.name || user?.full_name || "Student";
  const studentUSN = identity.usn || user?.usn;

  // Attendance metrics
  const attAvailable = data.attendance?.status === "available" && data.attendance.value !== null;
  const attValue = data.attendance?.value !== undefined ? Number(data.attendance.value) : null;

  const cgpa = histPerf.cgpa !== null && histPerf.cgpa !== undefined ? Number(histPerf.cgpa) : null;
  const sgpa = histPerf.latest_sgpa !== null && histPerf.latest_sgpa !== undefined ? Number(histPerf.latest_sgpa) : null;
  const arrearsCount = Number(histPerf.arrears_count || 0);
  const completedSems = histPerf.completed_semesters || (data.historical_semesters?.length || 0);
  const totalCredits = histPerf.total_credits_earned || 0;

  // Real-time Early Dropout / Detention Risk Calculation
  let riskLevel = "LOW";
  let riskColor = "var(--primary)";
  let riskBg = "rgba(6,214,160,0.12)";
  let riskDescription = "Good standing. Keep maintaining regular attendance and exam performance.";

  if (arrearsCount >= 3 || (attAvailable && attValue !== null && attValue < 65)) {
    riskLevel = "CRITICAL";
    riskColor = "var(--danger, #e76f6f)";
    riskBg = "rgba(231,111,111,0.15)";
    riskDescription = "High risk of academic probation or exam detainment due to backlogs / low attendance.";
  } else if (arrearsCount > 0 || (attAvailable && attValue !== null && attValue < 75) || (cgpa && cgpa < 6.0)) {
    riskLevel = "MODERATE";
    riskColor = "#ffd166";
    riskBg = "rgba(255,209,102,0.15)";
    riskDescription = "Attendance or backlog warnings detected. Review subjects falling below 75%.";
  }

  const academicStanding = deriveAcademicStanding(histPerf, data.academic_guidance);

  return (
    <div className="dashboard-page">
      {/* HEADER */}
      <div className="dashboard-welcome" style={{ marginBottom: "20px" }}>
        <div>
          <span className="dashboard-eyebrow">ACADEMIC OVERVIEW</span>
          <h2>Welcome back, {studentName}.</h2>
          <p style={{ margin: "4px 0 0", fontSize: "13px", color: "var(--text-muted)" }}>
            Academic status and early warning monitor (USN: {studentUSN || "—"}).
          </p>
        </div>
      </div>

      {/* TOP KPI GRID */}
      <div className="dashboard-stats" style={{ marginBottom: "20px" }}>
        {/* Card 1: Risk Status */}
        <div className="dashboard-stat-card">
          <div className="stat-card-top">
            <div className="stat-icon">
              {riskLevel === "LOW" ? <ShieldCheck size={17} /> : <ShieldAlert size={17} />}
            </div>
            <span
              style={{
                fontSize: "11px",
                fontWeight: 800,
                padding: "2px 8px",
                borderRadius: "12px",
                background: riskBg,
                color: riskColor,
              }}
            >
              {riskLevel} RISK
            </span>
          </div>
          <div className="stat-value" style={{ color: riskColor }}>
            {riskLevel === "LOW" ? "Safe Standing" : riskLevel === "MODERATE" ? "Monitor Closely" : "Action Required"}
          </div>
          <div className="stat-label">Academic Standing &amp; Risk</div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "6px", lineHeight: "1.4" }}>
            {riskDescription}
          </div>
        </div>

        {/* Card 2: Current Attendance */}
        <div className="dashboard-stat-card">
          <div className="stat-card-top">
            <div className="stat-icon">
              <Activity size={17} />
            </div>
            <span
              style={{
                fontSize: "11px",
                fontWeight: 700,
                padding: "2px 8px",
                borderRadius: "12px",
                background: attAvailable ? (attValue >= 75 ? "rgba(6,214,160,0.12)" : "rgba(231,111,111,0.15)") : "rgba(255,209,102,0.12)",
                color: attAvailable ? (attValue >= 75 ? "var(--primary)" : "var(--danger, #e76f6f)") : "#ffd166",
              }}
            >
              {attAvailable ? (attValue >= 75 ? "On Track (≥75%)" : "Shortage (<75%)") : "Pending"}
            </span>
          </div>
          <div className="stat-value">
            {attAvailable ? `${attValue}%` : "Pending"}
          </div>
          <div className="stat-label">Current Semester Attendance</div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "6px", lineHeight: "1.4" }}>
            {attAvailable
              ? `${data.attendance.classes_attended || 0} of ${data.attendance.classes_held || 0} classes attended (Threshold: 75%)`
              : "Attendance records are pending publication."}
          </div>
        </div>

        {/* Card 3: Cumulative CGPA */}
        <div className="dashboard-stat-card">
          <div className="stat-card-top">
            <div className="stat-icon">
              <Award size={17} />
            </div>
            <span style={{ fontSize: "11px", fontWeight: 700, padding: "2px 8px", borderRadius: "12px", background: "rgba(6,214,160,0.12)", color: "var(--primary)" }}>
              {academicStanding.badge || "CGPA"}
            </span>
          </div>
          <div className="stat-value">
            {cgpa ? cgpa.toFixed(2) : "—"}
          </div>
          <div className="stat-label">Cumulative CGPA</div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "6px", lineHeight: "1.4" }}>
            {completedSems > 0 ? `Evaluated across ${completedSems} completed semesters (${totalCredits} credits)` : "Official examination standings"}
          </div>
        </div>

        {/* Card 4: Latest SGPA */}
        <div className="dashboard-stat-card">
          <div className="stat-card-top">
            <div className="stat-icon">
              <TrendingUp size={17} />
            </div>
            <span
              style={{
                fontSize: "11px",
                fontWeight: 700,
                padding: "2px 8px",
                borderRadius: "12px",
                background: arrearsCount === 0 ? "rgba(6,214,160,0.12)" : "rgba(231,111,111,0.15)",
                color: arrearsCount === 0 ? "var(--primary)" : "var(--danger, #e76f6f)",
              }}
            >
              {arrearsCount === 0 ? "0 Backlogs" : `${arrearsCount} Backlog${arrearsCount > 1 ? "s" : ""}`}
            </span>
          </div>
          <div className="stat-value">
            {sgpa ? sgpa.toFixed(2) : "—"}
          </div>
          <div className="stat-label">Latest SGPA {completedSems > 0 ? `(Sem ${completedSems})` : ""}</div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "6px", lineHeight: "1.4" }}>
            {arrearsCount === 0 ? "Clear academic record with zero pending arrears." : `${arrearsCount} uncleared backlog subject(s).`}
          </div>
        </div>
      </div>

      {/* STRATEGY & VELOCITY SECTION */}
      <div className="dashboard-middle" style={{ marginBottom: "24px" }}>
        {/* Left: Strategy Summary */}
        <div className="support-card" style={{ flex: 1.2, padding: "20px 22px" }}>
          <div className="section-heading" style={{ marginBottom: "14px" }}>
            <div>
              <span className="section-eyebrow">ACADEMIC STATUS &amp; STRATEGY</span>
              <h3 style={{ margin: "4px 0 0", fontSize: "16px" }}>{academicStanding.headline || "Academic Trajectory"}</h3>
            </div>
            <span
              style={{
                fontSize: "11px",
                fontWeight: 800,
                padding: "4px 10px",
                borderRadius: "12px",
                background: academicStanding.badgeTone === "warning" ? "rgba(255,209,102,0.15)" : academicStanding.badgeTone === "danger" ? "rgba(231,111,111,0.15)" : "rgba(6,214,160,0.12)",
                color: academicStanding.badgeTone === "warning" ? "#ffd166" : academicStanding.badgeTone === "danger" ? "var(--danger, #e76f6f)" : "var(--primary)",
                border: academicStanding.badgeTone === "warning" ? "1px solid rgba(255,209,102,0.3)" : academicStanding.badgeTone === "danger" ? "1px solid rgba(231,111,111,0.3)" : "1px solid rgba(6,214,160,0.25)",
              }}
            >
              {academicStanding.badge || "ACTIVE"}
            </span>
          </div>

          <p style={{ fontSize: "13px", color: "var(--text)", margin: 0, lineHeight: "1.6", fontWeight: 500 }}>
            {academicStanding.message}
          </p>
        </div>

        {/* Right: Academic Velocity */}
        <div className="recovery-card" style={{ flex: 1, padding: "20px 22px" }}>
          <div className="section-heading" style={{ marginBottom: "14px" }}>
            <div>
              <span className="section-eyebrow">ACADEMIC VELOCITY</span>
              <h3 style={{ margin: "4px 0 0", fontSize: "16px" }}>Performance Outlook</h3>
            </div>
            <Sparkles size={18} style={{ color: "var(--primary)" }} />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "12px 16px",
                borderRadius: "10px",
                background: "rgba(255,255,255,0.03)",
                border: "1px solid var(--border)",
              }}
            >
              <div>
                <span style={{ fontSize: "11px", color: "var(--text-muted)", display: "block" }}>
                  MOMENTUM
                </span>
                <strong
                  style={{
                    fontSize: "16px",
                    fontWeight: 800,
                    color: cgpa && cgpa >= 8.5 ? "var(--primary)" : "#ffd166",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                    marginTop: "2px",
                  }}
                >
                  <TrendingUp size={16} />
                  {cgpa && cgpa >= 8.5 ? "Distinction Pace" : "Stable Progress"}
                </strong>
              </div>

              <div style={{ textAlign: "right" }}>
                <span style={{ fontSize: "11px", color: "var(--text-muted)", display: "block" }}>
                  TARGET RETENTION
                </span>
                <strong style={{ fontSize: "14px", color: "var(--text)" }}>
                  {cgpa ? `≥ ${(cgpa - 0.2).toFixed(1)} SGPA` : "—"}
                </strong>
              </div>
            </div>

           
          </div>
        </div>
      </div>

      {/* SEMESTER EXAMINATION RECORDS & MARKS CARDS */}
      {data.historical_semesters && data.historical_semesters.length > 0 && (
        <section
          className="profile-card"
          style={{
            background: "rgba(255,255,255,0.02)",
            border: "1px solid var(--border)",
            borderRadius: "12px",
            overflow: "hidden",
            marginBottom: "24px",
          }}
        >
          <div
            style={{
              padding: "16px 20px",
              borderBottom: "1px solid var(--border)",
            }}
          >
            <span className="dashboard-eyebrow">ACADEMIC RECORDS</span>
            <h3 style={{ margin: "4px 0 0", fontSize: "16px", color: "var(--text)" }}>
              Marks Card &amp; Semester Results
            </h3>
          </div>

          <div style={{ padding: "14px 18px" }}>
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
                    background: isExpanded ? "rgba(255,255,255,0.02)" : "transparent",
                  }}
                >
                  <div
                    onClick={() => setExpandedSemester((prev) => (prev === sem.semester ? null : sem.semester))}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "12px 16px",
                      cursor: "pointer",
                      background: "rgba(255,255,255,0.03)",
                      userSelect: "none",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <FileText size={16} style={{ color: "var(--primary)" }} />
                      <div>
                        <strong style={{ fontSize: "14px", color: "var(--text)" }}>
                          Semester {sem.semester}
                        </strong>
                        {sem.exam_name && (
                          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                            {typeof sem.exam_name === "string"
                              ? sem.exam_name.replace(/<br\s*\/?>/gi, " — ")
                              : sem.exam_name}
                          </div>
                        )}
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                      <div>
                        <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>SGPA: </span>
                        <strong style={{ fontSize: "13px", color: "var(--text)" }}>
                          {sem.sgpa !== null && sem.sgpa !== undefined ? Number(sem.sgpa).toFixed(2) : "—"}
                        </strong>
                      </div>

                      {sem.cgpa !== null && sem.cgpa !== undefined && (
                        <div>
                          <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>CGPA: </span>
                          <strong style={{ fontSize: "13px", color: "var(--primary)" }}>
                            {Number(sem.cgpa).toFixed(2)}
                          </strong>
                        </div>
                      )}

                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 700,
                          padding: "2px 8px",
                          borderRadius: "6px",
                          background: sem.result?.toLowerCase().includes("pass")
                            ? "rgba(6,214,160,0.12)"
                            : "rgba(231,111,111,0.12)",
                          color: sem.result?.toLowerCase().includes("pass")
                            ? "var(--success, #06d6a0)"
                            : "var(--danger, #e76f6f)",
                        }}
                      >
                        {sem.result || "PASS"}
                      </span>

                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                  </div>

                  {isExpanded && (
                    <div style={{ padding: "14px 16px", borderTop: "1px solid var(--border)" }}>
                      {subjs.length > 0 ? (
                        <div style={{ overflowX: "auto" }}>
                          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                            <thead>
                              <tr
                                style={{
                                  borderBottom: "1px solid var(--border)",
                                  color: "var(--text-muted)",
                                  fontSize: "11px",
                                }}
                              >
                                <th style={{ textAlign: "left", padding: "6px 8px" }}>CODE</th>
                                <th style={{ textAlign: "left", padding: "6px 8px" }}>SUBJECT</th>
                                <th style={{ textAlign: "center", padding: "6px 8px" }}>IA</th>
                                <th style={{ textAlign: "center", padding: "6px 8px" }}>SEE</th>
                                <th style={{ textAlign: "center", padding: "6px 8px" }}>TOTAL</th>
                                <th style={{ textAlign: "center", padding: "6px 8px" }}>GRADE</th>
                                <th style={{ textAlign: "center", padding: "6px 8px" }}>GP</th>
                                <th style={{ textAlign: "center", padding: "6px 8px" }}>CREDITS</th>
                                <th style={{ textAlign: "right", padding: "6px 8px" }}>RESULT</th>
                              </tr>
                            </thead>
                            <tbody>
                              {subjs.map((sub, sIdx) => (
                                <tr
                                  key={sIdx}
                                  style={{
                                    borderBottom:
                                      sIdx < subjs.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none",
                                  }}
                                >
                                  <td style={{ padding: "8px", fontWeight: 600, color: "var(--primary)" }}>
                                    {sub.subject_code || "—"}
                                  </td>
                                  <td style={{ padding: "8px", fontWeight: 500 }}>
                                    {sub.subject_name || "—"}
                                  </td>
                                  <td style={{ padding: "8px", textAlign: "center", color: "var(--text-muted)" }}>
                                    {sub.internal_marks ?? "—"}
                                  </td>
                                  <td style={{ padding: "8px", textAlign: "center", color: "var(--text-muted)" }}>
                                    {sub.external_marks ?? "—"}
                                  </td>
                                  <td style={{ padding: "8px", textAlign: "center", fontWeight: 700 }}>
                                    {sub.marks_obtained ?? "—"}
                                    {sub.max_marks ? ` / ${sub.max_marks}` : ""}
                                  </td>
                                  <td style={{ padding: "8px", textAlign: "center", fontWeight: 700 }}>
                                    {sub.grade || "—"}
                                  </td>
                                  <td style={{ padding: "8px", textAlign: "center" }}>
                                    {sub.grade_point ?? "—"}
                                  </td>
                                  <td style={{ padding: "8px", textAlign: "center" }}>
                                    {sub.credits ?? "—"}
                                  </td>
                                  <td
                                    style={{
                                      padding: "8px",
                                      textAlign: "right",
                                      fontWeight: 600,
                                      color:
                                        sub.result?.toLowerCase().includes("fail") || sub.grade === "F"
                                          ? "var(--danger, #e76f6f)"
                                          : "var(--success, #06d6a0)",
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
                        <div style={{ color: "var(--text-muted)", fontSize: "12px", padding: "8px 0" }}>
                          Marks Card details not available for this semester.
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
      <div className="dashboard-bottom">
        <div className="dashboard-panel">
          <div className="panel-header">
            <div>
              <span className="section-eyebrow">INTERVENTIONS &amp; RESOURCES</span>
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
                <span>Personalized study plans &amp; guidance</span>
              </div>
              <ArrowRight size={13} />
            </button>

            <button onClick={() => navigate("/progress")}>
              <div className="quick-action-icon">
                <Activity size={16} />
              </div>
              <div>
                <strong>Detailed Attendance &amp; Progress</strong>
                <span>Subject-wise breakdown &amp; 75% threshold monitor</span>
              </div>
              <ArrowRight size={13} />
            </button>

            <button onClick={() => navigate("/goals")}>
              <div className="quick-action-icon">
                <Target size={16} />
              </div>
              <div>
                <strong>Academic Target Tracker</strong>
                <span>Keep your target SGPA on track</span>
              </div>
              <ArrowRight size={13} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;