import React, { useEffect, useState, useCallback } from "react";
import { GraduationCap, Save, CheckCircle2, Award, Sparkles, RefreshCw } from "lucide-react";
import { useTeacher } from "../../context/TeacherContext";
import { EmptyState } from "../../components/shared/Shared";

export default function SubjectMarks() {
  const { active } = useTeacher();

  const [quizName, setQuizName] = useState("Internal Assessment 1");
  const [maxMarks, setMaxMarks] = useState(50);
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
      setStudents((data.students || []).map((s) => ({ ...s, marks: "" })));
    } catch (err) {
      console.error("failed to load roster:", err);
    } finally {
      setLoading(false);
    }
  }, [active]);

  useEffect(() => {
    fetchRoster();
  }, [fetchRoster]);

  function setMark(id, value) {
    setStudents((prev) => prev.map((s) => (s.id === id ? { ...s, marks: value } : s)));
  }

  async function handleSave() {
    if (!quizName.trim()) return;
    setSaving(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:5000/api/quiz-results", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          subject_code: active.subject_code,
          department: active.department,
          semester: active.semester,
          section: active.section,
          quiz_name: quizName,
          max_marks: Number(maxMarks),
          results: students.map((s) => ({ student_id: s.id, marks_obtained: Number(s.marks) || 0 })),
        }),
      });
      if (res.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 4000);
      }
    } catch (err) {
      console.error("failed to save marks:", err);
    } finally {
      setSaving(false);
    }
  }

  const enteredCount = students.filter((s) => s.marks !== "").length;

  return (
    <div className="subject-page">
      <div className="subject-header" style={{ marginBottom: "20px" }}>
        <div>
          <h2 style={{ fontSize: "22px", fontWeight: 700, margin: 0 }}>
            Marks &amp; Assessments — {active.subject_name || active.subject_code}
          </h2>
          <p style={{ margin: "4px 0 0", color: "var(--text-secondary)", fontSize: "13px" }}>
            Record Quiz, Lab Assessment, and Internal Test scores for <strong>NMAMIT {active.department} Sem {active.semester} ({active.section})</strong>
          </p>
        </div>
      </div>

      <div className="teacher-panel">
        <div
          className="marks-toolbar"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            paddingBottom: "16px",
            borderBottom: "1px solid var(--border)",
            marginBottom: "16px",
            gap: "12px",
            flexWrap: "wrap",
          }}
        >
          <div style={{ display: "flex", gap: "12px", alignItems: "center", flex: 1 }}>
            <input
              type="text"
              placeholder="e.g. IA-1, Quiz 2, Lab Evaluation..."
              value={quizName}
              onChange={(e) => setQuizName(e.target.value)}
              style={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                padding: "8px 14px",
                color: "var(--text)",
                fontSize: "13px",
                minWidth: "220px",
              }}
            />
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>Max Marks:</span>
              <input
                type="number"
                value={maxMarks}
                onChange={(e) => setMaxMarks(e.target.value)}
                style={{
                  width: "70px",
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  padding: "8px 10px",
                  color: "var(--text)",
                  fontSize: "13px",
                  textAlign: "center",
                }}
              />
            </div>
            <span style={{ fontSize: "12px", color: "var(--text-secondary)", background: "var(--surface-soft)", padding: "6px 12px", borderRadius: "6px" }}>
              {enteredCount} / {students.length} entered
            </span>
          </div>

          <button
            className="attendance-save-button"
            onClick={handleSave}
            disabled={saving || loading || !quizName.trim()}
            style={{ height: "36px", padding: "0 16px", display: "flex", alignItems: "center", gap: "6px" }}
          >
            <Save size={14} /> {saving ? "Saving..." : "Save Assessment Marks"}
          </button>
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
            <span>Marks for <strong>{quizName}</strong> saved successfully into database!</span>
          </div>
        )}

        {loading ? (
          <div className="ui-state">
            <div className="ui-spinner">Loading student roster...</div>
          </div>
        ) : students.length === 0 ? (
          <EmptyState
            icon={<GraduationCap size={24} />}
            title="No students found"
            message="This class has no enrolled students yet."
          />
        ) : (
          <div className="marks-table-wrap" style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1.5px solid var(--border)", background: "var(--surface-soft)" }}>
                  <th style={{ padding: "12px 16px", fontSize: "12px", color: "var(--text-muted)", textTransform: "uppercase" }}>USN</th>
                  <th style={{ padding: "12px 16px", fontSize: "12px", color: "var(--text-muted)", textTransform: "uppercase" }}>Student Name</th>
                  <th style={{ padding: "12px 16px", fontSize: "12px", color: "var(--text-muted)", textTransform: "uppercase" }}>Marks Obtained (/{maxMarks})</th>
                  <th style={{ padding: "12px 16px", fontSize: "12px", color: "var(--text-muted)", textTransform: "uppercase" }}>Percentage</th>
                </tr>
              </thead>
              <tbody>
                {students.map((s, idx) => {
                  const m = Number(s.marks);
                  const pct = s.marks !== "" && maxMarks > 0 ? Math.round((m / maxMarks) * 100) : null;
                  return (
                    <tr
                      key={s.id}
                      style={{
                        borderBottom: "1px solid var(--border)",
                        background: idx % 2 === 0 ? "transparent" : "rgba(255,255,255,0.01)",
                      }}
                    >
                      <td style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 600, color: "var(--text-muted)" }}>{s.usn}</td>
                      <td style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 600, color: "var(--text)" }}>{s.name}</td>
                      <td style={{ padding: "12px 16px" }}>
                        <input
                          type="number"
                          min="0"
                          max={maxMarks}
                          value={s.marks}
                          onChange={(e) => setMark(s.id, e.target.value)}
                          placeholder="—"
                          style={{
                            width: "100px",
                            background: "var(--surface)",
                            border: "1px solid var(--border)",
                            borderRadius: "6px",
                            padding: "6px 12px",
                            color: "var(--text)",
                            fontSize: "13px",
                            outline: "none",
                          }}
                        />
                      </td>
                      <td style={{ padding: "12px 16px", fontSize: "13px" }}>
                        {pct !== null ? (
                          <span style={{ fontWeight: 700, color: pct >= 75 ? "#00d59b" : pct >= 50 ? "#f59e0b" : "#ef4444" }}>
                            {pct}%
                          </span>
                        ) : (
                          <span style={{ color: "var(--text-muted)" }}>—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

