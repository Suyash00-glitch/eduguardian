import React, { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useTeacher } from "../../context/TeacherContext";
import { RiskBadge, EmptyState } from "../../components/shared/Shared";
import { Users } from "lucide-react";

export default function StudentRoster() {
  const { active } = useTeacher();

  const [students, setStudents] = useState([]);
  const [selected, setSelected] = useState(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [risk, setRisk] = useState("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [totalStudents, setTotalStudents] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  useEffect(() => {
    async function fetchStudents() {
      setLoading(true);
      setError("");
      try {
        const token = localStorage.getItem("token");
        const params = new URLSearchParams({
          department: active.department,
          semester: String(active.semester),
          section: active.section,
          page: String(page),
          page_size: String(pageSize),
          risk,
        });

        const res = await fetch(`http://127.0.0.1:8000/api/students/roster?${params}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error(`request failed: ${res.status}`);

        const data = await res.json();
        setStudents(data.students || []);
        setTotalStudents(data.total_students || 0);
        setTotalPages(data.total_pages || 0);
        setSelected(data.students?.[0] || null);
      } catch (err) {
        console.error(err);
        setError("Unable to load students");
      } finally {
        setLoading(false);
      }
    }
    fetchStudents();
  }, [active, page, risk]);

  return (
    <div className="roster-page">
      <div className="roster-header">
        <div>
          <span className="dashboard-eyebrow">STUDENT COHORT</span>
          <h2>Student Roster</h2>
          <p>{active.department} · Semester {active.semester} · Section {active.section}</p>
        </div>

        <select value={risk} onChange={(e) => { setRisk(e.target.value); setPage(1); }} className="roster-risk-select">
          <option value="all">All students</option>
          <option value="high">High risk</option>
          <option value="medium">Medium risk</option>
          <option value="low">Low risk</option>
        </select>
      </div>

      <div className="roster-grid">
        <div className="teacher-panel roster-table-panel">
          <div className="teacher-panel-header">
            <h3>Complete Roster</h3>
            <span className="teacher-panel-sub">{totalStudents} students</span>
          </div>

          {loading && <div className="ui-state"><span>Loading students...</span></div>}
          {error && <div className="ui-state"><span className="danger-text">{error}</span></div>}

          {!loading && !error && students.length === 0 && (
            <EmptyState icon={<Users size={20} />} title="No students found" message="Try a different risk filter." />
          )}

          {!loading && !error && students.length > 0 && (
            <div className="roster-table">
              <div className="roster-table-head">
                <span>Student</span>
                <span>Risk</span>
                <span>Attendance</span>
                <span>Quiz Avg</span>
              </div>
              {students.map((s) => (
                <button
                  key={s.id}
                  className={`roster-row${selected?.id === s.id ? " active" : ""}`}
                  onClick={() => setSelected(s)}
                >
                  <span className="roster-name">{s.usn} · {s.name}</span>
                  <RiskBadge risk={s.risk_level} />
                  <span>{s.attendance}%</span>
                  <span>{s.quiz_average}%</span>
                </button>
              ))}
            </div>
          )}

          {!loading && totalPages > 0 && (
            <div className="roster-pagination">
              <button disabled={page === 1} onClick={() => setPage(page - 1)}><ChevronLeft size={14} /></button>
              <span>Page {page} of {totalPages}</span>
              <button disabled={page === totalPages} onClick={() => setPage(page + 1)}><ChevronRight size={14} /></button>
            </div>
          )}
        </div>

        <div className="teacher-panel roster-detail-panel">
          {selected ? (
            <>
              <span className="dashboard-eyebrow">SELECTED STUDENT</span>
              <h3>{selected.name}</h3>
              <div className="roster-detail-rows">
                <div><span>USN</span><strong>{selected.usn}</strong></div>
                <div><span>Risk level</span><RiskBadge risk={selected.risk_level} /></div>
                <div><span>Attendance</span><strong>{selected.attendance}%</strong></div>
                <div><span>Quiz average</span><strong>{selected.quiz_average}%</strong></div>
              </div>
            </>
          ) : (
            <EmptyState icon={<Users size={20} />} title="No student selected" message="Select a row to see details." />
          )}
        </div>
      </div>
    </div>
  );
}
