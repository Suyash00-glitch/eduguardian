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
      <div className="profile-header">
        <div>
          <span className="dashboard-eyebrow">ACCOUNT</span>
          <h2>Profile</h2>
          <p>
            {isPortal
              ? "Academic profile from University Solutions Student Portal."
              : isDemo
              ? "Demo profile — log in with your portal credentials for real data."
              : "Manage your student information."}
          </p>
        </div>

        {/* Data source badge */}
        <div style={{ display: "flex", alignItems: "flex-start", marginTop: "8px" }}>
          {isPortal && (
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                fontSize: "11px",
                fontWeight: 700,
                padding: "4px 10px",
                borderRadius: "20px",
                background: "rgba(6,214,160,0.12)",
                color: "var(--primary)",
                border: "1px solid rgba(6,214,160,0.25)",
              }}
            >
              <CheckCircle2 size={11} />
              University Solutions Portal
            </span>
          )}
          {isDemo && (
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                fontSize: "11px",
                fontWeight: 700,
                padding: "4px 10px",
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
      <section className="profile-card profile-hero">
        <div className="profile-avatar">
          <User size={30} />
        </div>

        <div className="profile-hero-info">
          <h3>{displayName}</h3>
          <p>{displayDept}</p>

          <div className="profile-badges">
            <span className="profile-badge">
              {displaySem ? `Semester ${displaySem}` : "Enrolled"}
            </span>
            <span className="profile-badge role">Student</span>
            {displayDegree && displayDegree !== "—" && (
              <span className="profile-badge">{displayDegree}</span>
            )}
          </div>
        </div>
      </section>

      {/* ACADEMIC STANDING HIGHLIGHT BANNER */}
      {(histPerf.cgpa || histPerf.latest_sgpa) && (
        <section
          className="profile-card"
          style={{
            marginTop: "16px",
            background: "linear-gradient(135deg, rgba(6,214,160,0.06), rgba(84,149,255,0.06))",
            border: "1px solid rgba(6,214,160,0.2)",
          }}
        >
          <div style={{ padding: "16px 20px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
              <Award size={16} style={{ color: "var(--primary)" }} />
              <span className="dashboard-eyebrow" style={{ color: "var(--primary)" }}>
                CUMULATIVE ACADEMIC STANDING
              </span>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
                gap: "14px",
              }}
            >
              {histPerf.cgpa && (
                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 600 }}>
                    CGPA
                  </div>
                  <div style={{ fontSize: "24px", fontWeight: 800, color: "var(--text)" }}>
                    {histPerf.cgpa.toFixed(2)}
                  </div>
                </div>
              )}

              {histPerf.latest_sgpa && (
                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 600 }}>
                    LATEST SGPA
                  </div>
                  <div style={{ fontSize: "24px", fontWeight: 800, color: "var(--text)" }}>
                    {histPerf.latest_sgpa.toFixed(2)}
                  </div>
                </div>
              )}

              {histPerf.sgpa_trend && histPerf.sgpa_trend !== "insufficient_data" && (
                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 600 }}>
                    PERFORMANCE TRAJECTORY
                  </div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      fontSize: "15px",
                      fontWeight: 700,
                      marginTop: "4px",
                      color:
                        histPerf.sgpa_trend === "improving"
                          ? "var(--success, #06d6a0)"
                          : histPerf.sgpa_trend === "declining"
                          ? "var(--danger, #e76f6f)"
                          : "var(--text)",
                    }}
                  >
                    {histPerf.sgpa_trend === "improving" && <TrendingUp size={16} />}
                    {histPerf.sgpa_trend === "declining" && <TrendingDown size={16} />}
                    {histPerf.sgpa_trend === "stable" && <Minus size={16} />}
                    {histPerf.sgpa_trend.charAt(0).toUpperCase() + histPerf.sgpa_trend.slice(1)}
                  </div>
                </div>
              )}

              {histPerf.total_credits_earned && (
                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 600 }}>
                    TOTAL CREDITS
                  </div>
                  <div style={{ fontSize: "24px", fontWeight: 800, color: "var(--text)" }}>
                    {histPerf.total_credits_earned}
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* STUDENT PROFILE DETAILS */}
      <section className="profile-card" style={{ marginTop: "16px" }}>
        <div style={{ padding: "16px 18px", borderBottom: "1px solid var(--border)" }}>
          <span className="dashboard-eyebrow">IDENTITY & PROGRAMME</span>
          <h4 style={{ margin: "4px 0 0", fontSize: "14px" }}>Student Details</h4>
        </div>

        <div className="profile-details-grid">
          <div className="profile-detail">
            <div className="profile-detail-icon">
              <User size={15} />
            </div>
            <div>
              <span>FULL NAME</span>
              <strong>{displayName}</strong>
            </div>
          </div>

          <div className="profile-detail">
            <div className="profile-detail-icon">
              <Mail size={15} />
            </div>
            <div>
              <span>EMAIL</span>
              <strong
                style={{
                  color: displayEmail === "Not available from Student Portal" ? "var(--text-muted)" : undefined,
                  fontStyle: displayEmail === "Not available from Student Portal" ? "italic" : undefined,
                  fontSize: displayEmail === "Not available from Student Portal" ? "12px" : undefined,
                }}
              >
                {displayEmail}
              </strong>
            </div>
          </div>

          {displayCollege && (
            <div className="profile-detail">
              <div className="profile-detail-icon">
                <Building2 size={15} />
              </div>
              <div>
                <span>COLLEGE</span>
                <strong>{displayCollege}</strong>
              </div>
            </div>
          )}

          <div className="profile-detail">
            <div className="profile-detail-icon">
              <Hash size={15} />
            </div>
            <div>
              <span>USN / REGISTRATION NUMBER</span>
              <strong>{displayUSN}</strong>
            </div>
          </div>

          <div className="profile-detail">
            <div className="profile-detail-icon">
              <Building2 size={15} />
            </div>
            <div>
              <span>DEPARTMENT</span>
              <strong>{displayDept}</strong>
            </div>
          </div>

          {displayDegree && displayDegree !== "—" && (
            <div className="profile-detail">
              <div className="profile-detail-icon">
                <GraduationCap size={15} />
              </div>
              <div>
                <span>DEGREE</span>
                <strong>{displayDegree}</strong>
              </div>
            </div>
          )}

          <div className="profile-detail">
            <div className="profile-detail-icon">
              <Calendar size={15} />
            </div>
            <div>
              <span>SEMESTER</span>
              <strong>{displaySem ? `Semester ${displaySem}` : "—"}</strong>
            </div>
          </div>

          {displaySection && (
            <div className="profile-detail">
              <div className="profile-detail-icon">
                <Hash size={15} />
              </div>
              <div>
                <span>SECTION</span>
                <strong>{displaySection}</strong>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* CURRENT SEMESTER ENROLLED SUBJECTS */}
      {enrolledSubjects.length > 0 && (
        <section className="profile-card" style={{ marginTop: "16px" }}>
          <div style={{ padding: "16px 18px", borderBottom: "1px solid var(--border)" }}>
            <span className="dashboard-eyebrow">CURRENT SEMESTER</span>
            <h4 style={{ margin: "4px 0 0", fontSize: "14px" }}>Enrolled Subjects</h4>
          </div>
          <div style={{ padding: "12px 18px" }}>
            {enrolledSubjects.map((sub, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  padding: "8px 0",
                  borderBottom: i < enrolledSubjects.length - 1 ? "1px solid var(--border)" : "none",
                }}
              >
                <BookOpen size={14} style={{ color: "var(--primary)", flexShrink: 0 }} />
                <div>
                  <strong style={{ fontSize: "13px" }}>{sub.subject_name}</strong>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{sub.subject_code}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* CURRENT SEMESTER ATTENDANCE STATUS */}
      <section className="profile-card" style={{ marginTop: "16px" }}>
        <div style={{ padding: "16px 18px", borderBottom: "1px solid var(--border)" }}>
          <span className="dashboard-eyebrow">CURRENT SEMESTER</span>
          <h4 style={{ margin: "4px 0 0", fontSize: "14px" }}>Attendance</h4>
        </div>
        <div style={{ padding: "14px 18px" }}>
          {attendanceStatus === "available" && attendanceValue !== null ? (
            <div style={{ fontSize: "28px", fontWeight: 800, color: "var(--primary)" }}>
              {attendanceValue}%
              <span style={{ fontSize: "12px", fontWeight: 400, color: "var(--text-muted)", marginLeft: "8px" }}>
                overall attendance
              </span>
            </div>
          ) : (
            <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-muted)", fontSize: "13px" }}>
              <AlertCircle size={14} />
              Current semester attendance records are pending faculty upload.
            </div>
          )}
        </div>
      </section>

      {/* HISTORICAL SEMESTER RESULTS & INTERACTIVE MARKS CARD */}
      {historicalSems.length > 0 && (
        <section className="profile-card" style={{ marginTop: "16px" }}>
          <div style={{ padding: "16px 18px", borderBottom: "1px solid var(--border)" }}>
            <span className="dashboard-eyebrow">ACADEMIC PERFORMANCE</span>
            <h4 style={{ margin: "4px 0 0", fontSize: "14px" }}>Marks Card & Previous Results</h4>
            <p style={{ margin: "4px 0 0", fontSize: "12px", color: "var(--text-muted)" }}>
              Click on any semester to view its detailed subject-level Marks Card breakdown.
            </p>
          </div>

          <div style={{ padding: "12px 18px" }}>
            {historicalSems.map((sem, i) => {
              const isExpanded = expandedSemester === sem.semester;
              const subjs = sem.subject_results || [];

              return (
                <div
                  key={i}
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: "10px",
                    marginBottom: "12px",
                    overflow: "hidden",
                    background: isExpanded ? "rgba(255,255,255,0.02)" : "transparent",
                  }}
                >
                  {/* Semester Summary Row (Clickable) */}
                  <div
                    onClick={() => toggleSemester(sem.semester)}
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
                        <strong style={{ fontSize: "14px" }}>
                          Semester {sem.semester}
                        </strong>
                        {sem.exam_name && (
                          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                            {typeof sem.exam_name === "string" ? sem.exam_name.replace(/<br\s*\/?>/gi, " — ") : sem.exam_name}
                          </div>
                        )}
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                      <div style={{ textAlign: "right" }}>
                        <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>SGPA: </span>
                        <strong style={{ fontSize: "13px" }}>
                          {sem.sgpa !== null && sem.sgpa !== undefined ? Number(sem.sgpa).toFixed(2) : "—"}
                        </strong>
                      </div>

                      {sem.cgpa !== null && sem.cgpa !== undefined && (
                        <div style={{ textAlign: "right" }}>
                          <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>CGPA: </span>
                          <strong style={{ fontSize: "13px" }}>
                            {Number(sem.cgpa).toFixed(2)}
                          </strong>
                        </div>
                      )}

                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 700,
                          padding: "3px 8px",
                          borderRadius: "6px",
                          background: sem.result?.toLowerCase().includes("pass")
                            ? "rgba(6,214,160,0.12)"
                            : "rgba(231,111,111,0.12)",
                          color: sem.result?.toLowerCase().includes("pass")
                            ? "var(--success, #06d6a0)"
                            : "var(--danger, #e76f6f)",
                        }}
                      >
                        {sem.result || "RESULT"}
                      </span>

                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                  </div>

                  {/* Expanded Subject-Level Marks Card */}
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
                                        sub.result?.toLowerCase().includes("fail") ||
                                        sub.grade === "F"
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
                          Subject-level marks card breakdown not available for this semester.
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
