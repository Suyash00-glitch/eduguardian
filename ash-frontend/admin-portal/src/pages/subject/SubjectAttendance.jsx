import React, { useEffect, useState } from "react";
import { ClipboardCheck, Save } from "lucide-react";
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

  useEffect(() => {
    async function fetchRoster() {
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
        const res = await fetch(`http://127.0.0.1:8000/api/students/roster?${params}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        setStudents((data.students || []).map((s) => ({ ...s, present: true })));
      } catch (err) {
        console.error("failed to load roster:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchRoster();
  }, [active]);

  function toggle(id) {
    setStudents((prev) => prev.map((s) => (s.id === id ? { ...s, present: !s.present } : s)));
  }

  async function handleSave() {
    setSaving(true);
    try {
      const token = localStorage.getItem("token");
      // TODO backend: POST /api/attendance with { subject_code, department, semester, section, date, records }
      await fetch("http://127.0.0.1:8000/api/attendance", {
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
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error("failed to save attendance:", err);
    } finally {
      setSaving(false);
    }
  }

  const presentCount = students.filter((s) => s.present).length;

  return (
    <div className="subject-page">
      <div className="subject-header">
        <span className="dashboard-eyebrow">{active.subject_name?.toUpperCase()}</span>
        <h2>Mark Attendance</h2>
        <p>{active.department} · Semester {active.semester} · Section {active.section}</p>
      </div>

      <div className="teacher-panel">
        <div className="attendance-toolbar">
          <div className="attendance-toolbar-info">
            <ClipboardCheck size={16} />
            <span>{presentCount} / {students.length} present</span>
          </div>

          <div className="attendance-toolbar-actions">
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            <button className="attendance-save-button" onClick={handleSave} disabled={saving || loading}>
              <Save size={13} /> {saving ? "Saving..." : "Save Attendance"}
            </button>
          </div>
        </div>

        {saved && <div className="success-inline"><span>Attendance saved for {date}.</span></div>}

        {loading ? (
          <div className="ui-state"><span>Loading roster...</span></div>
        ) : students.length === 0 ? (
          <EmptyState icon={<ClipboardCheck size={20} />} title="No students found" message="This class has no enrolled students yet." />
        ) : (
          <div className="attendance-list">
            {students.map((s) => (
              <label key={s.id} className={`attendance-row ${s.present ? "present" : "absent"}`}>
                <input type="checkbox" checked={s.present} onChange={() => toggle(s.id)} />
                <span className="attendance-name">{s.usn} · {s.name}</span>
                <span className={`attendance-pill ${s.present ? "present" : "absent"}`}>
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
