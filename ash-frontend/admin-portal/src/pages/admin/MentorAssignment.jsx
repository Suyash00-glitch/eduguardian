import React, { useCallback, useEffect, useState } from "react";
import {
  UserCheck,
  UserPlus,
  Search,
  CheckCircle2,
  AlertCircle,
  Users,
  Shield,
  Layers,
  Sparkles,
  UserMinus,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTeacher } from "../../context/TeacherContext";
import { RiskBadge, EmptyState } from "../../components/shared/Shared";

function mentorStatus(load, max, isActive) {
  if (!isActive) return "inactive";
  if (load >= max) return "full";
  if (load >= max - 1) return "near-full";
  return "available";
}

export default function MentorAssignment() {
  const { active } = useTeacher();
  const navigate = useNavigate();

  const [mentors, setMentors] = useState([]);
  const [mentorLoading, setMentorLoading] = useState(false);
  const [selectedMentor, setSelectedMentor] = useState("");

  const [students, setStudents] = useState([]);
  const [studentLoading, setStudentLoading] = useState(false);
  const [studentSearch, setStudentSearch] = useState("");
  const [studentRiskFilter, setStudentRiskFilter] = useState("all");
  const [selectedStudent, setSelectedStudent] = useState(null);

  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  // Live Mentee Assignments list
  const [activeAssignments, setActiveAssignments] = useState([]);

  const fetchMentors = useCallback(async () => {
    setMentorLoading(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:5000/api/mentors", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      const list = (data.mentors || data.teachers || []).map((m) => ({
        ...m,
        current_load: m.current_load ?? 0,
        max_capacity: m.capacity ?? m.max_capacity ?? 5,
        is_active: m.is_active !== undefined ? m.is_active : true,
      }));
      setMentors(list);
      setSelectedMentor((prev) => {
        if (prev && list.some((t) => t.id === prev && t.current_load < t.max_capacity && t.is_active)) {
          return prev;
        }
        const firstAvail = list.find((t) => t.is_active && t.current_load < t.max_capacity);
        return firstAvail ? firstAvail.id : (list[0]?.id || "");
      });
    } catch (err) {
      console.error("failed to load mentors:", err);
    } finally {
      setMentorLoading(false);
    }
  }, []);

  const fetchStudents = useCallback(async () => {
    setStudentLoading(true);
    try {
      const token = localStorage.getItem("token");
      const params = new URLSearchParams({
        department: active?.department || "ISE",
        semester: String(active?.semester || 5),
        section: active?.section || "A",
        page: "1",
        page_size: "200",
        risk: "all",
      });
      const res = await fetch(`http://localhost:5000/api/students/roster?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setStudents(data.students || []);
    } catch (err) {
      console.error("failed to load students:", err);
    } finally {
      setStudentLoading(false);
    }
  }, [active]);

  const fetchMenteesList = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:5000/api/mentors/me/students", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setActiveAssignments(data.mentees || data.students || []);
      }
    } catch (e) {
      console.warn("Could not load mentee assignments:", e);
    }
  }, []);

  useEffect(() => {
    fetchMentors();
    fetchStudents();
    fetchMenteesList();
  }, [fetchMentors, fetchStudents, fetchMenteesList]);

  const filteredStudents = students.filter((s) => {
    const matchesSearch =
      (s.name || "").toLowerCase().includes(studentSearch.toLowerCase()) ||
      (s.usn || "").toLowerCase().includes(studentSearch.toLowerCase());
    const matchesRisk =
      studentRiskFilter === "all" ||
      (s.risk_level || "").toLowerCase() === studentRiskFilter.toLowerCase();
    return matchesSearch && matchesRisk;
  });

  async function handleAssign(e) {
    e.preventDefault();
    if (!selectedStudent) {
      setError("Please select a student to assign.");
      return;
    }
    if (!selectedMentor) {
      setError("Please select a mentor.");
      return;
    }

    const mentor = mentors.find((m) => m.id === selectedMentor);
    if (!mentor) return;

    if (!mentor.is_active) {
      setError(`Mentor ${mentor.full_name || mentor.name} is currently inactive.`);
      return;
    }

    if (mentor.current_load >= mentor.max_capacity) {
      setError(`Mentor ${mentor.full_name || mentor.name} is at full capacity (${mentor.current_load}/${mentor.max_capacity}).`);
      return;
    }

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:5000/api/mentors/assign", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ student_id: selectedStudent, mentor_id: selectedMentor }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.message || "Assignment failed.");

      const st = students.find((s) => s.id === selectedStudent);
      setSuccess(`Student ${st?.name || ""} (${st?.usn || ""}) successfully assigned to ${mentor.full_name || mentor.name}!`);
      setSelectedStudent(null);
      await Promise.all([fetchMentors(), fetchStudents(), fetchMenteesList()]);
      setTimeout(() => setSuccess(""), 5000);
    } catch (err) {
      setError(err.message || "Could not assign mentor.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleUnassign(assignmentId, studentName) {
    if (!window.confirm(`Unassign mentee ${studentName}?`)) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:5000/api/mentors/assignments/${assignmentId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to unassign.");
      await Promise.all([fetchMentors(), fetchMenteesList()]);
      setSuccess(`Mentee ${studentName} unassigned.`);
      setTimeout(() => setSuccess(""), 4000);
    } catch (err) {
      alert(err.message || "Failed to unassign.");
    }
  }

  return (
    <div className="mentor-page">
      {/* HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
        <div>
          <span className="dashboard-eyebrow">HUMAN-IN-THE-LOOP</span>
          <h2>Mentor Assignment</h2>
          <p>{active?.department || "ISE"} · Semester {active?.semester || 5} · Section {active?.section || "A"}</p>
        </div>
        <button
          type="button"
          onClick={() => navigate("/mentor-management")}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            background: "rgba(99, 102, 241, 0.15)",
            color: "#a5b4fc",
            border: "1px solid rgba(99, 102, 241, 0.3)",
            borderRadius: "8px",
            padding: "8px 14px",
            fontSize: "12px",
            fontWeight: 600,
            cursor: "pointer"
          }}
        >
          <Users size={14} />
          <span>Manage Mentor Roster →</span>
        </button>
      </div>

      {success && (
        <div style={{
          background: "rgba(16, 185, 129, 0.15)",
          border: "1px solid rgba(16, 185, 129, 0.4)",
          color: "#34d399",
          padding: "12px 16px",
          borderRadius: "8px",
          marginBottom: "16px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          fontSize: "13px"
        }}>
          <CheckCircle2 size={16} />
          <span>{success}</span>
        </div>
      )}

      {error && (
        <div style={{
          background: "rgba(239, 68, 68, 0.15)",
          border: "1px solid rgba(239, 68, 68, 0.4)",
          color: "#f87171",
          padding: "12px 16px",
          borderRadius: "8px",
          marginBottom: "16px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          fontSize: "13px"
        }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* TWO COLUMN WORKBENCH */}
      <div className="mentor-grid">
        {/* LEFT: MENTOR AVAILABILITY */}
        <div className="teacher-panel">
          <div className="teacher-panel-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3><UserCheck size={14} className="inline-icon" /> Mentor Availability</h3>
            <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.5)" }}>
              {mentors.filter((m) => m.is_active).length} Active Mentors
            </span>
          </div>

          {mentorLoading ? (
            <div className="ui-state"><span>Loading dynamic mentors...</span></div>
          ) : mentors.length === 0 ? (
            <EmptyState
              icon={<UserCheck size={20} />}
              title="No mentors registered"
              message="Go to Mentor Management to add faculty mentors."
            />
          ) : (
            <div className="mentor-list" style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {mentors.map((m) => {
                const status = mentorStatus(m.current_load, m.max_capacity, m.is_active);
                return (
                  <div
                    className="mentor-row"
                    key={m.id}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "12px 16px",
                      background: "rgba(255, 255, 255, 0.02)",
                      border: "1px solid rgba(255, 255, 255, 0.06)",
                      borderRadius: "8px"
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <strong style={{ color: "#fff", fontSize: "13px" }}>{m.full_name || m.name}</strong>
                      </div>
                      <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.6)", marginTop: "2px" }}>
                        <span>{m.employee_id}</span> · <span>{m.designation || "Assistant Professor"} · {m.department}</span>
                      </div>
                    </div>

                    <span className={`mentor-load-badge ${status}`} style={{ fontSize: "11px", fontWeight: 700 }}>
                      {m.current_load} / {m.max_capacity} mentees
                      {status === "inactive"
                        ? " · Inactive"
                        : status === "full"
                        ? " · FULL"
                        : status === "near-full"
                        ? " · NEAR FULL"
                        : " · AVAILABLE"}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* RIGHT: ASSIGN MENTOR */}
        <div className="teacher-panel">
          <div className="teacher-panel-header">
            <h3><UserPlus size={14} className="inline-icon" /> Assign Mentor</h3>
          </div>

          <form onSubmit={handleAssign} className="mentor-form">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
              <label style={{ margin: 0 }}>Step 1: Select Student</label>
              <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.5)" }}>
                {filteredStudents.length} available
              </span>
            </div>

            <div className="mentor-search-row">
              <div className="mentor-search-input">
                <Search size={13} />
                <input
                  type="text"
                  placeholder="Search student by Name or USN..."
                  value={studentSearch}
                  onChange={(e) => setStudentSearch(e.target.value)}
                />
              </div>
              <select value={studentRiskFilter} onChange={(e) => setStudentRiskFilter(e.target.value)}>
                <option value="all">All Risks</option>
                <option value="high">High risk</option>
                <option value="medium">Medium risk</option>
                <option value="low">Low risk</option>
              </select>
            </div>

            {studentLoading ? (
              <div className="ui-state small"><span>Loading student roster...</span></div>
            ) : filteredStudents.length === 0 ? (
              <EmptyState
                icon={<UserCheck size={18} />}
                title="No students match criteria"
                message="Adjust your search or risk filter."
              />
            ) : (
              <div className="mentor-student-list" style={{ maxHeight: "240px", overflowY: "auto" }}>
                {filteredStudents.map((s) => {
                  const isPortal = s.data_source === "student_portal" || s.usn === "NNM24IS127" || s.usn === "NNM24IS172";
                  return (
                    <label
                      key={s.id}
                      className={`mentor-student-option${selectedStudent === s.id ? " active" : ""}`}
                      style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 12px" }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <input
                          type="radio"
                          name="student"
                          checked={selectedStudent === s.id}
                          onChange={() => setSelectedStudent(s.id)}
                        />
                        <div>
                          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <strong style={{ color: "#fff", fontSize: "13px" }}>{s.name}</strong>
                            <span style={{
                              background: isPortal ? "rgba(16, 185, 129, 0.15)" : "rgba(148, 163, 184, 0.15)",
                              color: isPortal ? "#34d399" : "#94a3b8",
                              fontSize: "9px",
                              fontWeight: 700,
                              padding: "2px 6px",
                              borderRadius: "4px"
                            }}>
                              {isPortal ? "PORTAL" : "DEMO"}
                            </span>
                          </div>
                          <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.6)" }}>
                            {s.usn} · CGPA: {s.cgpa || "—"}
                          </span>
                        </div>
                      </div>
                      <RiskBadge risk={s.risk_level} />
                    </label>
                  );
                })}
              </div>
            )}

            <div style={{ marginTop: "16px" }}>
              <label style={{ display: "block", marginBottom: "6px" }}>Step 2: Select Mentor</label>
              <select
                value={selectedMentor}
                onChange={(e) => setSelectedMentor(parseInt(e.target.value))}
                className="mentor-select"
                style={{ width: "100%", padding: "10px 12px", background: "rgba(255,255,255,0.05)", color: "#fff", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.12)" }}
              >
                {mentorLoading ? (
                  <option>Loading mentors...</option>
                ) : (
                  mentors.map((m) => {
                    const isFull = m.current_load >= m.max_capacity;
                    const isDisabled = !m.is_active || isFull;
                    return (
                      <option key={m.id} value={m.id} disabled={isDisabled}>
                        {m.full_name || m.name} ({m.current_load}/{m.max_capacity} mentees)
                        {!m.is_active ? " — [INACTIVE]" : (isFull ? " — [FULL]" : "")}
                      </option>
                    );
                  })
                )}
              </select>
            </div>

            <button
              type="submit"
              className="mentor-submit"
              disabled={!selectedStudent || !selectedMentor || submitting}
              style={{
                marginTop: "16px",
                width: "100%",
                background: "#6366f1",
                color: "#fff",
                border: "none",
                borderRadius: "8px",
                padding: "12px",
                fontSize: "13px",
                fontWeight: 600,
                cursor: !selectedStudent || !selectedMentor || submitting ? "not-allowed" : "pointer",
                opacity: !selectedStudent || !selectedMentor || submitting ? 0.6 : 1
              }}
            >
              {submitting ? "Assigning..." : "Confirm Mentor Assignment"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
