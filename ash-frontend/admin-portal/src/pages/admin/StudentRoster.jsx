import React, { useEffect, useState, useMemo } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Users,
  AlertTriangle,
  TrendingDown,
  CheckCircle2,
  HelpCircle,
  Eye,
  Search,
  SlidersHorizontal,
  FileText,
  Clock,
  BookOpen,
  Calendar,
  Layers,
  ArrowUpDown,
  GraduationCap,
  ShieldAlert,
  Info,
  X,
} from "lucide-react";
import { useTeacher } from "../../context/TeacherContext";
import { RiskBadge, ConfidenceBadge, EmptyState } from "../../components/shared/Shared";

export default function StudentRoster() {
  const { active } = useTeacher();

  // State Management
  const [students, setStudents] = useState([]);
  const [summary, setSummary] = useState({
    total_enrolled: 0,
    high_risk: 0,
    medium_risk: 0,
    low_risk: 0,
    insufficient_data: 0,
  });
  const [selected, setSelected] = useState(null);
  const [detailedProfile, setDetailedProfile] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [showMarksCardModal, setShowMarksCardModal] = useState(false);

  // Filters & Search State
  const [searchQuery, setSearchQuery] = useState("");
  const [riskFilter, setRiskFilter] = useState("all");
  const [confidenceFilter, setConfidenceFilter] = useState("all");
  const [sortBy, setSortBy] = useState("risk_desc");

  // Pagination & Loading
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [totalStudents, setTotalStudents] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  const [detailError, setDetailError] = useState("");

  // 1. Fetch Student Roster from Backend API
  useEffect(() => {
    async function fetchStudents() {
      setLoading(true);
      setError("");
      try {
        const token = localStorage.getItem("token");
        const params = new URLSearchParams();

        if (active?.department) params.append("department", active.department);
        if (active?.semester) params.append("semester", String(active.semester));
        if (active?.section) params.append("section", active.section);
        params.append("page", String(page));
        params.append("page_size", String(pageSize));
        params.append("risk", riskFilter);

        const res = await fetch(`http://localhost:5000/api/students/roster?${params.toString()}`, {
          headers: {
            "Content-Type": "application/json",
            Authorization: token ? `Bearer ${token}` : "",
          },
        });

        if (res.status === 401) {
          throw new Error("Authentication required. Please log in.");
        }
        if (res.status === 403) {
          throw new Error("Access forbidden: Faculty/Admin permissions required.");
        }
        if (!res.ok) {
          throw new Error(`Failed to load roster (HTTP ${res.status}).`);
        }

        const data = await res.json();
        const studentList = data.students || [];
        setStudents(studentList);
        setTotalStudents(data.total_students || studentList.length);
        setTotalPages(data.total_pages || Math.ceil(studentList.length / pageSize) || 1);

        if (data.summary) {
          setSummary(data.summary);
        } else {
          // Dynamic calculation if summary object is absent
          const high = studentList.filter((s) => s.risk_level?.toLowerCase() === "high").length;
          const med = studentList.filter((s) => s.risk_level?.toLowerCase() === "medium").length;
          const low = studentList.filter((s) => s.risk_level?.toLowerCase() === "low").length;
          const ins = studentList.filter((s) => s.risk_level?.toLowerCase()?.includes("insufficient")).length;
          setSummary({
            total_enrolled: studentList.length,
            high_risk: high,
            medium_risk: med,
            low_risk: low,
            insufficient_data: ins,
          });
        }

        if (studentList.length > 0 && !selected) {
          setSelected(studentList[0]);
        }
      } catch (err) {
        console.error("StudentRoster fetch error:", err);
        setError(err.message || "Unable to load student risk data.");
      } finally {
        setLoading(false);
      }
    }

    fetchStudents();
  }, [active, page, riskFilter, pageSize]);

  // 2. Fetch Deep Risk Detail & Marks Cards when a student is selected
  useEffect(() => {
    if (!selected) {
      setDetailedProfile(null);
      setDetailError("");
      return;
    }

    let isMounted = true;
    const studentId = selected.id || selected.student_id;

    async function fetchStudentDetail() {
      setLoadingDetail(true);
      setDetailError("");
      try {
        const token = localStorage.getItem("token");
        const res = await fetch(`http://localhost:5000/api/students/risk-detail/${studentId}`, {
          headers: {
            "Content-Type": "application/json",
            Authorization: token ? `Bearer ${token}` : "",
          },
        });

        if (!res.ok) {
          throw new Error(`Failed to load student profile (HTTP ${res.status}).`);
        }

        const detailData = await res.json();
        if (isMounted) {
          setDetailedProfile(detailData);
        }
      } catch (err) {
        console.error("Failed to load student risk detail:", err);
        if (isMounted) {
          setDetailError("Unable to load student profile.");
        }
      } finally {
        if (isMounted) {
          setLoadingDetail(false);
        }
      }
    }

    fetchStudentDetail();

    return () => {
      isMounted = false;
    };
  }, [selected?.id, selected?.student_id]);

  // 3. Client-Side Search, Filter & Sorting
  const filteredStudents = useMemo(() => {
    let result = [...students];

    // Search Query (Name or USN)
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      result = result.filter(
        (s) =>
          (s.name && s.name.toLowerCase().includes(q)) ||
          (s.usn && s.usn.toLowerCase().includes(q)) ||
          (s.email && s.email.toLowerCase().includes(q))
      );
    }

    // Confidence Filter
    if (confidenceFilter !== "all") {
      result = result.filter((s) => {
        const conf = (s.confidence || "LOW").toUpperCase();
        if (confidenceFilter === "high") return conf === "FULL" || conf === "HIGH";
        if (confidenceFilter === "partial") return conf === "PARTIAL" || conf === "MEDIUM";
        if (confidenceFilter === "low") return conf === "LOW";
        return true;
      });
    }

    // Sorting
    result.sort((a, b) => {
      if (sortBy === "risk_desc") return (b.risk_score || 0) - (a.risk_score || 0);
      if (sortBy === "risk_asc") return (a.risk_score || 0) - (b.risk_score || 0);
      if (sortBy === "cgpa_desc") return (b.cgpa || 0) - (a.cgpa || 0);
      if (sortBy === "cgpa_asc") return (a.cgpa || 0) - (b.cgpa || 0);
      if (sortBy === "backlogs_desc") return (b.backlogs || 0) - (a.backlogs || 0);
      if (sortBy === "name_asc") return (a.name || "").localeCompare(b.name || "");
      if (sortBy === "usn_asc") return (a.usn || "").localeCompare(b.usn || "");
      return 0;
    });

    return result;
  }, [students, searchQuery, confidenceFilter, sortBy]);

  // Format Helper for Risk Basis
  const formatRiskBasis = (basis) => {
    if (!basis) return "Historical Academic Performance";
    return basis
      .split("_")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");
  };

  return (
    <div className="roster-page">
      {/* ── Page Header ───────────────────────────────────────────── */}
      <div className="roster-header">
        <div>
          <h2>Student Risk &amp; Academic Diagnostics</h2>
          <p>
            Cohort records and explainable risk profiles · {active?.department || "ISE"} · Semester {active?.semester || 5} · Section{" "}
            {active?.section || "C"}
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <div className="search-input-wrapper" style={{ position: "relative" }}>
            <Search
              size={14}
              style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }}
            />
            <input
              type="text"
              placeholder="Search by Name or USN..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="roster-search-input"
              style={{
                paddingLeft: "32px",
                paddingRight: "12px",
                height: "36px",
                borderRadius: "8px",
                background: "rgba(255,255,255,0.05)",
                border: "1px solid var(--border)",
                color: "var(--text)",
                fontSize: "13px",
                minWidth: "220px",
              }}
            />
          </div>

          <select
            value={riskFilter}
            onChange={(e) => {
              setRiskFilter(e.target.value);
              setPage(1);
            }}
            className="roster-risk-select"
          >
            <option value="all">All Risk Levels</option>
            <option value="high">High Risk Only</option>
            <option value="medium">Medium Risk Only</option>
            <option value="low">Low Risk Only</option>
            <option value="insufficient">Insufficient Data</option>
          </select>
        </div>
      </div>

      {/* ── Dynamic Cohort Risk Summary Counters ─────────────────── */}
      <div className="teacher-stats-grid" style={{ marginBottom: "20px" }}>
        <div className="teacher-stat-card">
          <div className="teacher-stat-top">
            <span>Total Enrolled</span>
            <div className="teacher-stat-icon neutral">
              <Users size={16} />
            </div>
          </div>
          <strong>{summary.total_enrolled || totalStudents}</strong>
        </div>

        <div className="teacher-stat-card">
          <div className="teacher-stat-top">
            <span className="danger-text">High Risk</span>
            <div className="teacher-stat-icon danger">
              <AlertTriangle size={16} />
            </div>
          </div>
          <strong className="danger-text">{summary.high_risk}</strong>
        </div>

        <div className="teacher-stat-card">
          <div className="teacher-stat-top">
            <span className="warning-text">Medium Risk</span>
            <div className="teacher-stat-icon warning">
              <TrendingDown size={16} />
            </div>
          </div>
          <strong className="warning-text">{summary.medium_risk}</strong>
        </div>

        <div className="teacher-stat-card">
          <div className="teacher-stat-top">
            <span className="primary-text">Low Risk</span>
            <div className="teacher-stat-icon primary">
              <CheckCircle2 size={16} />
            </div>
          </div>
          <strong className="primary-text">{summary.low_risk}</strong>
        </div>

        {summary.insufficient_data > 0 && (
          <div className="teacher-stat-card">
            <div className="teacher-stat-top">
              <span>Insufficient Data</span>
              <div className="teacher-stat-icon neutral">
                <HelpCircle size={16} />
              </div>
            </div>
            <strong>{summary.insufficient_data}</strong>
          </div>
        )}
      </div>

      {/* ── Filter & Sort Bar ──────────────────────────────────────── */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "14px",
          padding: "8px 14px",
          background: "rgba(255,255,255,0.02)",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          fontSize: "12px",
        }}
      >
        <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
          <span style={{ color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "4px" }}>
            <SlidersHorizontal size={13} /> Filter Confidence:
          </span>
          <select
            value={confidenceFilter}
            onChange={(e) => setConfidenceFilter(e.target.value)}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text)",
              fontSize: "12px",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            <option value="all" style={{ background: "#1b2533" }}>All Confidence Levels</option>
            <option value="high" style={{ background: "#1b2533" }}>High (Multi-Signal)</option>
            <option value="partial" style={{ background: "#1b2533" }}>Partial Signal</option>
            <option value="low" style={{ background: "#1b2533" }}>Low (Early-Semester)</option>
          </select>
        </div>

        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span style={{ color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "4px" }}>
            <ArrowUpDown size={13} /> Sort:
          </span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text)",
              fontSize: "12px",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            <option value="risk_desc" style={{ background: "#1b2533" }}>Risk Score (Highest First)</option>
            <option value="risk_asc" style={{ background: "#1b2533" }}>Risk Score (Lowest First)</option>
            <option value="cgpa_desc" style={{ background: "#1b2533" }}>CGPA (High to Low)</option>
            <option value="cgpa_asc" style={{ background: "#1b2533" }}>CGPA (Low to High)</option>
            <option value="backlogs_desc" style={{ background: "#1b2533" }}>Backlogs (Most First)</option>
            <option value="name_asc" style={{ background: "#1b2533" }}>Student Name (A-Z)</option>
            <option value="usn_asc" style={{ background: "#1b2533" }}>USN (A-Z)</option>
          </select>
        </div>
      </div>

      {/* ── Main Layout: Table + Detail Panel ─────────────────────── */}
      <div className="roster-grid">
        {/* Left: Authoritative Student Table */}
        <div className="teacher-panel roster-table-panel" style={{ flex: 1.4 }}>
          <div className="teacher-panel-header">
            <h3>Student Roster &amp; Academic Performance</h3>
            <span className="teacher-panel-sub">{filteredStudents.length} matching students</span>
          </div>

          {loading && (
            <div className="ui-state">
              <span>Loading student risk overview...</span>
            </div>
          )}

          {error && (
            <div className="ui-state">
              <span className="danger-text">{error}</span>
            </div>
          )}

          {!loading && !error && filteredStudents.length === 0 && (
            <EmptyState icon={<Users size={20} />} title="No student records available" message="Try adjusting your search query or risk filters." />
          )}

          {!loading && !error && filteredStudents.length > 0 && (
            <div className="roster-table" style={{ overflowX: "auto" }}>
              <div
                className="roster-table-head"
                style={{
                  display: "grid",
                  gridTemplateColumns: "1.8fr 0.8fr 0.8fr 0.9fr 0.7fr 1.1fr 1fr 0.7fr",
                  gap: "8px",
                  padding: "10px 14px",
                  fontSize: "11px",
                  fontWeight: 700,
                  color: "var(--text-muted)",
                  borderBottom: "1px solid var(--border)",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}
              >
                <span>Name &amp; USN</span>
                <span>CGPA</span>
                <span>Latest SGPA</span>
                <span>Attendance</span>
                <span>Backlogs</span>
                <span>Risk Level</span>
                <span>Confidence</span>
                <span>Action</span>
              </div>

              {filteredStudents.map((s) => {
                const isSelected = selected?.id === s.id;
                const isPendingAttendance = s.attendance_status === "pending" || s.attendance === null || s.attendance === undefined;

                return (
                  <div
                    key={s.id || s.usn}
                    className={`roster-row${isSelected ? " active" : ""}`}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1.8fr 0.8fr 0.8fr 0.9fr 0.7fr 1.1fr 1fr 0.7fr",
                      gap: "8px",
                      alignItems: "center",
                      padding: "12px 14px",
                      borderBottom: "1px solid rgba(255,255,255,0.04)",
                      cursor: "pointer",
                      background: isSelected ? "rgba(6,214,160,0.06)" : "transparent",
                      transition: "background 0.15s ease",
                    }}
                    onClick={() => setSelected(s)}
                  >
                    {/* Name & USN & Source */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
                        <strong style={{ fontSize: "13px", color: "var(--text)" }}>{s.name}</strong>
                        {s.data_source === "student_portal" ? (
                          <span
                            style={{
                              fontSize: "9px",
                              fontWeight: 700,
                              padding: "1px 5px",
                              borderRadius: "4px",
                              background: "rgba(6,214,160,0.15)",
                              color: "#06d6a0",
                              border: "1px solid rgba(6,214,160,0.3)",
                              letterSpacing: "0.03em",
                            }}
                          >
                            PORTAL
                          </span>
                        ) : (
                          <span
                            style={{
                              fontSize: "9px",
                              fontWeight: 600,
                              padding: "1px 5px",
                              borderRadius: "4px",
                              background: "rgba(255,255,255,0.06)",
                              color: "var(--text-muted)",
                              border: "1px solid rgba(255,255,255,0.1)",
                              letterSpacing: "0.03em",
                            }}
                          >
                            DEMO
                          </span>
                        )}
                      </div>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>{s.usn}</span>
                    </div>

                    {/* CGPA */}
                    <span
                      style={{
                        fontSize: "13px",
                        fontWeight: 700,
                        color: s.cgpa >= 7.5 ? "var(--primary)" : s.cgpa < 6.0 ? "var(--danger)" : "var(--text)",
                      }}
                    >
                      {s.cgpa !== null && s.cgpa !== undefined ? Number(s.cgpa).toFixed(2) : "—"}
                    </span>

                    {/* Latest SGPA */}
                    <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--text)" }}>
                      {s.latest_sgpa !== null && s.latest_sgpa !== undefined ? Number(s.latest_sgpa).toFixed(2) : "—"}
                    </span>

                    {/* Attendance (Never 0% for pending) */}
                    <div>
                      {isPendingAttendance ? (
                        <span
                          style={{
                            fontSize: "11px",
                            fontWeight: 600,
                            padding: "2px 6px",
                            borderRadius: "4px",
                            background: "rgba(255,255,255,0.06)",
                            color: "var(--text-muted)",
                          }}
                          title="Current semester attendance not yet published"
                        >
                          Pending
                        </span>
                      ) : (
                        <span style={{ fontSize: "12px", fontWeight: 600, color: s.attendance < 75 ? "var(--danger)" : "var(--primary)" }}>
                          {Number(s.attendance).toFixed(1)}%
                        </span>
                      )}
                    </div>

                    {/* Backlogs */}
                    <span
                      style={{
                        fontSize: "13px",
                        fontWeight: 700,
                        color: s.backlogs > 0 ? "var(--danger)" : "var(--primary)",
                      }}
                    >
                      {s.backlogs ?? 0}
                    </span>

                    {/* Risk Level Badge */}
                    <div>
                      <RiskBadge risk={s.risk_level} />
                    </div>

                    {/* Calibrated Confidence Badge */}
                    <div>
                      <ConfidenceBadge confidence={s.confidence} />
                    </div>

                    {/* Action Button */}
                    <button
                      style={{
                        border: "none",
                        background: isSelected ? "var(--primary)" : "rgba(6,214,160,0.12)",
                        color: isSelected ? "#121a24" : "var(--primary)",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "4px",
                        fontSize: "11px",
                        fontWeight: 700,
                        padding: "6px 10px",
                        borderRadius: "6px",
                        transition: "all 0.15s ease",
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelected(s);
                      }}
                      title="Inspect student risk details"
                    >
                      <Eye size={12} /> View
                    </button>
                  </div>
                );
              })}
            </div>
          )}

          {/* Pagination Controls */}
          {!loading && totalPages > 1 && (
            <div className="roster-pagination" style={{ marginTop: "14px" }}>
              <button disabled={page === 1} onClick={() => setPage(page - 1)}>
                <ChevronLeft size={14} />
              </button>
              <span>
                Page {page} of {totalPages}
              </span>
              <button disabled={page === totalPages} onClick={() => setPage(page + 1)}>
                <ChevronRight size={14} />
              </button>
            </div>
          )}
        </div>

        {/* Right: Explainability & Deep Intervention Panel */}
        <div className="teacher-panel roster-detail-panel" style={{ flex: 1 }}>
          {selected ? (() => {
            const profile = detailedProfile || selected;
            const isPortal = (profile?.data_source === "student_portal") || (selected?.data_source === "student_portal");
            const cgpa = detailedProfile?.academic_performance?.cgpa ?? profile?.cgpa;
            const latestSgpa = detailedProfile?.academic_performance?.latest_sgpa ?? profile?.latest_sgpa;
            const backlogs = detailedProfile?.academic_performance?.backlogs ?? profile?.backlogs ?? 0;
            const riskLevel = detailedProfile?.risk_assessment?.risk_level ?? profile?.risk_level ?? "LOW";
            const riskScore = detailedProfile?.risk_assessment?.risk_score ?? profile?.risk_score;
            const confidence = detailedProfile?.risk_assessment?.confidence ?? profile?.confidence ?? "LOW";
            const riskBasis = detailedProfile?.risk_assessment?.risk_basis ?? profile?.risk_basis;
            const factors = detailedProfile?.risk_assessment?.factors ?? profile?.factors ?? [];
            const recoveryProb = detailedProfile?.risk_assessment?.recovery_probability ?? profile?.recovery_probability;
            const supportSignal = detailedProfile?.risk_assessment?.support_signal ?? profile?.support_signal;
            const attVal = detailedProfile?.current_semester?.attendance ?? profile?.attendance;
            const attStatus = detailedProfile?.current_semester?.attendance_status ?? profile?.attendance_status ?? (attVal !== null && attVal !== undefined ? "published" : "pending");
            const isPendingAttendance = attStatus === "pending" || attVal === null || attVal === undefined;

            return (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {/* Student Identity Header */}
                <div style={{ borderBottom: "1px solid var(--border)", paddingBottom: "12px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <h3 style={{ margin: 0, fontSize: "18px" }}>{profile.name}</h3>
                        {isPortal ? (
                          <span
                            style={{
                              fontSize: "10px",
                              fontWeight: 700,
                              padding: "2px 6px",
                              borderRadius: "4px",
                              background: "rgba(6,214,160,0.15)",
                              color: "#06d6a0",
                              border: "1px solid rgba(6,214,160,0.3)",
                            }}
                          >
                            PORTAL
                          </span>
                        ) : (
                          <span
                            style={{
                              fontSize: "10px",
                              fontWeight: 600,
                              padding: "2px 6px",
                              borderRadius: "4px",
                              background: "rgba(255,255,255,0.06)",
                              color: "var(--text-muted)",
                              border: "1px solid rgba(255,255,255,0.1)",
                            }}
                          >
                            DEMO
                          </span>
                        )}
                      </div>
                      <span style={{ fontSize: "12px", color: "var(--text-muted)", fontFamily: "monospace", marginTop: "4px", display: "inline-block" }}>
                        {profile.usn} · {profile.department || active?.department || "ISE"} · Sem {profile.semester || active?.semester || 5} · Sec {profile.section || active?.section || "—"}
                      </span>
                    </div>
                    <RiskBadge risk={riskLevel} />
                  </div>
                </div>

                {/* Loading / Error Banner */}
                {loadingDetail && (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "rgba(6,214,160,0.08)",
                      border: "1px solid rgba(6,214,160,0.2)",
                      fontSize: "12px",
                      color: "var(--primary)",
                    }}
                  >
                    <Clock size={14} />
                    <span>Loading student profile...</span>
                  </div>
                )}
                {detailError && (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "rgba(231,111,111,0.08)",
                      border: "1px solid rgba(231,111,111,0.2)",
                      fontSize: "12px",
                      color: "var(--danger)",
                    }}
                  >
                    <AlertTriangle size={14} />
                    <span>{detailError}</span>
                  </div>
                )}

                {/* Authoritative Risk Assessment Box */}
                <div
                  style={{
                    padding: "14px 16px",
                    borderRadius: "10px",
                    background:
                      String(riskLevel).toUpperCase() === "HIGH"
                        ? "rgba(231,111,111,0.08)"
                        : String(riskLevel).toUpperCase() === "MEDIUM"
                        ? "rgba(255,209,102,0.08)"
                        : "rgba(6,214,160,0.08)",
                    border:
                      String(riskLevel).toUpperCase() === "HIGH"
                        ? "1px solid rgba(231,111,111,0.25)"
                        : String(riskLevel).toUpperCase() === "MEDIUM"
                        ? "1px solid rgba(255,209,102,0.25)"
                        : "1px solid rgba(6,214,160,0.25)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <ShieldAlert size={16} color={String(riskLevel).toUpperCase() === "HIGH" ? "#e76f6f" : "#06d6a0"} />
                      <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--text)" }}>
                        Risk Score: {riskScore ?? "—"} / 100
                      </span>
                    </div>
                    <ConfidenceBadge confidence={confidence} />
                  </div>

                  <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "8px" }}>
                    Risk Basis:{" "}
                    <strong style={{ color: "var(--text)" }}>{formatRiskBasis(riskBasis)}</strong>
                  </div>

                  {/* Calibrated Confidence Notice */}
                  {isPendingAttendance && (
                    <div
                      style={{
                        display: "flex",
                        alignItems: "flex-start",
                        gap: "6px",
                        padding: "8px 10px",
                        borderRadius: "6px",
                        background: "rgba(255,255,255,0.04)",
                        border: "1px solid rgba(255,255,255,0.08)",
                        fontSize: "11px",
                        color: "var(--text-muted)",
                        lineHeight: "1.4",
                      }}
                    >
                      <Info size={13} style={{ flexShrink: 0, marginTop: "2px", color: "var(--warning)" }} />
                      <span>
                        Current-semester attendance and assessments are pending publication. Risk estimate is calibrated based on
                        historical University Portal records.
                      </span>
                    </div>
                  )}
                </div>

                {/* Academic Standing & Trajectory Indicators */}
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <h4 style={{ margin: 0, fontSize: "var(--font-sm)", fontWeight: 600, color: "var(--text-secondary)" }}>
                    Academic Standing &amp; Observations
                  </h4>
                  <div className="roster-detail-rows">
                    <div>
                      <span>Cumulative CGPA</span>
                      <strong>{cgpa !== null && cgpa !== undefined ? Number(cgpa).toFixed(2) : "—"}</strong>
                    </div>
                    <div>
                      <span>Latest SGPA</span>
                      <strong>{latestSgpa !== null && latestSgpa !== undefined ? Number(latestSgpa).toFixed(2) : "—"}</strong>
                    </div>
                    <div>
                      <span>Historical Backlogs</span>
                      <strong style={{ color: backlogs > 0 ? "var(--danger)" : "var(--primary)" }}>
                        {backlogs ?? 0}
                      </strong>
                    </div>
                    <div>
                      <span>Current Attendance</span>
                      <strong style={{ color: isPendingAttendance ? "var(--text-muted)" : "var(--text)" }}>
                        {isPendingAttendance ? "Pending publication" : `${attVal}%`}
                      </strong>
                    </div>
                    <div>
                      <span>Recovery Probability</span>
                      <strong style={{ color: "var(--primary)" }}>
                        {recoveryProb ? `${recoveryProb}%` : "—"}
                      </strong>
                    </div>
                  </div>
                </div>

                {/* Explainable Contributing Factors (from Backend Engine) */}
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <h4 style={{ margin: 0, fontSize: "var(--font-sm)", fontWeight: 600, color: "var(--text-secondary)" }}>
                    Contributing Risk Signals
                  </h4>
                  {factors && factors.length > 0 ? (
                    <ul
                      style={{
                        margin: 0,
                        paddingLeft: "18px",
                        fontSize: "12px",
                        color: "var(--text)",
                        lineHeight: "1.6",
                      }}
                    >
                      {factors.map((f, idx) => (
                        <li key={idx} style={{ marginBottom: "2px" }}>
                          {f}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                      No negative risk flags detected. Consistent academic standing.
                    </span>
                  )}
                </div>

                {/* Recommended Intervention / Faculty Support Area */}
                {supportSignal && (
                  <div
                    style={{
                      padding: "10px 14px",
                      borderRadius: "8px",
                      background: "rgba(6,214,160,0.06)",
                      border: "1px solid rgba(6,214,160,0.2)",
                      fontSize: "12px",
                    }}
                  >
                    <span
                      style={{
                        display: "block",
                        fontSize: "10px",
                        fontWeight: 700,
                        textTransform: "uppercase",
                        color: "var(--primary)",
                        marginBottom: "4px",
                      }}
                    >
                      Faculty Guidance Note
                    </span>
                    <span style={{ color: "var(--text)" }}>{supportSignal}</span>
                  </div>
                )}

                {/* Marks Card / Historical Semester Results Trigger */}
                <div style={{ marginTop: "4px" }}>
                  <button
                    className="export-banner-button"
                    style={{ width: "100%", justifyContent: "center" }}
                    onClick={() => setShowMarksCardModal(true)}
                    disabled={loadingDetail}
                  >
                    <FileText size={14} /> View Semester Marks Cards &amp; Historical Breakdown
                  </button>
                </div>
              </div>
            );
          })() : (
            <EmptyState icon={<Users size={20} />} title="No student selected" message="Select a row from the roster to inspect explainable risk signals." />
          )}
        </div>
      </div>

      {/* ── Marks Card & Academic Records Modal ────────────────────── */}
      {showMarksCardModal && selected && (() => {
        const profile = detailedProfile || selected;
        const isPortal = (profile?.data_source === "student_portal") || (selected?.data_source === "student_portal");
        const cgpa = detailedProfile?.academic_performance?.cgpa ?? profile?.cgpa;
        const latestSgpa = detailedProfile?.academic_performance?.latest_sgpa ?? profile?.latest_sgpa;

        return (
          <div
            className="modal-overlay"
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(0,0,0,0.75)",
              backdropFilter: "blur(6px)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 1000,
              padding: "20px",
            }}
            onClick={() => setShowMarksCardModal(false)}
          >
            <div
              className="marks-card-modal"
              style={{
                background: "#161f2c",
                border: "1px solid var(--border)",
                borderRadius: "12px",
                maxWidth: "800px",
                width: "100%",
                maxHeight: "85vh",
                overflowY: "auto",
                padding: "24px",
                boxShadow: "0 20px 40px rgba(0,0,0,0.5)",
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  marginBottom: "20px",
                  borderBottom: "1px solid var(--border)",
                  paddingBottom: "14px",
                }}
              >
                <div>
                  <h3 style={{ margin: "0 0 4px" }}>Academic Marks Cards — {profile?.name}</h3>
                  <span style={{ fontSize: "12px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                    USN: {profile?.usn} · CGPA: {cgpa ? Number(cgpa).toFixed(2) : "—"} · Completed Semesters:{" "}
                    {detailedProfile?.academic_performance?.completed_semesters || detailedProfile?.historical_semesters?.length || (isPortal ? 4 : 4)}
                  </span>
                </div>
                <button
                  onClick={() => setShowMarksCardModal(false)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "var(--text-muted)",
                    cursor: "pointer",
                    padding: "4px",
                  }}
                >
                  <X size={18} />
                </button>
              </div>

              {loadingDetail ? (
                <div className="ui-state">
                  <span>Loading marks card records...</span>
                </div>
              ) : detailedProfile?.historical_semesters && detailedProfile.historical_semesters.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  {detailedProfile.historical_semesters.map((sem, idx) => (
                    <div
                      key={idx}
                      style={{
                        border: "1px solid var(--border)",
                        borderRadius: "8px",
                        padding: "14px",
                        background: "rgba(255,255,255,0.02)",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "10px",
                          borderBottom: "1px solid rgba(255,255,255,0.06)",
                          paddingBottom: "8px",
                        }}
                      >
                        <strong style={{ fontSize: "14px", color: "var(--text)" }}>Semester {sem.semester}</strong>
                        <div style={{ display: "flex", gap: "12px", fontSize: "12px" }}>
                          <span>
                            SGPA: <strong style={{ color: "var(--primary)" }}>{sem.sgpa ? Number(sem.sgpa).toFixed(2) : "—"}</strong>
                          </span>
                          {sem.credits_earned && (
                            <span>
                              Credits: <strong>{sem.credits_earned}</strong>
                            </span>
                          )}
                          {sem.arrears !== undefined && (
                            <span>
                              Arrears:{" "}
                              <strong style={{ color: sem.arrears > 0 ? "var(--danger)" : "var(--primary)" }}>
                                {sem.arrears}
                              </strong>
                            </span>
                          )}
                        </div>
                      </div>

                      {sem.subjects && sem.subjects.length > 0 ? (
                        <div style={{ overflowX: "auto" }}>
                          <table style={{ width: "100%", fontSize: "12px", borderCollapse: "collapse" }}>
                            <thead>
                              <tr style={{ color: "var(--text-muted)", textAlign: "left", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                                <th style={{ padding: "6px 8px" }}>Subject Code</th>
                                <th style={{ padding: "6px 8px" }}>Subject Name</th>
                                <th style={{ padding: "6px 8px" }}>Marks %</th>
                                <th style={{ padding: "6px 8px" }}>Grade</th>
                                <th style={{ padding: "6px 8px" }}>Status</th>
                              </tr>
                            </thead>
                            <tbody>
                              {sem.subjects.map((sub, sidx) => (
                                <tr key={sidx} style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
                                  <td style={{ padding: "6px 8px", fontFamily: "monospace" }}>{sub.subject_code}</td>
                                  <td style={{ padding: "6px 8px" }}>{sub.subject_name}</td>
                                  <td style={{ padding: "6px 8px" }}>{sub.marks_percentage ? `${sub.marks_percentage}%` : "—"}</td>
                                  <td style={{ padding: "6px 8px", fontWeight: 700 }}>{sub.grade || "—"}</td>
                                  <td style={{ padding: "6px 8px" }}>
                                    <span
                                      style={{
                                        fontSize: "10px",
                                        fontWeight: 700,
                                        padding: "1px 6px",
                                        borderRadius: "4px",
                                        background: sub.is_backlog || sub.grade === "F" ? "rgba(231,111,111,0.15)" : "rgba(6,214,160,0.15)",
                                        color: sub.is_backlog || sub.grade === "F" ? "var(--danger)" : "var(--primary)",
                                      }}
                                    >
                                      {sub.is_backlog || sub.grade === "F" ? "ARREAR" : "PASS"}
                                    </span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                          Semester result recorded (SGPA: {sem.sgpa}). Detailed subject breakdown stored in portal archives.
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={<BookOpen size={20} />}
                  title={isPortal ? "Historical Records Archived" : "Marks Cards Not Available"}
                  message={
                    isPortal
                      ? `Cumulative CGPA ${cgpa || "—"} and latest SGPA ${latestSgpa || "—"} are authoritative from the university database.`
                      : "Marks Card details are not available for this demo student."
                  }
                />
              )}
            </div>
          </div>
        );
      })()}
    </div>
  );
}
