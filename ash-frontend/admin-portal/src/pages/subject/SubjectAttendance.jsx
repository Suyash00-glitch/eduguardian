import React, { useEffect, useState, useCallback } from "react";
import { ClipboardCheck, Save, CheckSquare, Square, RefreshCw, CheckCircle2 } from "lucide-react";
import { useTeacher } from "../../context/TeacherContext";
import { EmptyState } from "../../components/shared/Shared";

export default function SubjectAttendance() {
  const { active } = useTeacher();
  const today = new Date().toISOString().split("T")[0];

  const [date, setDate] = useState(today);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const fetchRoster = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const params = new URLSearchParams({
        department: active.department,
        semester: String(active.semester),
        section: active.section,
        page: "1",
        page_size: "200",
        risk: "all",
      });
      const res = await fetch(`http://localhost:5000/api/students/roster?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setStudents((data.students || []).map((s) => ({ ...s, present: true })));
    } catch (err) {
      console.error("failed to load roster:", err);
    } finally {
      setLoading(false);
    }
  }, [active]);

  useEffect(() => {
    fetchRoster();
  }, [fetchRoster]);

  function toggle(id) {
    setStudents((prev) => prev.map((s) => (s.id === id ? { ...s, present: !s.present } : s)));
  }

  function markAll(present) {
    setStudents((prev) => prev.map((s) => ({ ...s, present })));
  }

  async function handleSave() {
    setSaving(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:5000/api/attendance", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          subject_code: active.subject_code,
          department: active.department,
          semester: active.semester,
          section: active.section,
          date,
          records: students.map((s) => ({ student_id: s.id, present: s.present })),
        }),
      });
      if (res.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 4000);
      }
    } catch (err) {
      console.error("failed to save attendance:", err);
    } finally {
      setSaving(false);
    }
  }

  const presentCount = students.filter((s) => s.present).length;
  const attendanceRate = students.length > 0 ? Math.round((presentCount / students.length) * 100) : 0;

  return (
    <div className="subject-page">
      <div className="subject-header" style={{ marginBottom: "20px" }}>
        <div>
          <h2 style={{ fontSize: "22px", fontWeight: 700, margin: 0 }}>
            Subject Attendance Log — {active.subject_name || active.subject_code}
          </h2>
          <p style={{ margin: "4px 0 0", color: "var(--text-secondary)", fontSize: "13px" }}>
            NMAMIT {active.department} · Semester {active.semester} · Section {active.section} · LH310
          </p>
        </div>
      </div>

      <div className="teacher-panel">
        <div className="attendance-toolbar" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingBottom: "16px", borderBottom: "1px solid var(--border)", marginBottom: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div className="attendance-toolbar-info" style={{ display: "flex", alignItems: "center", gap: "8px", background: "var(--surface-soft)", padding: "6px 14px", borderRadius: "8px", border: "1px solid var(--border)" }}>
              <ClipboardCheck size={16} style={{ color: "var(--primary)" }} />
              <span style={{ fontSize: "13px", fontWeight: 600 }}>
                {presentCount} / {students.length} Present ({attendanceRate}%)
              </span>
            </div>

            <div style={{ display: "flex", gap: "8px" }}>
              <button
                type="button"
                onClick={() => markAll(true)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 12px",
                  borderRadius: "6px",
                  border: "1px solid var(--border)",
                  background: "var(--surface)",
                  color: "var(--text)",
                  fontSize: "12px",
                  cursor: "pointer",
                }}
              >
                <CheckSquare size={13} style={{ color: "var(--primary)" }} /> All Present
              </button>
              <button
                type="button"
                onClick={() => markAll(false)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 12px",
                  borderRadius: "6px",
                  border: "1px solid var(--border)",
                  background: "var(--surface)",
                  color: "var(--text-muted)",
                  fontSize: "12px",
                  cursor: "pointer",
                }}
              >
                <Square size={13} /> Clear All
              </button>
            </div>
          </div>

          <div className="attendance-toolbar-actions" style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              style={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                padding: "7px 12px",
                color: "var(--text)",
                fontSize: "13px",
              }}
            />
            <button
              className="attendance-save-button"
              onClick={handleSave}
              disabled={saving || loading}
              style={{ height: "36px", padding: "0 16px", display: "flex", alignItems: "center", gap: "6px" }}
            >
              <Save size={14} /> {saving ? "Saving..." : "Save Log"}
            </button>
          </div>
        </div>

        {saved && (
          <div
            className="success-inline"
            style={{
              background: "rgba(0, 213, 155, 0.12)",
              border: "1px solid rgba(0, 213, 155, 0.3)",
              color: "var(--primary)",
              padding: "10px 16px",
              borderRadius: "8px",
              marginBottom: "16px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "13px",
            }}
          >
            <CheckCircle2 size={16} />
            <span>Attendance successfully recorded in PostgreSQL for <strong>{date}</strong>!</span>
          </div>
        )}

        {loading ? (
          <div className="ui-state">
            <div className="ui-spinner">Loading class roster...</div>
          </div>
        ) : students.length === 0 ? (
          <EmptyState
            icon={<ClipboardCheck size={24} />}
            title="No students found"
            message="No students currently enrolled in this subject section."
          />
        ) : (
          <div className="attendance-list" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "10px" }}>
            {students.map((s) => (
              <label
                key={s.id}
                className={`attendance-row ${s.present ? "present" : "absent"}`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "12px 16px",
                  borderRadius: "8px",
                  border: `1px solid ${s.present ? "rgba(0, 213, 155, 0.3)" : "rgba(239, 68, 68, 0.2)"}`,
                  background: s.present ? "rgba(0, 213, 155, 0.05)" : "rgba(239, 68, 68, 0.05)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <input
                    type="checkbox"
                    checked={s.present}
                    onChange={() => toggle(s.id)}
                    style={{ width: "16px", height: "16px", accentColor: "var(--primary)", cursor: "pointer" }}
                  />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: "13px", color: "var(--text)" }}>{s.name}</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{s.usn}</div>
                  </div>
                </div>
                <span
                  className={`attendance-pill ${s.present ? "present" : "absent"}`}
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    padding: "3px 8px",
                    borderRadius: "6px",
                    background: s.present ? "rgba(0, 213, 155, 0.15)" : "rgba(239, 68, 68, 0.15)",
                    color: s.present ? "#00d59b" : "#ef4444",
                  }}
                >
                  {s.present ? "Present" : "Absent"}
                </span>
              </label>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

