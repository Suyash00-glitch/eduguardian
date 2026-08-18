import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ClipboardList, Plus, X } from "lucide-react";
import { useTeacher } from "../../context/TeacherContext";
import { EmptyState } from "../../components/shared/Shared";

export default function SubjectAssignments() {
  const { active } = useTeacher();
  const navigate = useNavigate();

  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [name, setName] = useState("");
  const [maxMarks, setMaxMarks] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [resource, setResource] = useState(null);

  useEffect(() => {
    async function fetchAssignments() {
      setLoading(true);
      try {
        const token = localStorage.getItem("token");
        const params = new URLSearchParams({
          department: active.department,
          semester: String(active.semester),
          section: active.section,
          subject_code: active.subject_code,
        });
        // TODO backend: GET /api/assignments?department=&semester=&section=&subject_code=
        const res = await fetch(`http://127.0.0.1:8000/api/assignments?${params}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) {
  throw new Error(`fetch assignments failed: ${res.status}`);
}

        const data = await res.json();
        setAssignments(data.assignments || []);
      } catch (err) {
        console.error("failed to load assignments:", err);
        setAssignments([]);
      } finally {
        setLoading(false);
      }
    }
    fetchAssignments();
  }, [active]);

  async function handleCreate(e) {
  e.preventDefault();

  try {
    const token = localStorage.getItem("token");

    const formData = new FormData();

    formData.append("department", active.department);
    formData.append("semester", active.semester);
    formData.append("section", active.section);
    formData.append("subject_code", active.subject_code);

    formData.append("assignment_name", name);
    formData.append("max_marks", maxMarks);
    formData.append("due_date", dueDate);

    if (resource) {
      formData.append("resource", resource);
    }

    const res = await fetch(
      "http://127.0.0.1:8000/api/assignments",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      }
    );

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));

      throw new Error(
        errorData.detail ||
        `create assignment failed: ${res.status}`
      );
    }

    const created = await res.json();

    setAssignments((prev) => [
      created,
      ...prev
    ]);

    setName("");
    setMaxMarks("");
    setDueDate("");
    setResource(null);

    setFormOpen(false);

  } catch (err) {
    console.error(
      "failed to create assignment:",
      err
    );

    alert(err.message);
  }
}

  return (
    <div className="subject-page">
      <div className="subject-header">
        <div>
          <span className="dashboard-eyebrow">{active.subject_name?.toUpperCase()}</span>
          <h2>Assignments</h2>
          <p>{active.department} · Semester {active.semester} · Section {active.section}</p>
        </div>
        <button className="attendance-save-button" onClick={() => setFormOpen((v) => !v)}>
          {formOpen ? <X size={13} /> : <Plus size={13} />}
          {formOpen ? "Cancel" : "New Assignment"}
        </button>
      </div>

      {formOpen && (
        <div className="teacher-panel">
          <form onSubmit={handleCreate} className="dispatch-form">
            <div>
              <label>Assignment name</label>
              <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. Unit 3 Problem Set" />
            </div>
            <div className="assignment-form-row">
              <div>
                <label>Max marks</label>
                <input type="number" value={maxMarks} onChange={(e) => setMaxMarks(e.target.value)} required />
              </div>
              <div>
                <label>Due date</label>
                <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} required />
              </div>
              <div>
  <label>Resource</label>

  <input
    type="file"
    accept=".pdf,.jpg,.jpeg,.png"
    onChange={(e) => setResource(e.target.files[0] || null)}
  />

  <small>
    PDF, JPG or PNG · Maximum 10 MB
  </small>
</div>
            </div>
            <button type="submit" className="dispatch-submit" style={{ width: "fit-content" }}>Create Assignment</button>
          </form>
        </div>
      )}

      <div className="teacher-panel">
        <div className="teacher-panel-header"><h3>All Assignments</h3></div>

        {loading ? (
          <div className="ui-state"><span>Loading assignments...</span></div>
        ) : assignments.length === 0 ? (
          <EmptyState icon={<ClipboardList size={20} />} title="No assignments yet" message="Create your first assignment for this subject." />
        ) : (
          <div className="assignment-list">
            {assignments.map((a) => (
  <div
    className="assignment-item-row"
    key={a.id}
    onClick={() => navigate(`/assignments/${a.id}`)}
    style={{ cursor: "pointer" }}
  >
    <div>
      <strong>{a.assignment_name}</strong>

      <span>
        Due {a.due_date} · Max marks {a.max_marks}

        {a.resource_url && (
          <>
            {" · "}
            <a
              href={`http://127.0.0.1:8000${a.resource_url}`}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
            >
              📎 {a.resource_name || "View Resource"}
            </a>
          </>
        )}
      </span>
    </div>

    <span className="assignment-submission-count">
      {a.submitted_count ?? 0} submitted
    </span>
  </div>
))}
          </div>
        )}
      </div>
    </div>
  );
}
