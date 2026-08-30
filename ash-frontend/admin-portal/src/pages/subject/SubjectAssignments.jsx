import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ClipboardList,
  Plus,
  X,
  CalendarDays,
  FileText,
  Download,
  Users,
  Award,
  CheckCircle2,
  Clock3,
  ArrowRight,
  UploadCloud,
  FileCheck2,
  Paperclip,
} from "lucide-react";
import { useTeacher } from "../../context/TeacherContext";
import { EmptyState } from "../../components/shared/Shared";

export default function SubjectAssignments() {
  const { active } = useTeacher();
  const navigate = useNavigate();

  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const [name, setName] = useState("");
  const [maxMarks, setMaxMarks] = useState("25");
  const [dueDate, setDueDate] = useState("");
  const [resource, setResource] = useState(null);

  const fetchAssignments = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const params = new URLSearchParams({
        department: active.department,
        semester: String(active.semester),
        section: active.section,
        subject_code: active.subject_code,
      });

      const res = await fetch(`http://localhost:5000/api/assignments?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        throw new Error(`Fetch assignments failed: ${res.status}`);
      }

      const data = await res.json();
      setAssignments(data.assignments || []);
    } catch (err) {
      console.error("failed to load assignments:", err);
      setAssignments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (active) {
      fetchAssignments();
    }
  }, [active]);

  async function handleCreate(e) {
    e.preventDefault();
    setFormError("");

    if (!name.trim()) {
      setFormError("Please enter an assignment title.");
      return;
    }
    if (!dueDate) {
      setFormError("Please select a due date.");
      return;
    }

    try {
      setSubmitting(true);
      const token = localStorage.getItem("token");
      const formData = new FormData();

      formData.append("department", active.department);
      formData.append("semester", active.semester);
      formData.append("section", active.section);
      formData.append("subject_code", active.subject_code);
      formData.append("assignment_name", name.trim());
      formData.append("max_marks", maxMarks);
      formData.append("due_date", dueDate);

      if (resource) {
        formData.append("resource", resource);
      }

      const res = await fetch("http://localhost:5000/api/assignments", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Create assignment failed: ${res.status}`);
      }

      const created = await res.json();
      setAssignments((prev) => [created, ...prev]);

      // Reset form
      setName("");
      setMaxMarks("25");
      setDueDate("");
      setResource(null);
      setFormOpen(false);
    } catch (err) {
      console.error("failed to create assignment:", err);
      setFormError(err.message || "Failed to create assignment");
    } finally {
      setSubmitting(false);
    }
  }

  function formatDate(dateStr) {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  function getDeadlineInfo(dateStr) {
    if (!dateStr) return null;
    const due = new Date(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    due.setHours(0, 0, 0, 0);

    const diffDays = Math.ceil((due - today) / (1000 * 60 * 60 * 24));
    if (diffDays < 0) {
      return { label: "Deadline Passed", isOverdue: true };
    }
    if (diffDays === 0) {
      return { label: "Due Today", isDueSoon: true };
    }
    if (diffDays === 1) {
      return { label: "Due Tomorrow", isDueSoon: true };
    }
    return { label: `Due in ${diffDays} days`, isDueSoon: false };
  }

  const totalAssignments = assignments.length;
  const totalSubmissions = assignments.reduce((acc, a) => acc + (a.submitted_count || 0), 0);

  return (
    <div className="faculty-assignments-container">
      {/* HEADER BAR */}
      <div className="faculty-page-header">
        <div className="faculty-page-title-group">
          <h2>Assignments & Coursework</h2>
          <div className="faculty-context-badges">
            <span className="context-tag accent">
              <ClipboardList size={13} />
              {active.subject_name || active.subject_code}
            </span>
            <span className="context-tag">
              {active.department} · Semester {active.semester} · Section {active.section}
            </span>
          </div>
        </div>

        <button
          type="button"
          className="create-assignment-btn"
          onClick={() => {
            setFormError("");
            setFormOpen(true);
          }}
        >
          <Plus size={16} />
          Create Assignment
        </button>
      </div>

      {/* METRIC STRIP */}
      <div className="faculty-metrics-grid">
        <div className="faculty-metric-card">
          <div className="faculty-metric-icon-box">
            <ClipboardList size={22} />
          </div>
          <div className="faculty-metric-data">
            <span>Total Assigned</span>
            <strong>{totalAssignments}</strong>
          </div>
        </div>

        <div className="faculty-metric-card">
          <div className="faculty-metric-icon-box">
            <CheckCircle2 size={22} />
          </div>
          <div className="faculty-metric-data">
            <span>Submissions Logged</span>
            <strong>{totalSubmissions}</strong>
          </div>
        </div>

        <div className="faculty-metric-card">
          <div className="faculty-metric-icon-box">
            <Users size={22} />
          </div>
          <div className="faculty-metric-data">
            <span>Class Section</span>
            <strong>Sec {active.section}</strong>
          </div>
        </div>

        <div className="faculty-metric-card">
          <div className="faculty-metric-icon-box">
            <Award size={22} />
          </div>
          <div className="faculty-metric-data">
            <span>Course Code</span>
            <strong>{active.subject_code}</strong>
          </div>
        </div>
      </div>

      {/* ASSIGNMENT LIST CARD CONTAINER */}
      <div className="teacher-panel" style={{ padding: "20px" }}>
        <div className="teacher-panel-header" style={{ marginBottom: "16px" }}>
          <h3 style={{ fontSize: "16px", fontWeight: 700 }}>
            Published Coursework ({assignments.length})
          </h3>
        </div>

        {loading ? (
          <div className="ui-state">
            <div className="loading-spinner" />
            <span>Loading assignments...</span>
          </div>
        ) : assignments.length === 0 ? (
          <EmptyState
            icon={<ClipboardList size={28} />}
            title="No assignments created yet"
            message="Click '+ Create Assignment' above to publish coursework and problem sets for your students."
          />
        ) : (
          <div className="faculty-assignments-grid">
            {assignments.map((a) => {
              const deadline = getDeadlineInfo(a.due_date);
              const submittedCount = a.submitted_count ?? 0;

              return (
                <div
                  className="faculty-assignment-card"
                  key={a.id}
                  onClick={() => navigate(`/assignments/${a.id}`)}
                >
                  <div className="faculty-card-top-row">
                    <div className="faculty-card-title-block">
                      <h3>{a.assignment_name}</h3>
                      <div className="faculty-card-meta-chips">
                        <span className="meta-chip">
                          <CalendarDays size={13} />
                          Due: {formatDate(a.due_date)}
                        </span>
                        <span className="meta-chip">
                          <Award size={13} />
                          Max: {a.max_marks} marks
                        </span>
                        {a.resource_url && (
                          <a
                            href={`http://localhost:5000${a.resource_url}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="meta-chip resource-chip"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Paperclip size={12} />
                            {a.resource_name || "Question Resource"}
                          </a>
                        )}
                      </div>
                    </div>

                    {deadline && (
                      <span
                        className={`attendance-pill ${
                          deadline.isOverdue ? "absent" : deadline.isDueSoon ? "pending" : "present"
                        }`}
                        style={{ fontSize: "11px", fontWeight: 700 }}
                      >
                        {deadline.label}
                      </span>
                    )}
                  </div>

                  <div className="faculty-card-bottom-row">
                    <div className="submission-progress-info">
                      <span className="submission-counter-badge">
                        👥 {submittedCount} Submitted
                      </span>
                      <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                        Click to view student solutions and grade marks
                      </span>
                    </div>

                    <button
                      type="button"
                      className="faculty-card-action-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/assignments/${a.id}`);
                      }}
                    >
                      Review & Grade Roster
                      <ArrowRight size={14} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* CREATE ASSIGNMENT MODAL */}
      {formOpen && (
        <div className="faculty-modal-overlay" onClick={() => !submitting && setFormOpen(false)}>
          <div className="faculty-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="faculty-modal-header">
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <ClipboardList size={20} color="var(--primary)" />
                <h3>Create New Course Assignment</h3>
              </div>
              <button
                type="button"
                className="submission-close-button"
                onClick={() => !submitting && setFormOpen(false)}
                disabled={submitting}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreate}>
              <div className="faculty-modal-body">
                {formError && (
                  <div className="submission-error" style={{ color: "var(--danger)", fontSize: "12px" }}>
                    {formError}
                  </div>
                )}

                <div className="form-group">
                  <label>Assignment Title / Topic</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    placeholder="e.g. Unit 3 Process Synchronization & Banker's Algorithm"
                  />
                </div>

                <div className="form-grid-2">
                  <div className="form-group">
                    <label>Maximum Marks</label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={maxMarks}
                      onChange={(e) => setMaxMarks(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Submission Due Date</label>
                    <input
                      type="date"
                      value={dueDate}
                      onChange={(e) => setDueDate(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Attach Question Paper / Resource (Optional)</label>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                    onChange={(e) => setResource(e.target.files?.[0] || null)}
                  />
                  <small style={{ color: "var(--text-muted)", fontSize: "11px", marginTop: "3px" }}>
                    Allowed: PDF, DOCX, JPG, PNG (Max 10 MB)
                  </small>
                </div>
              </div>

              <div className="faculty-modal-footer">
                <button
                  type="button"
                  className="submission-cancel-button"
                  onClick={() => setFormOpen(false)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="create-assignment-btn"
                  disabled={submitting}
                >
                  {submitting ? "Publishing..." : "Publish to Students"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
