import React, { useEffect, useState, useCallback } from "react";
import {
  HeartHandshake,
  ClipboardList,
  Mail,
  GraduationCap,
  Calendar,
  AlertTriangle,
  UserX,
  FileText,
  Sparkles,
  BookOpen,
} from "lucide-react";
import { RiskBadge, EmptyState } from "../../components/shared/Shared";

export default function MyMentees() {
  const [mentees, setMentees] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [unassigning, setUnassigning] = useState(false);

  const fetchMentees = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:5000/api/mentors/me/students", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Request failed with status ${res.status}`);

      const data = await res.json();
      const list = data.mentees || data.students || [];
      setMentees(list);
      setSelected((prev) => {
        if (prev && list.some((m) => m.assignment_id === prev.assignment_id)) {
          return list.find((m) => m.assignment_id === prev.assignment_id);
        }
        return list[0] || null;
      });
    } catch (err) {
      console.error("failed to load mentees:", err);
      setError("Unable to load your assigned mentees.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMentees();
  }, [fetchMentees]);

  async function handleUnassign(assignmentId, studentName) {
    if (!window.confirm(`Release/unassign mentee "${studentName}"?`)) return;
    setUnassigning(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:5000/api/mentors/assignments/${assignmentId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to release mentee.");
      await fetchMentees();
    } catch (e) {
      alert(e.message || "Failed to unassign mentee.");
    } finally {
      setUnassigning(false);
    }
  }

  return (
    <div className="mentees-page">
      <div className="mentees-header" style={{ marginBottom: "20px" }}>
        <span className="dashboard-eyebrow">FACULTY MENTORSHIP</span>
        <h2>My Mentees</h2>
        <p style={{ color: "rgba(255,255,255,0.6)", fontSize: "13px", marginTop: "4px" }}>
          Students currently assigned to you for 1-on-1 academic mentoring and intervention.
        </p>
      </div>

      {loading && <div className="ui-state"><span>Loading your assigned mentees...</span></div>}
      {error && <div className="ui-state"><span className="danger-text">{error}</span></div>}

      {!loading && !error && mentees.length === 0 && (
        <EmptyState
          icon={<HeartHandshake size={24} />}
          title="No mentees assigned yet"
          message="When students are assigned to you via Mentor Assignment, they will appear here."
        />
      )}

      {!loading && !error && mentees.length > 0 && (
        <div className="mentees-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1.4fr", gap: "20px" }}>
          {/* LEFT: MENTEES LIST */}
          <div className="teacher-panel mentees-list-panel">
            <div className="teacher-panel-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3>Assigned Mentees</h3>
              <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.5)", fontWeight: 600 }}>
                {mentees.length} Active Mentee{mentees.length !== 1 ? "s" : ""}
              </span>
            </div>

            <div className="mentees-list" style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {mentees.map((m) => {
                const isPortal = m.data_source === "student_portal" || m.usn === "NNM24IS127" || m.usn === "NNM24IS172";
                const isSelected = selected?.assignment_id === m.assignment_id;

                return (
                  <button
                    key={m.assignment_id}
                    className={`mentee-row${isSelected ? " active" : ""}`}
                    onClick={() => setSelected(m)}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "12px 14px",
                      background: isSelected ? "rgba(99, 102, 241, 0.15)" : "rgba(255, 255, 255, 0.02)",
                      border: `1px solid ${isSelected ? "rgba(99, 102, 241, 0.4)" : "rgba(255, 255, 255, 0.06)"}`,
                      borderRadius: "8px",
                      cursor: "pointer",
                      textAlign: "left"
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <strong style={{ color: "#fff", fontSize: "13px" }}>{m.name}</strong>
                        <span style={{
                          background: isPortal ? "rgba(16, 185, 129, 0.15)" : "rgba(148, 163, 184, 0.15)",
                          color: isPortal ? "#34d399" : "#94a3b8",
                          fontSize: "9px",
                          fontWeight: 700,
                          padding: "2px 5px",
                          borderRadius: "4px"
                        }}>
                          {isPortal ? "PORTAL" : "DEMO"}
                        </span>
                      </div>
                      <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.6)", marginTop: "2px", display: "block" }}>
                        {m.usn} · {m.department} Sem {m.semester} Sec {m.section}
                      </span>
                    </div>
                    <RiskBadge risk={m.risk_level} />
                  </button>
                );
              })}
            </div>
          </div>

          {/* RIGHT: MENTEE DETAIL CARD */}
          <div className="teacher-panel mentee-detail-panel" style={{ padding: "24px" }}>
            {selected ? (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
                  <div>
                    <span className="dashboard-eyebrow">MENTEE PROFILE &amp; ACADEMIC RECORD</span>
                    <h3 style={{ fontSize: "20px", fontWeight: 700, color: "#fff", margin: "4px 0" }}>
                      {selected.name}
                    </h3>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "4px" }}>
                      <span style={{ fontSize: "12px", color: "rgba(255,255,255,0.7)" }}>
                        USN: <strong>{selected.usn}</strong>
                      </span>
                      <span style={{ color: "rgba(255,255,255,0.3)" }}>•</span>
                      <span style={{
                        background: selected.data_source === "student_portal" ? "rgba(16, 185, 129, 0.15)" : "rgba(148, 163, 184, 0.15)",
                        color: selected.data_source === "student_portal" ? "#34d399" : "#94a3b8",
                        fontSize: "10px",
                        fontWeight: 700,
                        padding: "2px 8px",
                        borderRadius: "4px"
                      }}>
                        {selected.data_source === "student_portal" ? "UNIVERSITY PORTAL RECORD" : "DEMO RECORD"}
                      </span>
                    </div>
                  </div>

                  <RiskBadge risk={selected.risk_level} />
                </div>

                {/* METRICS GRID */}
                <div style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(3, 1fr)",
                  gap: "12px",
                  marginBottom: "20px"
                }}>
                  <div style={{ background: "rgba(255,255,255,0.03)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                    <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.5)", display: "block" }}>Cumulative CGPA</span>
                    <strong style={{ fontSize: "16px", color: "#fff" }}>{selected.cgpa ?? "—"}</strong>
                  </div>
                  <div style={{ background: "rgba(255,255,255,0.03)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                    <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.5)", display: "block" }}>Latest SGPA</span>
                    <strong style={{ fontSize: "16px", color: "#fff" }}>{selected.latest_sgpa ?? "—"}</strong>
                  </div>
                  <div style={{ background: "rgba(255,255,255,0.03)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                    <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.5)", display: "block" }}>Active Backlogs</span>
                    <strong style={{ fontSize: "16px", color: selected.backlogs > 0 ? "#f87171" : "#34d399" }}>
                      {selected.backlogs ?? 0}
                    </strong>
                  </div>
                </div>

                {/* REASON / SUPPORT SIGNAL */}
                {selected.reason && (
                  <div style={{
                    background: "rgba(99, 102, 241, 0.08)",
                    border: "1px solid rgba(99, 102, 241, 0.25)",
                    borderRadius: "8px",
                    padding: "14px",
                    marginBottom: "20px",
                    display: "flex",
                    gap: "10px",
                    alignItems: "flex-start"
                  }}>
                    <ClipboardList size={16} color="#a5b4fc" style={{ marginTop: "2px", flexShrink: 0 }} />
                    <div>
                      <strong style={{ fontSize: "12px", color: "#a5b4fc", display: "block", marginBottom: "4px" }}>
                        Mentorship Signal &amp; Focus Area
                      </strong>
                      <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.85)", margin: 0 }}>
                        {selected.reason}
                      </p>
                    </div>
                  </div>
                )}

                {/* DETAILS LIST */}
                <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "13px", marginBottom: "24px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.06)", paddingBottom: "8px" }}>
                    <span style={{ color: "rgba(255,255,255,0.5)" }}>Enrolled Program</span>
                    <strong style={{ color: "#fff" }}>{selected.department} · Semester {selected.semester} · Section {selected.section}</strong>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.06)", paddingBottom: "8px" }}>
                    <span style={{ color: "rgba(255,255,255,0.5)" }}>Mentorship Status</span>
                    <span style={{ color: "#34d399", fontWeight: 600 }}>Active (Assigned)</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.06)", paddingBottom: "8px" }}>
                    <span style={{ color: "rgba(255,255,255,0.5)" }}>Assigned Date</span>
                    <strong style={{ color: "#fff" }}>
                      {selected.assigned_at ? new Date(selected.assigned_at).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" }) : "Active Session"}
                    </strong>
                  </div>
                </div>

                {/* ACTIONS */}
                <div style={{ display: "flex", gap: "10px" }}>
                  <button
                    type="button"
                    onClick={() => handleUnassign(selected.assignment_id, selected.name)}
                    disabled={unassigning}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      background: "rgba(239, 68, 68, 0.1)",
                      border: "1px solid rgba(239, 68, 68, 0.3)",
                      color: "#f87171",
                      borderRadius: "6px",
                      padding: "8px 14px",
                      fontSize: "12px",
                      cursor: "pointer"
                    }}
                  >
                    <UserX size={14} />
                    <span>{unassigning ? "Releasing..." : "Release Mentee"}</span>
                  </button>
                </div>
              </div>
            ) : (
              <EmptyState
                icon={<HeartHandshake size={20} />}
                title="No mentee selected"
                message="Select a student from the list to view their detailed academic profile."
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
