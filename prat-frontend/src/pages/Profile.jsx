import React, { useCallback, useEffect, useState } from "react";
import {
  User,
  Mail,
  GraduationCap,
  Building2,
  Hash,
  BookOpen,
  Calendar,
  CheckCircle2,
  AlertCircle,
  Award,
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronDown,
  ChevronUp,
  FileText,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";
import { studentService } from "../services/studentService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

function Profile() {
  const { user } = useAuth();
  const [portalData, setPortalData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedSemester, setExpandedSemester] = useState(null);

  const loadProfile = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const ctx = await studentService.getPortalContext();
      if (ctx && ctx.identity) {
        setPortalData(ctx);
        // Auto-expand the most recent semester with subject results
        const sems = ctx.historical_semesters || [];
        if (sems.length > 0) {
          const withSubjs = sems.find((s) => s.subject_results && s.subject_results.length > 0);
          if (withSubjs) {
            setExpandedSemester(withSubjs.semester);
          } else {
            setExpandedSemester(sems[0].semester);
          }
        }
      } else {
        const demo = await studentService.getStudent();
        setPortalData({ _isDemo: true, ...demo });
      }
    } catch (err) {
      setError(err.message || "Unable to load profile.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  if (loading) {
    return <LoadingState message="Loading your profile..." />;
  }

  if (error && !portalData) {
    return (
      <ErrorState
        title="Unable to load profile"
        message={error}
        onRetry={loadProfile}
      />
    );
  }

  const identity = portalData?.identity;
  const isPortal = portalData?.data_source === "student_portal";
  const isDemo = portalData?.data_source === "demo" || portalData?._isDemo;

  const displayName = identity?.name || user?.full_name || portalData?.name || "—";
  const displayUSN = identity?.usn || user?.usn || portalData?.usn || "—";
  const displayDept = identity?.department || user?.department || portalData?.department || "—";
  const displayDegree = identity?.degree || portalData?.degree || "—";
  const displaySem = identity?.semester || user?.semester || portalData?.semester;
  const displayEmail = isPortal
    ? (identity?.email || "Not available from Student Portal")
    : (user?.email || portalData?.email || "—");
  const displaySection = identity?.section || user?.section || portalData?.section;
  const displayCollege = identity?.college;

  const historicalSems = portalData?.historical_semesters || [];
  const histPerf = portalData?.historical_academic_performance || {};
  const enrolledSubjects = portalData?.current_academic_profile?.enrolled_subjects || [];
  const attendanceStatus = portalData?.attendance?.status || "not_available";
  const attendanceValue = portalData?.attendance?.value;

  const toggleSemester = (semId) => {
    setExpandedSemester((prev) => (prev === semId ? null : semId));
  };

  return (
    <div className="profile-page">
      {/* HEADER */}
      <div className="profile-header" style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <h1 style={{ fontSize: "var(--font-2xl)", fontWeight: 700, margin: 0, color: "var(--text)" }}>
            Student Profile
          </h1>
          <p style={{ margin: "6px 0 0", fontSize: "var(--font-base)", color: "var(--text-secondary)" }}>
            {isPortal
              ? "Authoritative academic credentials synchronized with University Solutions Student Portal."
              : "Institutional identity, enrollment status, and verified examination marks cards."}
          </p>
        </div>

        {/* Data source badge */}
        <div>
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
          {isDemo && (
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                fontSize: "var(--font-xs)",
                fontWeight: 600,
                padding: "6px 14px",
                borderRadius: "20px",
                background: "rgba(255,209,102,0.12)",
                color: "#ffd166",
                border: "1px solid rgba(255,209,102,0.25)",
              }}
            >
              Demo Profile Mode
            </span>
          )}
        </div>
      </div>

      {/* STUDENT IDENTITY HERO CARD */}
      <section
        style={{
          padding: "22px 24px",
          borderRadius: "12px",
          border: "1px solid var(--border)",
          background: "var(--surface)",
          display: "flex",
          alignItems: "center",
          gap: "20px",
          marginBottom: "20px",
        }}
      >
        <div
          style={{
            width: "56px",
            height: "56px",
            borderRadius: "14px",
            background: "var(--primary-soft)",
            color: "var(--primary)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <User size={28} />
        </div>

        <div style={{ flex: 1 }}>
          <h2 style={{ fontSize: "var(--font-xl)", fontWeight: 700, margin: 0, color: "var(--text)" }}>
            {displayName}
          </h2>
          <p style={{ margin: "4px 0 0", fontSize: "var(--font-sm)", color: "var(--text-secondary)" }}>
            {displayDept} {displayCollege ? `· ${displayCollege}` : ""}
          </p>

          <div style={{ display: "flex", gap: "8px", marginTop: "12px", flexWrap: "wrap" }}>
            <span
              style={{
                fontSize: "var(--font-xs)",
                fontWeight: 600,
                padding: "4px 10px",
                borderRadius: "6px",
                background: "var(--surface-soft)",
                color: "var(--text)",
                border: "1px solid var(--border)",
              }}
            >
              {displaySem ? `Semester ${displaySem}` : "Enrolled"}
            </span>
            <span
              style={{
                fontSize: "var(--font-xs)",
                fontWeight: 600,
                padding: "4px 10px",
                borderRadius: "6px",
                background: "rgba(6,214,160,0.12)",
                color: "var(--primary)",
              }}
            >
              Verified Student
            </span>
            {displayDegree && displayDegree !== "—" && (
              <span
                style={{
                  fontSize: "var(--font-xs)",
                  padding: "4px 10px",
                  borderRadius: "6px",
                  background: "var(--surface-soft)",
                  color: "var(--text-secondary)",
                  border: "1px solid var(--border)",
                }}
              >
                {displayDegree}
              </span>
            )}
          </div>
        </div>
      </section>

      {/* ACADEMIC STANDING HIGHLIGHT BANNER */}
      {(histPerf.cgpa || histPerf.latest_sgpa) && (
        <section
          style={{
            padding: "20px 24px",
            borderRadius: "12px",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            marginBottom: "20px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px" }}>
            <Award size={18} style={{ color: "var(--primary)" }} />
            <h3 style={{ fontSize: "var(--font-md)", fontWeight: 600, margin: 0, color: "var(--text)" }}>
              Cumulative Academic Standing
            </h3>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
              gap: "16px",
            }}
          >
            {histPerf.cgpa && (
              <div>
                <div style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", fontWeight: 600 }}>
                  Cumulative CGPA
                </div>
                <div style={{ fontSize: "var(--font-stat)", fontWeight: 700, color: "var(--text)", marginTop: "2px" }}>
                  {histPerf.cgpa.toFixed(2)}
                </div>
              </div>
            )}

            {histPerf.latest_sgpa && (
              <div>
                <div style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", fontWeight: 600 }}>
                  Latest SGPA
                </div>
                <div style={{ fontSize: "var(--font-stat)", fontWeight: 700, color: "var(--text)", marginTop: "2px" }}>
                  {histPerf.latest_sgpa.toFixed(2)}
                </div>
              </div>
            )}

            {histPerf.sgpa_trend && histPerf.sgpa_trend !== "insufficient_data" && (
              <div>
                <div style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", fontWeight: 600 }}>
                  Performance Trajectory
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    fontSize: "var(--font-md)",
                    fontWeight: 700,
                    marginTop: "6px",
                    color:
                      histPerf.sgpa_trend === "improving"
                        ? "var(--primary)"
                        : histPerf.sgpa_trend === "declining"
                        ? "var(--danger)"
                        : "var(--text)",
                  }}
                >
                  {histPerf.sgpa_trend === "improving" && <TrendingUp size={18} />}
                  {histPerf.sgpa_trend === "declining" && <TrendingDown size={18} />}
                  {histPerf.sgpa_trend === "stable" && <Minus size={18} />}
                  {histPerf.sgpa_trend.charAt(0).toUpperCase() + histPerf.sgpa_trend.slice(1)}
                </div>
              </div>
            )}

            {histPerf.total_credits_earned && (
              <div>
                <div style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", fontWeight: 600 }}>
                  Total Credits Earned
                </div>
                <div style={{ fontSize: "var(--font-stat)", fontWeight: 700, color: "var(--text)", marginTop: "2px" }}>
                  {histPerf.total_credits_earned}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* STUDENT PROFILE DETAILS */}
      <section
        style={{
          borderRadius: "12px",
          border: "1px solid var(--border)",
          background: "var(--surface)",
          overflow: "hidden",
          marginBottom: "20px",
        }}
      >
        <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--border)" }}>
          <h3 style={{ margin: 0, fontSize: "var(--font-md)", fontWeight: 600, color: "var(--text)" }}>
            Institutional Registration Details
          </h3>
        </div>

        <div
          style={{
            padding: "20px 22px",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "16px",
          }}
        >
          <div style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}>
            <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "var(--surface-soft)", color: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <User size={16} />
            </div>
            <div>
              <span style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", display: "block" }}>Full Name</span>
              <strong style={{ fontSize: "var(--font-sm)", color: "var(--text)" }}>{displayName}</strong>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}>
            <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "var(--surface-soft)", color: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Mail size={16} />
            </div>
            <div>
              <span style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", display: "block" }}>Email</span>
              <strong style={{ fontSize: "var(--font-sm)", color: "var(--text)" }}>{displayEmail}</strong>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}>
            <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "var(--surface-soft)", color: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Hash size={16} />
            </div>
            <div>
              <span style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", display: "block" }}>USN / Reg No</span>
              <strong style={{ fontSize: "var(--font-sm)", color: "var(--text)" }}>{displayUSN}</strong>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}>
            <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "var(--surface-soft)", color: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Building2 size={16} />
            </div>
            <div>
              <span style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", display: "block" }}>Department</span>
              <strong style={{ fontSize: "var(--font-sm)", color: "var(--text)" }}>{displayDept}</strong>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}>
            <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "var(--surface-soft)", color: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Calendar size={16} />
            </div>
            <div>
              <span style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", display: "block" }}>Current Semester</span>
              <strong style={{ fontSize: "var(--font-sm)", color: "var(--text)" }}>{displaySem ? `Semester ${displaySem}` : "—"}</strong>
            </div>
          </div>

          {displaySection && (
            <div style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}>
              <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "var(--surface-soft)", color: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Hash size={16} />
              </div>
              <div>
                <span style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", display: "block" }}>Section</span>
                <strong style={{ fontSize: "var(--font-sm)", color: "var(--text)" }}>{displaySection}</strong>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* HISTORICAL SEMESTER RESULTS & INTERACTIVE MARKS CARD */}
      {historicalSems.length > 0 && (
        <section
          style={{
            borderRadius: "12px",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            overflow: "hidden",
            marginBottom: "20px",
          }}
        >
          <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--border)" }}>
            <h3 style={{ margin: 0, fontSize: "var(--font-md)", fontWeight: 600, color: "var(--text)" }}>
              Marks Cards &amp; Examination Records
            </h3>
            <p style={{ margin: "4px 0 0", fontSize: "var(--font-sm)", color: "var(--text-muted)" }}>
              Click on any semester to expand its authoritative subject-level marks card.
            </p>
          </div>

          <div style={{ padding: "16px 20px" }}>
            {historicalSems.map((sem, i) => {
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
                  <div
                    onClick={() => toggleSemester(sem.semester)}
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
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <strong style={{ fontSize: "var(--font-base)", color: "var(--text)" }}>
                            {sem.is_summer || (sem.exam_name || "").toLowerCase().includes("summer") || (sem.semester || "").toLowerCase().includes("summer")
                              ? (sem.display_label || sem.short_title || "Summer Semester")
                              : (sem.semester_number ? `Semester ${sem.semester_number}` : sem.display_label || `Semester ${sem.semester}`)}
                          </strong>
                          {(sem.is_summer || (sem.exam_name || "").toLowerCase().includes("summer") || (sem.semester || "").toLowerCase().includes("summer")) && (
                            <span style={{ fontSize: "10px", fontWeight: 700, padding: "2px 6px", borderRadius: "4px", background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8", border: "1px solid rgba(56, 189, 248, 0.3)" }}>
                              Summer Sem
                            </span>
                          )}
                        </div>
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
                                <th style={{ textAlign: "center", padding: "8px 10px" }}>GP</th>
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
    </div>
  );
}

export default Profile;
