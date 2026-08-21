import React, { useCallback, useEffect, useState } from "react";
import {
  Activity,
  ClipboardCheck,
  GraduationCap,
  Award,
  BookOpen,
  TrendingUp,
  CheckCircle2,
  Clock3,
  Info,
  Calendar,
  Layers,
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

  const cgpaDisplay = histPerf.cgpa ? Number(histPerf.cgpa).toFixed(2) : null;
  const sgpaDisplay = histPerf.latest_sgpa ? Number(histPerf.latest_sgpa).toFixed(2) : null;
  const trend = histPerf.sgpa_trend || "stable";
  const completedSems = histPerf.total_semesters_completed || histSems.length;
  const totalCredits = histPerf.total_credits_earned || 84;

  const attAvailable = ctx?.attendance?.status === "available" && ctx.attendance.value !== null;
  const attValue = ctx?.attendance?.value;

  // Dynamic Academic Standing & Supportive Guidance
  const academicStanding = deriveAcademicStanding(histPerf, ctx?.academic_guidance);

  return (
    <div className="progress-page">
      {/* HEADER */}
      <div className="progress-header">
        <div>
          <span className="progress-eyebrow">ACADEMIC PERFORMANCE</span>
          <h1>My Academic Progress</h1>
          <p>
            {isPortal
              ? "Official academic records synchronized with University Solutions Student Portal."
              : "A comprehensive overview of your attendance, assessments, subject scores, and learning progress."}
          </p>
        </div>

        {isPortal && (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
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
      </div>

      {/* SUMMARY STATS (AUTHORITATIVE HISTORICAL PERFORMANCE) */}
      <div className="progress-summary-grid">
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
          value={attAvailable ? `${attValue}%` : "Pending"}
          label="Current Attendance"
          sub={attAvailable ? "Published" : "Pending faculty upload"}
        />
      </div>

      {/* 1. CURRENT SEMESTER (SEMESTER 5) ATTENDANCE */}
      <section className="progress-section">
        <div className="progress-section-heading">
          <div>
            <span>CURRENT SEMESTER</span>
            <h2>Subject-wise attendance {currentSem ? `(Semester ${currentSem})` : ""}</h2>
          </div>
          <div className="target-badge">Threshold: 75%</div>
        </div>

        {attAvailable && attendance.length > 0 ? (
          <div className="attendance-table-container">
            <div className="attendance-table">
              <div className="attendance-table-head">
                <span>SUBJECT</span>
                <span>HELD</span>
                <span>ATTENDED</span>
                <span>ATTENDANCE</span>
                <span>STATUS</span>
              </div>

              {attendance.map((item) => {
                const percentage = Number(item.percentage || 0);
                const good = percentage >= 75;

                return (
                  <div className="attendance-row" key={item.subjectCode}>
                    <div className="subject-cell">
                      <strong>{item.subjectCode}</strong>
                      <span>{item.subjectName}</span>
                    </div>

                    <span className="count-cell">{item.classesHeld}</span>
                    <span className="count-cell">{item.classesAttended}</span>

                    <div className="attendance-progress-cell">
                      <div className="attendance-percentage">
                        {percentage.toFixed(1)}%
                      </div>
                      <div className="mini-progress">
                        <div
                          style={{
                            width: `${Math.min(percentage, 100)}%`,
                            background: good ? "var(--primary)" : "#e85c47",
                          }}
                        />
                      </div>
                    </div>

                    <span className={`attendance-status ${good ? "good" : "warning"}`}>
                      {good ? "On track" : "Attention"}
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
              background: "rgba(255,255,255,0.02)",
              border: "1px solid var(--border)",
              borderRadius: "12px",
              display: "flex",
              alignItems: "center",
              gap: "14px",
            }}
          >
            <Info size={20} style={{ color: "var(--primary)", flexShrink: 0 }} />
            <div>
              <strong style={{ fontSize: "14px", color: "var(--text)" }}>
                Current Semester Attendance Pending
              </strong>
              <p style={{ margin: "3px 0 0", fontSize: "12px", color: "var(--text-muted)" }}>
                Faculty members have not yet uploaded attendance records for the current semester. Live tracking will activate automatically once published.
              </p>
            </div>
          </div>
        )}
      </section>

      {/* 2. HISTORICAL EXAMINATION PERFORMANCE & MARKS CARDS */}
      {histSems.length > 0 && (
        <section className="progress-section">
          <div className="progress-section-heading">
            <div>
              <span>HISTORICAL STANDING</span>
              <h2>Completed Semester Examination Records</h2>
            </div>
            <button
              style={{
                border: "none",
                background: "transparent",
                color: "var(--primary)",
                cursor: "pointer",
                fontSize: "12px",
                fontWeight: 700,
              }}
              onClick={() => navigate("/profile")}
            >
              View Full Marks Cards →
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "14px" }}>
            {histSems.map((sem, idx) => (
              <div
                key={idx}
                style={{
                  padding: "16px 18px",
                  borderRadius: "12px",
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid var(--border)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
                  <strong style={{ fontSize: "13px", color: "var(--text)" }}>
                    Semester {sem.semester_number || idx + 1}
                  </strong>
                  <span
                    style={{
                      fontSize: "11px",
                      fontWeight: 700,
                      padding: "2px 8px",
                      borderRadius: "6px",
                      background: "rgba(6,214,160,0.12)",
                      color: "var(--primary)",
                    }}
                  >
                    {sem.result_class || "PASS"}
                  </span>
                </div>

                <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "10px" }}>
                  Exam Date: {sem.exam_date || "—"}
                </div>

                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "8px" }}>
                  <div>
                    <span style={{ fontSize: "10px", color: "var(--text-muted)", display: "block" }}>SGPA</span>
                    <strong style={{ fontSize: "15px", color: "var(--text)" }}>
                      {sem.sgpa ? Number(sem.sgpa).toFixed(2) : "—"}
                    </strong>
                  </div>
                  <div>
                    <span style={{ fontSize: "10px", color: "var(--text-muted)", display: "block" }}>CGPA</span>
                    <strong style={{ fontSize: "15px", color: "var(--primary)" }}>
                      {sem.cgpa ? Number(sem.cgpa).toFixed(2) : "—"}
                    </strong>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 3. ASSIGNMENTS & LMS TRACKING STATUS */}
      <section className="progress-section">
        <div className="progress-section-heading">
          <div>
            <span>SYSTEM INTEGRATION</span>
            <h2>LMS & Coursework Activity</h2>
          </div>
        </div>

        <div
          style={{
            padding: "20px 24px",
            background: "rgba(255,255,255,0.02)",
            border: "1px solid var(--border)",
            borderRadius: "12px",
            display: "flex",
            alignItems: "center",
            gap: "14px",
          }}
        >
          <Clock3 size={20} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
          <div>
            <strong style={{ fontSize: "14px", color: "var(--text)" }}>
              External LMS & Coursework Tracking Not Integrated
            </strong>
            <p style={{ margin: "3px 0 0", fontSize: "12px", color: "var(--text-muted)" }}>
              Assignment submissions and LMS telemetry are not tracked by the University Solutions Student Portal. Academic standing is evaluated from authoritative university examination and attendance records.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

function ProgressCard({ icon: Icon, value, label, sub }) {
  return (
    <div className="progress-stat-card">
      <div className="progress-stat-icon">
        <Icon size={18} />
      </div>

      <div>
        <strong>{value}</strong>
        <span>{label}</span>
        {sub && <small style={{ display: "block", fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>{sub}</small>}
      </div>
    </div>
  );
}

export default Progress;