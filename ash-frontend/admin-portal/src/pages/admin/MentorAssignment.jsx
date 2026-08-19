import React, { useCallback, useEffect, useState } from "react";
import { UserCheck, UserPlus, Search, CheckCircle2 } from "lucide-react";
import { useTeacher } from "../../context/TeacherContext";
import { RiskBadge, EmptyState } from "../../components/shared/Shared";

// fallback max capacity if the backend doesn't send max_capacity per mentor
const DEFAULT_MAX_CAPACITY = 5;

function mentorStatus(load, max) {
  if (load >= max) return "full";
  if (load >= max - 1) return "near-full";
  return "available";
}

export default function MentorAssignment() {
  const { active } = useTeacher();

  const [mentors, setMentors] = useState([]);
  const [mentorLoading, setMentorLoading] = useState(false);
  const [selectedMentor, setSelectedMentor] = useState("");

  const [riskStudents, setRiskStudents] = useState([]);
  const [studentLoading, setStudentLoading] = useState(false);
  const [studentSearch, setStudentSearch] = useState("");
  const [studentRiskFilter, setStudentRiskFilter] = useState("all");
  const [selectedStudent, setSelectedStudent] = useState(null);

  const [success, setSuccess] = useState(false);

  const fetchMentors = useCallback(async () => {
    setMentorLoading(true);
    try {
      const token = localStorage.getItem("token");
      // Backend contract expected:
      // GET /api/teachers -> { teachers: [{ id, full_name, employee_id, current_load, max_capacity }] }
      // current_load = count of active rows in mentor_assignments for this teacher
      const res = await fetch("http://127.0.0.1:8000/api/teachers", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      const teachers = (data.teachers || []).map((t) => ({
        ...t,
        current_load: t.current_load ?? 0,
        max_capacity: t.max_capacity ?? DEFAULT_MAX_CAPACITY,
      }));
      setMentors(teachers);
      setSelectedMentor((prev) => {
        if (prev && teachers.some((t) => t.id === prev)) return prev;
        const firstAvailable = teachers.find((t) => t.current_load < t.max_capacity);
        return firstAvailable ? firstAvailable.id : (teachers[0]?.id || "");
      });
    } catch (err) {
      console.error("failed to load teachers:", err);
    } finally {
      setMentorLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMentors();
  }, [fetchMentors]);

  useEffect(() => {
    async function fetchRiskStudents() {
      setStudentLoading(true);
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
        const needHelp = (data.students || []).filter(
          (s) => s.risk_level?.toLowerCase() === "high" || s.risk_level?.toLowerCase() === "medium"
        );
        setRiskStudents(needHelp);
      } catch (err) {
        console.error("failed to load risk students:", err);
      } finally {
        setStudentLoading(false);
      }
    }
    fetchRiskStudents();
  }, [active]);

  const filteredStudents = riskStudents.filter((s) => {
    const matchesSearch =
      s.name?.toLowerCase().includes(studentSearch.toLowerCase()) ||
      s.usn?.toLowerCase().includes(studentSearch.toLowerCase());
    const matchesRisk = studentRiskFilter === "all" || s.risk_level?.toLowerCase() === studentRiskFilter;
    return matchesSearch && matchesRisk;
  });

  async function handleAssign(e) {
    e.preventDefault();

    const mentor = mentors.find((m) => m.id === selectedMentor);
    if (mentor && mentor.current_load >= mentor.max_capacity) {
      alert(`${mentor.full_name} is already at full capacity (${mentor.max_capacity}/${mentor.max_capacity}). Pick another mentor.`);
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://127.0.0.1:8000/api/mentors/assign", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ student_id: selectedStudent, mentor_id: selectedMentor }),
      });
      if (!res.ok) throw new Error("assignment failed");

      setSuccess(true);
      setSelectedStudent(null);
      await fetchMentors(); // pull fresh load counts so the badge updates immediately
      setTimeout(() => setSuccess(false), 4000);
    } catch (err) {
      console.error(err);
      alert("Could not assign mentor. Check backend connection.");
    }
  }

  return (
    <div className="mentor-page">
      <div className="mentor-header">
        <span className="dashboard-eyebrow">HUMAN-IN-THE-LOOP</span>
        <h2>Mentor Assignment</h2>
        <p>{active.department} · Semester {active.semester} · Section {active.section}</p>
      </div>

      <div className="mentor-grid">
        <div className="teacher-panel">
          <div className="teacher-panel-header">
            <h3><UserCheck size={14} className="inline-icon" /> Live Mentor Availability</h3>
          </div>

          {mentorLoading ? (
            <div className="ui-state"><span>Loading mentors...</span></div>
          ) : mentors.length === 0 ? (
            <EmptyState icon={<UserCheck size={20} />} title="No teachers found" message="Add teachers to assign as mentors." />
          ) : (
            <div className="mentor-list">
              {mentors.map((m) => {
                const status = mentorStatus(m.current_load, m.max_capacity);
                return (
                  <div className="mentor-row" key={m.id}>
                    <div>
                      <strong>{m.full_name}</strong>
                      <span>Employee ID: {m.employee_id || "N/A"}</span>
                    </div>
                    <span className={`mentor-load-badge ${status}`}>
                      {m.current_load} / {m.max_capacity}
                      {status === "full" ? " · Full" : status === "near-full" ? " · Nearly full" : " · Available"}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="teacher-panel">
          <div className="teacher-panel-header">
            <h3><UserPlus size={14} className="inline-icon" /> Assign Mentor</h3>
          </div>

          {success && (
            <div className="success-inline">
              <CheckCircle2 size={15} />
              <span>Mentor assigned successfully! Intervention logged.</span>
            </div>
          )}

          <form onSubmit={handleAssign} className="mentor-form">
            <label>Select student</label>

            <div className="mentor-search-row">
              <div className="mentor-search-input">
                <Search size={13} />
                <input
                  type="text"
                  placeholder="Search name or USN..."
                  value={studentSearch}
                  onChange={(e) => setStudentSearch(e.target.value)}
                />
              </div>
              <select value={studentRiskFilter} onChange={(e) => setStudentRiskFilter(e.target.value)}>
                <option value="all">All</option>
                <option value="high">High risk</option>
                <option value="medium">Medium risk</option>
              </select>
            </div>

            {studentLoading ? (
              <div className="ui-state small"><span>Loading students...</span></div>
            ) : filteredStudents.length === 0 ? (
              <EmptyState icon={<UserCheck size={18} />} title="No students need mentoring" message="Nobody in this class currently needs intervention." />
            ) : (
              <div className="mentor-student-list">
                {filteredStudents.map((s) => (
                  <label
                    key={s.id}
                    className={`mentor-student-option${selectedStudent === s.id ? " active" : ""}`}
                  >
                    <input
                      type="radio"
                      name="student"
                      checked={selectedStudent === s.id}
                      onChange={() => setSelectedStudent(s.id)}
                    />
                    <div>
                      <strong>{s.name}</strong>
                      <span>{s.usn}</span>
                    </div>
                    <RiskBadge risk={s.risk_level} />
                  </label>
                ))}
              </div>
            )}

            <label>Select mentor</label>
            <select value={selectedMentor} onChange={(e) => setSelectedMentor(e.target.value)} className="mentor-select">
              {mentorLoading ? (
                <option>Loading teachers...</option>
              ) : (
                mentors.map((m) => (
                  <option key={m.id} value={m.id} disabled={m.current_load >= m.max_capacity}>
                    {m.full_name} ({m.current_load}/{m.max_capacity}{m.current_load >= m.max_capacity ? " — Full" : ""})
                  </option>
                ))
              )}
            </select>

            <button type="submit" className="mentor-submit" disabled={!selectedStudent}>
              Confirm Mentor Assignment
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
