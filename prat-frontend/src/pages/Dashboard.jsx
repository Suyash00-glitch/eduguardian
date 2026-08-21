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
  Info,
  Award,
  BookOpen,
  FileText,
  Minus,
  ShieldCheck,
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
  const riskInfo = data?.risk || {};
  const studentName = identity.name || user?.name || user?.full_name || "Student";
  const studentUSN = identity.usn || user?.usn;
  const currentSem = identity.semester || user?.semester || 5;

  // Attendance & Assessment status flags
  const attAvailable = data.attendance?.status === "available" && data.attendance.value !== null;
  const attValue = data.attendance?.value;
  const assessAvailable = data.assessments?.status === "available" && data.assessments.value !== null;
  const assessValue = data.assessments?.value;

  const cgpaDisplay = histPerf.cgpa !== null && histPerf.cgpa !== undefined ? Number(histPerf.cgpa).toFixed(2) : null;
  const sgpaDisplay = histPerf.latest_sgpa !== null && histPerf.latest_sgpa !== undefined ? Number(histPerf.latest_sgpa).toFixed(2) : null;
  const trend = histPerf.sgpa_trend || "stable";
  const completedSems = histPerf.completed_semesters || (data.historical_semesters?.length || 0);

  // Dynamic Academic Standing & Supportive Guidance
  const academicStanding = deriveAcademicStanding(histPerf, data.academic_guidance);

  return (
    <div className="dashboard-page">
      {/* Header */}
      <div className="dashboard-welcome">
        <div>
          <span className="dashboard-eyebrow">ACADEMIC OVERVIEW</span>
          <h2>Good afternoon, {studentName}.</h2>
          <p>
            {isPortal
              ? `Academic status synchronized with University Solutions Student Portal (USN: ${studentUSN || "—"}).`
              : "Here's how your academic journey is looking right now."}
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          {isPortal && (
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                fontSize: "11px",
                fontWeight: 700,
                padding: "5px 12px",
                borderRadius: "20px",
                background: "rgba(6,214,160,0.12)",
                color: "var(--primary)",
                border: "1px solid rgba(6,214,160,0.25)",
              }}
            >
              <CheckCircle2 size={12} />
              University Solutions Portal
            </span>
          )}

          <button
            className="dashboard-action"
            onClick={() => navigate("/profile")}
          >
            View Marks Card
            <ArrowRight size={14} />
          </button>
        </div>
      </div>

      {/* HISTORICAL ACADEMIC PERFORMANCE (AUTHORITATIVE SEMESTERS 1–4) */}
      {(cgpaDisplay || sgpaDisplay) && (
        <section
          className="profile-card"
          style={{
            marginBottom: "20px",
            background: "linear-gradient(135deg, rgba(6,214,160,0.06) 0%, rgba(84,149,255,0.06) 100%)",
            border: "1px solid rgba(6,214,160,0.2)",
          }}
        >
          <div style={{ padding: "18px 22px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "10px", marginBottom: "14px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Award size={16} style={{ color: "var(--primary)" }} />
                <span className="dashboard-eyebrow" style={{ color: "var(--primary)" }}>
                  HISTORICAL ACADEMIC PERFORMANCE
                </span>
              </div>
              <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 600 }}>
                {completedSems > 0 ? `Completed Semesters: 1–${completedSems}` : "Historical Standing"}
              </span>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                gap: "16px",
              }}
            >
              {cgpaDisplay && (
                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 600, letterSpacing: "0.04em" }}>
                    CUMULATIVE CGPA
                  </div>
                  <div style={{ fontSize: "26px", fontWeight: 800, color: "#fff", marginTop: "2px" }}>
                    {cgpaDisplay}
                  </div>
                  <div
                    style={{
                      fontSize: "11px",
                      color:
                        academicStanding.badgeTone === "warning"
                          ? "#ffd166"
                          : academicStanding.badgeTone === "danger"
                          ? "var(--danger, #e76f6f)"
                          : "var(--primary)",
                      fontWeight: 600,
                    }}
                  >
                    {academicStanding.standingLabel}
                  </div>
                </div>
              )}

              {sgpaDisplay && (
                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 600, letterSpacing: "0.04em" }}>
                    LATEST SGPA {completedSems > 0 ? `(SEM ${completedSems})` : ""}
                  </div>
                  <div style={{ fontSize: "26px", fontWeight: 800, color: "#fff", marginTop: "2px" }}>
                    {sgpaDisplay}
                  </div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    Semester examination result
                  </div>
                </div>
              )}

              <div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 600, letterSpacing: "0.04em" }}>
                  PERFORMANCE TRAJECTORY
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    fontSize: "16px",
                    fontWeight: 800,
                    marginTop: "6px",
                    color:
                      trend === "improving"
                        ? "var(--success, #06d6a0)"
                        : trend === "declining"
                        ? "var(--danger, #e76f6f)"
                        : "var(--text)",
                  }}
                >
                  {trend === "improving" && <TrendingUp size={18} />}
                  {trend === "declining" && <TrendingDown size={18} />}
                  {trend === "stable" && <Minus size={18} />}
                  {trend.charAt(0).toUpperCase() + trend.slice(1)}
                </div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                  Semester-over-semester
                </div>
              </div>

              {histPerf.total_credits_earned && (
                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 600, letterSpacing: "0.04em" }}>
                    TOTAL CREDITS
                  </div>
                  <div style={{ fontSize: "26px", fontWeight: 800, color: "#fff", marginTop: "2px" }}>
                    {histPerf.total_credits_earned}
                  </div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    Credits earned to date
                  </div>
                </div>
              )}

              <div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 600, letterSpacing: "0.04em" }}>
                  BACKLOGS / ARREARS
                </div>
                <div style={{ fontSize: "26px", fontWeight: 800, color: histPerf.arrears_count > 0 ? "var(--danger, #e76f6f)" : "var(--success, #06d6a0)", marginTop: "2px" }}>
                  {histPerf.arrears_count ?? 0}
                </div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                  {histPerf.arrears_count > 0 ? "Active backlogs" : "Clear academic record"}
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* CURRENT SEMESTER STATUS CARDS (SEMESTER 5) */}
      <div style={{ marginBottom: "10px" }}>
        <span className="dashboard-eyebrow">
          CURRENT SEMESTER {currentSem ? `(SEMESTER ${currentSem})` : ""}
        </span>
      </div>

      <div className="dashboard-stats">
        {/* Card 1: Attendance */}
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
                background: attAvailable ? "rgba(6,214,160,0.12)" : "rgba(255,209,102,0.12)",
                color: attAvailable ? "var(--primary)" : "#ffd166",
              }}
            >
              {attAvailable ? "Published" : "Pending"}
            </span>
          </div>

          <div className="stat-value">
            {attAvailable ? `${attValue}%` : "Pending"}
          </div>

          <div className="stat-label">Current Semester Attendance</div>

          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "6px", lineHeight: "1.4" }}>
            {attAvailable
              ? `${data.attendance.classes_attended || 0} of ${data.attendance.classes_held || 0} classes attended`
              : "Current semester attendance has not yet been published by faculty."}
          </div>

          {attAvailable && (
            <div className="stat-progress" style={{ marginTop: "8px" }}>
              <span style={{ width: `${attValue}%` }} />
            </div>
          )}
        </div>

        {/* Card 2: Academic Performance (Latest SGPA or Current Assessment) */}
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
                background: assessAvailable ? "rgba(6,214,160,0.12)" : "rgba(84,149,255,0.12)",
                color: assessAvailable ? "var(--primary)" : "#5495ff",
              }}
            >
              {assessAvailable ? "Published" : sgpaDisplay ? `Sem ${completedSems} SGPA` : "Pending"}
            </span>
          </div>

          <div className="stat-value">
            {assessAvailable
              ? `${assessValue}%`
              : sgpaDisplay
              ? sgpaDisplay
              : "Pending"}
          </div>

          <div className="stat-label">
            {assessAvailable
              ? "Current Assessment Score"
              : sgpaDisplay
              ? `Latest SGPA (Semester ${completedSems})`
              : "Academic Performance"}
          </div>

          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "6px", lineHeight: "1.4" }}>
            {assessAvailable
              ? "Current semester internal assessment average."
              : sgpaDisplay
              ? `Cumulative CGPA: ${cgpaDisplay || "—"} across ${completedSems} completed semesters.`
              : "Current semester assessment records have not yet been published."}
          </div>
        </div>

        {/* Card 3: Assignments */}
        <div className="dashboard-stat-card">
          <div className="stat-card-top">
            <div className="stat-icon">
              <ClipboardCheck size={17} />
            </div>

            <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 600 }}>
              Not Tracked
            </span>
          </div>

          <div className="stat-value" style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-muted)" }}>
            Not available
          </div>

          <div className="stat-label">Coursework / Assignments</div>

          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "6px", lineHeight: "1.4" }}>
            Assignment tracking is not integrated into this portal.
          </div>
        </div>

        {/* Card 4: LMS Engagement */}
        <div className="dashboard-stat-card">
          <div className="stat-card-top">
            <div className="stat-icon">
              <Clock3 size={17} />
            </div>

            <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 600 }}>
              Not Tracked
            </span>
          </div>

          <div className="stat-value" style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-muted)" }}>
            Not available
          </div>

          <div className="stat-label">LMS Engagement</div>

          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "6px", lineHeight: "1.4" }}>
            LMS tracking is not integrated into this portal.
          </div>
        </div>
      </div>

      {/* ACADEMIC STATUS & GUIDANCE (STUDENT-FACING) */}
      <div className="dashboard-middle" style={{ marginTop: "24px" }}>
        {/* Card A: Academic Status & Guidance */}
        <div className="support-card" style={{ flex: 1 }}>
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">ACADEMIC STATUS &amp; GUIDANCE</span>
              <h3>{academicStanding.headline}</h3>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: 800,
                  padding: "4px 10px",
                  borderRadius: "12px",
                  background:
                    academicStanding.badgeTone === "warning"
                      ? "rgba(255,209,102,0.15)"
                      : academicStanding.badgeTone === "danger"
                      ? "rgba(231,111,111,0.15)"
                      : "rgba(6,214,160,0.12)",
                  color:
                    academicStanding.badgeTone === "warning"
                      ? "#ffd166"
                      : academicStanding.badgeTone === "danger"
                      ? "var(--danger, #e76f6f)"
                      : "var(--primary)",
                  border:
                    academicStanding.badgeTone === "warning"
                      ? "1px solid rgba(255,209,102,0.3)"
                      : academicStanding.badgeTone === "danger"
                      ? "1px solid rgba(231,111,111,0.3)"
                      : "1px solid rgba(6,214,160,0.25)",
                }}
              >
                {academicStanding.badge}
              </span>
            </div>
          </div>

          <div style={{ padding: "14px 16px", background: "rgba(255,255,255,0.02)", borderRadius: "10px", margin: "12px 0" }}>
            <p style={{ fontSize: "13px", color: "var(--text)", margin: "0 0 8px", lineHeight: "1.5", fontWeight: 500 }}>
              {academicStanding.message}
            </p>

            <div style={{ fontSize: "11px", color: "var(--text-muted)", fontStyle: "italic", borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: "8px", marginTop: "8px" }}>
              Current-semester attendance and assessment records are not yet available from the university portal. Academic overview is evaluated from official semester examination results.
            </div>
          </div>

          <div className="support-footer">
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              Synchronized with University Solutions Portal
            </span>

            <button onClick={() => navigate("/profile")}>
              View Academic Record
              <ArrowRight size={12} />
            </button>
          </div>
        </div>

        {/* Card B: Academic Outlook & Trajectory */}
        <div className="recovery-card" style={{ flex: 1 }}>
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">ACADEMIC TRAJECTORY</span>
              <h3>Progress Outlook</h3>
            </div>

            <Sparkles size={17} className="section-ai-icon" />
          </div>

          <div className="recovery-content">
            <div className="recovery-circle">
              <div>
                <strong style={{ fontSize: "20px" }}>
                  {trend === "improving" ? "↗" : trend === "declining" ? "↘" : "→"}
                </strong>
                <span>{trend.toUpperCase()}</span>
              </div>
            </div>

            <div className="recovery-description">
              <div className="recovery-status">
                {academicStanding.badgeTone === "warning" || academicStanding.badgeTone === "danger" ? (
                  <AlertTriangle size={15} style={{ color: "#ffd166" }} />
                ) : (
                  <CheckCircle2 size={15} style={{ color: "var(--primary)" }} />
                )}
                <strong>{academicStanding.outlookStatus}</strong>
              </div>

              <p style={{ fontSize: "12px", color: "var(--text-muted)", margin: "6px 0 10px", lineHeight: "1.4" }}>
                {academicStanding.outlookMessage}
              </p>

              <button onClick={() => navigate("/profile")}>
                View Marks Card Breakdown
                <ArrowRight size={13} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* COMPLETE MARKS CARDS (SEMESTERS 1–4) */}
      {data.historical_semesters && data.historical_semesters.length > 0 && (
        <section
          className="profile-card"
          style={{
            marginTop: "24px",
            background: "rgba(255,255,255,0.02)",
            border: "1px solid var(--border)",
            borderRadius: "12px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "16px 20px",
              borderBottom: "1px solid var(--border)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <div>
              <span className="dashboard-eyebrow">AUTHORITATIVE ACADEMIC RECORDS</span>
              <h3 style={{ margin: "4px 0 0", fontSize: "16px", color: "var(--text)" }}>
                Marks Card &amp; Semester Results
              </h3>
              <p style={{ margin: "2px 0 0", fontSize: "12px", color: "var(--text-muted)" }}>
                Official subject-level breakdown from University Solutions Student Portal.
              </p>
            </div>

            <button
              onClick={() => navigate("/profile")}
              style={{
                border: "none",
                background: "transparent",
                color: "var(--primary)",
                cursor: "pointer",
                fontSize: "12px",
                fontWeight: 700,
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              View Full Profile Records
              <ArrowRight size={13} />
            </button>
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
                  {/* Clickable Semester Header */}
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

                  {/* Expanded Subject-Level Marks Card Table */}
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
      <div className="dashboard-bottom" style={{ marginTop: "24px" }}>
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

            <button onClick={() => navigate("/profile")}>
              <div className="quick-action-icon">
                <FileText size={16} />
              </div>
              <div>
                <strong>Marks Card & Academic Record</strong>
                <span>Inspect semester results and grades</span>
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
