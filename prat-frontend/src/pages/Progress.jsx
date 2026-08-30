import React, { useCallback, useEffect, useState } from "react";
import {
  Activity,
  GraduationCap,
  Award,
  TrendingUp,
  CheckCircle2,
  Info,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { studentService } from "../services/studentService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import { deriveAcademicStanding } from "../utils/academicStanding";

function Progress() {
  const navigate = useNavigate();
  const [ctx, setCtx] = useState(null);
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadProgress = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const portalCtx = await studentService.getPortalContext();
      setCtx(portalCtx);
      const attData = await studentService.getAttendance();
      setAttendance(attData || []);
    } catch (err) {
      setError(err.message || "Unable to load progress.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProgress();
  }, [loadProgress]);

  if (loading) {
    return <LoadingState message="Loading your academic progress..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Unable to load progress"
        message={error}
        onRetry={loadProgress}
      />
    );
  }

  const isPortal = ctx?.data_source === "student_portal";
  const histPerf = ctx?.historical_academic_performance || {};
  const histSems = ctx?.historical_semesters || [];
  const currentSem = ctx?.identity?.semester || 5;

  const cgpaDisplay = histPerf.cgpa
    ? Number(histPerf.cgpa).toFixed(2)
    : (histSems[0]?.cgpa ? Number(histSems[0].cgpa).toFixed(2) : null);
  const sgpaDisplay = histPerf.latest_sgpa
    ? Number(histPerf.latest_sgpa).toFixed(2)
    : (histSems[0]?.sgpa ? Number(histSems[0].sgpa).toFixed(2) : null);
  const completedSems = histPerf.total_semesters_completed || histSems.length;
  const totalCredits = histPerf.total_credits_earned || (completedSems * 21) || 84;

  const attCalculated = attendance && attendance.length > 0
    ? Math.round(attendance.reduce((sum, a) => sum + Number(a.percentage || 0), 0) / attendance.length)
    : null;
  const effectiveAttValue = (ctx?.attendance?.value !== null && ctx?.attendance?.value !== undefined)
    ? ctx.attendance.value
    : attCalculated;
  const isAttAvailable = (ctx?.attendance?.status === "available" || (attendance && attendance.length > 0)) && effectiveAttValue !== null;

  // Dynamic Academic Standing & Supportive Guidance
  const academicStanding = deriveAcademicStanding(histPerf, ctx?.academic_guidance);

  return (
    <div className="progress-page">
      {/* HEADER */}
      <div className="progress-header" style={{ marginBottom: "24px" }}>
        <div>
          <h1 style={{ fontSize: "var(--font-2xl)", fontWeight: 700, margin: 0, color: "var(--text)" }}>
            Academic Progress
          </h1>
          <p style={{ margin: "6px 0 0", fontSize: "var(--font-base)", color: "var(--text-secondary)" }}>
            {isPortal
              ? "Official academic and examination performance synchronized with University Solutions Student Portal."
              : "Comprehensive overview of cumulative grades, semester results, and subject attendance."}
          </p>
        </div>

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
      </div>

      {/* SUMMARY STATS */}
      <div className="progress-summary-grid" style={{ marginBottom: "24px" }}>
        <ProgressCard
          icon={Award}
          value={cgpaDisplay ? cgpaDisplay : "—"}
          label="Cumulative CGPA"
          sub={academicStanding.standingLabel}
        />

        <ProgressCard
          icon={TrendingUp}
          value={sgpaDisplay ? sgpaDisplay : "—"}
          label={`Latest SGPA (Sem ${completedSems || 4})`}
          sub="Semester examination"
        />

        <ProgressCard
          icon={GraduationCap}
          value={completedSems ? `${completedSems} Sems` : "—"}
          label="Completed Semesters"
          sub={`${totalCredits} credits earned`}
        />

        <ProgressCard
          icon={Activity}
          value={isAttAvailable ? `${effectiveAttValue}%` : "Pending"}
          label="Current Attendance"
          sub={isAttAvailable ? "Published" : "Pending faculty publication"}
        />
      </div>

      {/* 1. CURRENT SEMESTER ATTENDANCE */}
      <section className="progress-section" style={{ marginBottom: "24px" }}>
        <div className="progress-section-heading" style={{ marginBottom: "16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h2 style={{ fontSize: "var(--font-lg)", fontWeight: 600, margin: 0, color: "var(--text)" }}>
              Subject Attendance {currentSem ? `(Semester ${currentSem})` : ""}
            </h2>
            <p style={{ margin: "4px 0 0", fontSize: "var(--font-sm)", color: "var(--text-muted)" }}>
              Minimum 75% attendance required for semester examination eligibility.
            </p>
          </div>
          <div
            style={{
              fontSize: "var(--font-xs)",
              fontWeight: 600,
              padding: "4px 10px",
              borderRadius: "6px",
              background: "var(--surface-soft)",
              color: "var(--text-secondary)",
              border: "1px solid var(--border)",
            }}
          >
            Threshold: 75%
          </div>
        </div>

        {isAttAvailable && attendance.length > 0 ? (
          <div className="attendance-table-container" style={{ border: "1px solid var(--border)", borderRadius: "12px", overflow: "hidden", background: "var(--surface)" }}>
            <div className="attendance-table">
              <div
                className="attendance-table-head"
                style={{
                  display: "grid",
                  gridTemplateColumns: "2fr 1fr 1fr 1.5fr 1fr",
                  padding: "12px 18px",
                  fontSize: "var(--font-xs)",
                  fontWeight: 600,
                  color: "var(--text-muted)",
                  borderBottom: "1px solid var(--border)",
                  background: "var(--surface-soft)",
                }}
              >
                <span>SUBJECT</span>
                <span style={{ textAlign: "center" }}>HELD</span>
                <span style={{ textAlign: "center" }}>ATTENDED</span>
                <span style={{ textAlign: "center" }}>ATTENDANCE</span>
                <span style={{ textAlign: "right" }}>STATUS</span>
              </div>

              {attendance.map((item, idx) => {
                const subCode = item.subjectCode || item.subject_code || item.fsubcode || `SUB-${idx + 1}`;
                const subName = item.subjectName || item.subject_name || item.fsubname || subCode;
                const held = Number(item.classesHeld ?? item.conducted ?? item.classes_held ?? item.held ?? 0);
                const attended = Number(item.classesAttended ?? item.attended ?? item.classes_attended ?? item.present ?? 0);
                const percentage = Number(item.percentage ?? (held > 0 ? (attended / held * 100) : 100));
                const good = percentage >= 75;

                return (
                  <div
                    className="attendance-row"
                    key={subCode + idx}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "2fr 1fr 1fr 1.5fr 1fr",
                      padding: "14px 18px",
                      alignItems: "center",
                      borderBottom: "1px solid var(--border)",
                      fontSize: "var(--font-sm)",
                    }}
                  >
                    <div className="subject-cell">
                      <strong style={{ color: "var(--text)", display: "block" }}>{subCode}</strong>
                      <span style={{ color: "var(--text-muted)", fontSize: "var(--font-xs)" }}>{subName}</span>
                    </div>

                    <span style={{ textAlign: "center", color: "var(--text-secondary)" }}>{held}</span>
                    <span style={{ textAlign: "center", color: "var(--text-secondary)" }}>{attended}</span>

                    <div style={{ padding: "0 10px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--font-xs)", fontWeight: 600, marginBottom: "4px" }}>
                        <span>{percentage.toFixed(1)}%</span>
                      </div>
                      <div className="progress-bar-track" style={{ height: "6px", background: "var(--surface-soft)", borderRadius: "3px", overflow: "hidden" }}>
                        <div
                          className="progress-bar-fill"
                          style={{
                            width: `${Math.min(100, Math.max(0, percentage))}%`,
                            height: "100%",
                            background: good ? "var(--primary)" : "var(--danger)",
                            borderRadius: "3px",
                          }}
                        />
                      </div>
                    </div>

                    <span style={{ textAlign: "right" }}>
                      <span
                        className={`status-badge ${good ? "good" : "danger"}`}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                          fontSize: "var(--font-xs)",
                          fontWeight: 600,
                          padding: "4px 8px",
                          borderRadius: "6px",
                          background: good ? "rgba(6,214,160,0.12)" : "rgba(239,71,111,0.12)",
                          color: good ? "var(--primary)" : "var(--danger)",
                        }}
                      >
                        {good ? "On Track" : "Low"}
                      </span>
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div
            style={{
              padding: "20px 24px",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "12px",
              display: "flex",
              alignItems: "center",
              gap: "14px",
            }}
          >
            <Info size={20} style={{ color: "var(--primary)", flexShrink: 0 }} />
            <div>
              <strong style={{ fontSize: "var(--font-base)", color: "var(--text)" }}>
                Current Semester Attendance Pending Publication
              </strong>
              <p style={{ margin: "4px 0 0", fontSize: "var(--font-sm)", color: "var(--text-secondary)" }}>
                Faculty members have not yet uploaded attendance records for the current semester. Live tracking will activate automatically once published.
              </p>
            </div>
          </div>
        )}
      </section>

      {/* 2. HISTORICAL EXAMINATION PERFORMANCE & MARKS CARDS */}
      {histSems.length > 0 && (
        <section className="progress-section">
          <div className="progress-section-heading" style={{ marginBottom: "16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h2 style={{ fontSize: "var(--font-lg)", fontWeight: 600, margin: 0, color: "var(--text)" }}>
                Completed Semester Examination Records
              </h2>
              <p style={{ margin: "4px 0 0", fontSize: "var(--font-sm)", color: "var(--text-muted)" }}>
                Cumulative academic performance by examination session.
              </p>
            </div>
            <button
              style={{
                border: "none",
                background: "transparent",
                color: "var(--primary)",
                cursor: "pointer",
                fontSize: "var(--font-sm)",
                fontWeight: 600,
              }}
              onClick={() => navigate("/profile")}
            >
              View Full Marks Cards →
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px" }}>
            {histSems.map((sem, idx) => {
              const isSummer = sem.is_summer || (sem.exam_name || "").toLowerCase().includes("summer") || (sem.semester || "").toLowerCase().includes("summer");
              const title = isSummer
                ? (sem.short_title || sem.display_label || "Summer Semester")
                : (sem.semester_number ? `Semester ${sem.semester_number}` : sem.display_label || sem.semester || `Semester ${idx + 1}`);

              return (
                <div
                  key={idx}
                  style={{
                    padding: "18px 20px",
                    borderRadius: "12px",
                    background: "var(--surface)",
                    border: "1px solid var(--border)",
                    transition: "transform 0.2s ease, border-color 0.2s ease",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px", gap: "8px" }}>
                    <strong style={{ fontSize: "var(--font-base)", color: "var(--text)" }}>
                      {title}
                    </strong>
                    <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                      {isSummer && (
                        <span
                          style={{
                            fontSize: "10px",
                            fontWeight: 700,
                            padding: "2px 6px",
                            borderRadius: "4px",
                            background: "rgba(56, 189, 248, 0.15)",
                            color: "#38bdf8",
                            border: "1px solid rgba(56, 189, 248, 0.3)",
                            whiteSpace: "nowrap",
                          }}
                        >
                          Summer Sem
                        </span>
                      )}
                      <span
                        style={{
                          fontSize: "var(--font-xs)",
                          fontWeight: 700,
                          padding: "3px 8px",
                          borderRadius: "6px",
                          background: sem.result_class?.toLowerCase().includes("pass") || sem.result?.toLowerCase().includes("pass")
                            ? "rgba(6,214,160,0.12)"
                            : "rgba(231,111,111,0.12)",
                          color: sem.result_class?.toLowerCase().includes("pass") || sem.result?.toLowerCase().includes("pass")
                            ? "var(--primary)"
                            : "var(--danger)",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {sem.result_class || sem.result || "PASS"}
                      </span>
                    </div>
                  </div>

                  <div style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", marginBottom: "12px" }}>
                    Exam: {sem.exam_date || sem.exam_name ? (typeof sem.exam_name === "string" ? sem.exam_name.replace(/<br\s*\/?>/gi, " — ") : sem.exam_date) : "Completed"}
                  </div>

                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderTop: "1px solid var(--border)", paddingTop: "10px" }}>
                    <div>
                      <span style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", display: "block" }}>SGPA</span>
                      <strong style={{ fontSize: "var(--font-md)", color: "var(--text)", fontWeight: 700 }}>
                        {sem.sgpa ? Number(sem.sgpa).toFixed(2) : "—"}
                      </strong>
                    </div>
                    <div>
                      <span style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", display: "block" }}>CGPA</span>
                      <strong style={{ fontSize: "var(--font-md)", color: "var(--primary)", fontWeight: 700 }}>
                        {sem.cgpa ? Number(sem.cgpa).toFixed(2) : "—"}
                      </strong>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}

function ProgressCard({ icon: Icon, value, label, sub }) {
  return (
    <div
      className="progress-stat-card"
      style={{
        padding: "18px 20px",
        borderRadius: "12px",
        background: "var(--surface)",
        border: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        gap: "14px",
      }}
    >
      <div
        className="progress-stat-icon"
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
        <Icon size={20} />
      </div>

      <div>
        <strong style={{ fontSize: "var(--font-stat)", fontWeight: 700, color: "var(--text)", display: "block", lineHeight: 1.1 }}>
          {value}
        </strong>
        <span style={{ fontSize: "var(--font-sm)", color: "var(--text-secondary)", marginTop: "4px", display: "block" }}>
          {label}
        </span>
        {sub && (
          <small style={{ display: "block", fontSize: "var(--font-xs)", color: "var(--text-muted)", marginTop: "2px" }}>
            {sub}
          </small>
        )}
      </div>
    </div>
  );
}

export default Progress;