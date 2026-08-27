import React, { useEffect, useState } from "react";
import { GraduationCap, Save } from "lucide-react";
import { useTeacher } from "../../context/TeacherContext";
import { EmptyState } from "../../components/shared/Shared";

export default function SubjectMarks() {
  const { active } = useTeacher();

  const [quizName, setQuizName] = useState("");
  const [maxMarks, setMaxMarks] = useState(100);
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
    }
    fetchRoster();
  }, [active]);

  function setMark(id, value) {
    setStudents((prev) => prev.map((s) => (s.id === id ? { ...s, marks: value } : s)));
  }

  async function handleSave() {
    setSaving(true);
    try {
      const token = localStorage.getItem("token");
      // TODO backend: POST /api/quiz-results
      await fetch("http://localhost:5000/api/quiz-results", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          subject_code: active.subject_code,
          department: active.department,
          semester: active.semester,
          section: active.section,
          quiz_name: quizName,
          max_marks: maxMarks,
          results: students.map((s) => ({ student_id: s.id, marks_obtained: Number(s.marks) || 0 })),
        }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error("failed to save marks:", err);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="subject-page">
      <div className="subject-header">
        <span className="dashboard-eyebrow">{active.subject_name?.toUpperCase()}</span>
        <h2>Marks &amp; Quizzes</h2>
        <p>{active.department} · Semester {active.semester} · Section {active.section}</p>
      </div>

      <div className="teacher-panel">
        <div className="marks-toolbar">
          <input
            type="text"
            placeholder="Quiz / exam name"
            value={quizName}
            onChange={(e) => setQuizName(e.target.value)}
            className="marks-quiz-name"
          />
          <div className="marks-max">
            <span>Max marks</span>
            <input type="number" value={maxMarks} onChange={(e) => setMaxMarks(e.target.value)} />
          </div>
          <button className="attendance-save-button" onClick={handleSave} disabled={saving || loading || !quizName}>
            <Save size={13} /> {saving ? "Saving..." : "Save Marks"}
          </button>
        </div>

        {saved && <div className="success-inline"><span>Marks saved for {quizName}.</span></div>}

        {loading ? (
          <div className="ui-state"><span>Loading roster...</span></div>
        ) : students.length === 0 ? (
          <EmptyState icon={<GraduationCap size={20} />} title="No students found" message="This class has no enrolled students yet." />
        ) : (
          <div className="marks-list">
            <div className="marks-list-head">
              <span>Student</span>
              <span>Marks obtained</span>
            </div>
            {students.map((s) => (
              <div className="marks-row" key={s.id}>
                <span>{s.usn} · {s.name}</span>
                <input
                  type="number"
                  min="0"
                  max={maxMarks}
                  value={s.marks}
                  onChange={(e) => setMark(s.id, e.target.value)}
                  placeholder="—"
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
