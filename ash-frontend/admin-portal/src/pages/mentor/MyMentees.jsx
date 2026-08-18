import React, { useEffect, useState } from "react";
import { HeartHandshake, ClipboardList } from "lucide-react";
import { RiskBadge, EmptyState } from "../../components/shared/Shared";

export default function MyMentees() {
  const [mentees, setMentees] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchMentees() {
      setLoading(true);
      setError("");
      try {
        const token = localStorage.getItem("token");

        // Backend contract:
        // GET /api/mentors/me/students
        // -> { mentees: [{
        //        assignment_id, student_id, usn, name,
        //        risk_level, reason, attendance, quiz_average,
        //        department, semester, section, assigned_at
        //      }] }
        const res = await fetch("http://127.0.0.1:8000/api/mentors/me/students", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error(`request failed: ${res.status}`);

        const data = await res.json();
        const list = data.mentees || [];
        setMentees(list);
        setSelected(list[0] || null);
      } catch (err) {
        console.error("failed to load mentees:", err);
        setError("Unable to load your mentees");
      } finally {
        setLoading(false);
      }
    }
    fetchMentees();
  }, []);

  return (
    <div className="mentees-page">
      <div className="mentees-header">
        <span className="dashboard-eyebrow">MENTORSHIP</span>
        <h2>My Mentees</h2>
        <p>Students currently assigned to you for one-on-one support.</p>
      </div>

      {loading && <div className="ui-state"><span>Loading your mentees...</span></div>}
      {error && <div className="ui-state"><span className="danger-text">{error}</span></div>}

      {!loading && !error && mentees.length === 0 && (
        <EmptyState
          icon={<HeartHandshake size={20} />}
          title="No mentees assigned yet"
          message="When a class admin assigns a student to you, they'll show up here."
        />
      )}

      {!loading && !error && mentees.length > 0 && (
        <div className="mentees-grid">
          <div className="teacher-panel mentees-list-panel">
            <div className="teacher-panel-header">
              <h3>Assigned Students</h3>
              <span className="teacher-panel-sub">{mentees.length} mentee{mentees.length !== 1 ? "s" : ""}</span>
            </div>

            <div className="mentees-list">
              {mentees.map((m) => (
                <button
                  key={m.assignment_id}
                  className={`mentee-row${selected?.assignment_id === m.assignment_id ? " active" : ""}`}
                  onClick={() => setSelected(m)}
                >
                  <div>
                    <strong>{m.name}</strong>
                    <span>{m.usn} · {m.department} Sem {m.semester} Sec {m.section}</span>
                  </div>
                  <RiskBadge risk={m.risk_level} />
                </button>
              ))}
            </div>
          </div>

          <div className="teacher-panel mentee-detail-panel">
            {selected ? (
              <>
                <span className="dashboard-eyebrow">SELECTED MENTEE</span>
                <h3>{selected.name}</h3>

                <div className="mentee-detail-rows">
                  <div><span>USN</span><strong>{selected.usn}</strong></div>
                  <div><span>Class</span><strong>{selected.department} · Sem {selected.semester} · Sec {selected.section}</strong></div>
                  <div><span>Risk level</span><RiskBadge risk={selected.risk_level} /></div>
                  <div><span>Attendance</span><strong>{selected.attendance}%</strong></div>
                  <div><span>Quiz average</span><strong>{selected.quiz_average}%</strong></div>
                  <div><span>Assigned on</span><strong>{selected.assigned_at ? new Date(selected.assigned_at).toLocaleDateString() : "—"}</strong></div>
                </div>

                {selected.reason && (
                  <div className="mentee-reason-box">
                    <ClipboardList size={14} className="inline-icon" />
                    <div>
                      <strong>Why this student was flagged</strong>
                      <p>{selected.reason}</p>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <EmptyState icon={<HeartHandshake size={20} />} title="No mentee selected" message="Select a student to see their details." />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
