import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  FileText,
  Download,
  Search,
  ChevronLeft,
  ChevronRight,
  Users,
  CalendarDays,
  Award,
  Save,
  MessageSquare,
  CheckCircle2,
  AlertCircle,
  Clock3,
  BookOpen,
} from "lucide-react";
import { getInitials } from "../../context/TeacherContext";

export default function SubjectAssignmentDetails() {
  const { assignmentId } = useParams();
  const navigate = useNavigate();

  const [assignment, setAssignment] = useState(null);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // Grading state per student: { [student_id]: { marks: string|number, feedback: string, saving: boolean, saved: boolean, error: string } }
  const [gradeState, setGradeState] = useState({});

  useEffect(() => {
    async function loadAssignment() {
      setLoading(true);
      setError("");

      try {
        const token = localStorage.getItem("token");
        const params = new URLSearchParams({
          page: String(page),
          page_size: String(pageSize),
          search,
        });

        const res = await fetch(
          `http://localhost:5000/api/assignments/teacher/${assignmentId}?${params}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || "Failed to load assignment");
        }

        setAssignment(data.assignment);
        const studs = data.submissions?.students || [];
        setStudents(studs);
        setTotal(data.submissions?.total || 0);
        setTotalPages(data.submissions?.total_pages || 1);

        // Initialize gradeState
        const initialGrades = {};
        studs.forEach((s) => {
          initialGrades[s.student_id] = {
            marks: s.marks_obtained !== null && s.marks_obtained !== undefined ? s.marks_obtained : "",
            feedback: s.feedback || "",
            saving: false,
            saved: false,
            error: "",
          };
        });
        setGradeState(initialGrades);
      } catch (err) {
        console.error("failed to load assignment:", err);
        setError(err.message || "Unable to load assignment");
      } finally {
        setLoading(false);
      }
    }

    loadAssignment();
  }, [assignmentId, page, search]);

  function handleSearch(e) {
    setSearch(e.target.value);
    setPage(1);
  }

  function handleGradeChange(studentId, field, value) {
    setGradeState((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        [field]: value,
        saved: false,
        error: "",
      },
    }));
  }

  async function handleSaveGrade(studentId) {
    const studentGrades = gradeState[studentId];
    if (!studentGrades) return;

    const rawMarks = studentGrades.marks;
    if (rawMarks === "" || rawMarks === null || rawMarks === undefined) {
      setGradeState((prev) => ({
        ...prev,
        [studentId]: { ...prev[studentId], error: "Enter marks" },
      }));
      return;
    }

    const marksNum = parseFloat(rawMarks);
    const maxMarks = assignment?.max_marks || 100;
    if (isNaN(marksNum) || marksNum < 0 || marksNum > maxMarks) {
      setGradeState((prev) => ({
        ...prev,
        [studentId]: {
          ...prev[studentId],
          error: `Between 0 & ${maxMarks}`,
        },
      }));
      return;
    }

    try {
      setGradeState((prev) => ({
        ...prev,
        [studentId]: { ...prev[studentId], saving: true, error: "" },
      }));

      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:5000/api/assignments/grade", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          assignment_id: parseInt(assignmentId, 10),
          student_id: studentId,
          marks_obtained: marksNum,
          feedback: studentGrades.feedback || "",
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to save grade");
      }

      setGradeState((prev) => ({
        ...prev,
        [studentId]: { ...prev[studentId], saving: false, saved: true, error: "" },
      }));

      // Update student in local list
      setStudents((prev) =>
        prev.map((s) =>
          s.student_id === studentId
            ? { ...s, marks_obtained: marksNum, feedback: studentGrades.feedback, display_status: "graded" }
            : s
        )
      );

      setTimeout(() => {
        setGradeState((prev) => ({
          ...prev,
          [studentId]: { ...prev[studentId], saved: false },
        }));
      }, 3000);
    } catch (err) {
      console.error("Failed to save grade:", err);
      setGradeState((prev) => ({
        ...prev,
        [studentId]: { ...prev[studentId], saving: false, error: err.message },
      }));
    }
  }

  function formatDate(date) {
    if (!date) return "—";
    return new Date(date).toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  function formatDateTime(date) {
    if (!date) return "—";
    return new Date(date).toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  if (loading && !assignment) {
    return (
      <div className="ui-state">
        <div className="loading-spinner" />
        <span>Loading assignment details...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ui-state" style={{ color: "var(--danger)" }}>
        <AlertCircle size={24} />
        <span>{error}</span>
      </div>
    );
  }

  if (!assignment) return null;

  const submittedCount = students.filter((s) => s.submission_id || s.marks_obtained !== null).length;
  const gradedCount = students.filter((s) => s.marks_obtained !== null).length;

  return (
    <div className="assignment-details-view">
      {/* BREADCRUMB / BACK */}
      <button
        type="button"
        className="assignment-back-nav"
        onClick={() => navigate("/")}
      >
        <ArrowLeft size={16} />
        Back to Assignments Dashboard
      </button>

      {/* HERO HEADER CARD */}
      <div className="assignment-hero-card">
        <div className="assignment-hero-main">
          <div className="assignment-hero-subject-chip">
            <BookOpen size={13} />
            {assignment.subject_name || assignment.subject_code}
          </div>
          <h1>{assignment.assignment_name}</h1>
          <p className="assignment-hero-cohort">
            {assignment.department} · Semester {assignment.semester} · Section {assignment.section} · Created on {formatDate(assignment.created_at)}
          </p>
        </div>

        <div className="assignment-hero-pills">
          <div className="hero-pill marks">
            <Award size={15} />
            Max: {assignment.max_marks} Marks
          </div>

          <div className="hero-pill due">
            <CalendarDays size={15} />
            Due: {formatDate(assignment.due_date)}
          </div>

          {assignment.resource_url && (
            <a
              href={`http://localhost:5000${assignment.resource_url}`}
              target="_blank"
              rel="noopener noreferrer"
              className="hero-pill resource"
            >
              <Download size={14} />
              {assignment.resource_name || "Question Paper"}
            </a>
          )}
        </div>
      </div>

      {/* METRIC ROW */}
      <div className="faculty-metrics-grid" style={{ marginBottom: "20px" }}>
        <div className="faculty-metric-card">
          <div className="faculty-metric-icon-box">
            <Users size={22} />
          </div>
          <div className="faculty-metric-data">
            <span>Enrolled Students</span>
            <strong>{total} Students</strong>
          </div>
        </div>

        <div className="faculty-metric-card">
          <div className="faculty-metric-icon-box">
            <CheckCircle2 size={22} />
          </div>
          <div className="faculty-metric-data">
            <span>Submissions Received</span>
            <strong>{submittedCount} / {total} ({total > 0 ? Math.round((submittedCount / total) * 100) : 0}%)</strong>
          </div>
        </div>

        <div className="faculty-metric-card">
          <div className="faculty-metric-icon-box">
            <Award size={22} />
          </div>
          <div className="faculty-metric-data">
            <span>Evaluated & Graded</span>
            <strong>{gradedCount} / {total} Graded</strong>
          </div>
        </div>

        <div className="faculty-metric-card">
          <div className="faculty-metric-icon-box">
            <Clock3 size={22} />
          </div>
          <div className="faculty-metric-data">
            <span>Awaiting Evaluation</span>
            <strong>{Math.max(0, submittedCount - gradedCount)} Pending</strong>
          </div>
        </div>
      </div>

      {/* STUDENT SUBMISSIONS & GRADING TABLE */}
      <div className="teacher-panel" style={{ padding: 0, overflow: "hidden" }}>
        <div className="assignment-roster-header-bar">
          <div className="assignment-roster-title-group">
            <h3>Student Submissions & Inline Evaluation</h3>
            <span>Enter student scores and optional feedback below, then click Grade.</span>
          </div>

          <div className="assignment-roster-search">
            <Search size={15} color="var(--text-muted)" />
            <input
              type="text"
              placeholder="Search student or USN..."
              value={search}
              onChange={handleSearch}
            />
          </div>
        </div>

        <div style={{ overflowX: "auto" }}>
          <table className="student-grading-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>USN</th>
                <th>Status</th>
                <th>Submitted File</th>
                <th style={{ width: "130px" }}>Score (/{assignment.max_marks})</th>
                <th>Faculty Feedback</th>
                <th style={{ width: "110px", textAlign: "right" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {students.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: "36px", textAlign: "center", color: "var(--text-muted)" }}>
                    No students match your search filter.
                  </td>
                </tr>
              ) : (
                students.map((student) => {
                  const hasFile = Boolean(student.file_url || student.submission_file_url);
                  const fileUrl = student.file_url || student.submission_file_url;
                  const fileName = student.file_name || student.submission_file_name;
                  const stGrades = gradeState[student.student_id] || { marks: "", feedback: "", saving: false, saved: false, error: "" };
                  const isGraded = student.marks_obtained !== null && student.marks_obtained !== undefined;
                  const initials = getInitials(student.name);

                  return (
                    <tr key={student.student_id}>
                      <td>
                        <div className="student-profile-cell">
                          <div className="student-initials-avatar">
                            {initials}
                          </div>
                          <div>
                            <div className="student-name-text">{student.name}</div>
                            {student.submission_date && (
                              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "1px" }}>
                                {formatDateTime(student.submission_date)}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>

                      <td>
                        <span className="student-usn-badge">{student.usn}</span>
                      </td>

                      <td>
                        {isGraded ? (
                          <span className="attendance-pill present" style={{ fontSize: "11px", fontWeight: 700, padding: "3px 8px" }}>
                            <Award size={12} style={{ marginRight: "3px", verticalAlign: "-1px" }} />
                            Graded
                          </span>
                        ) : hasFile ? (
                          <span className="attendance-pill present" style={{ fontSize: "11px", fontWeight: 700, padding: "3px 8px" }}>
                            <CheckCircle2 size={12} style={{ marginRight: "3px", verticalAlign: "-1px" }} />
                            Submitted
                          </span>
                        ) : (
                          <span className="attendance-pill absent" style={{ fontSize: "11px", fontWeight: 700, padding: "3px 8px" }}>
                            Pending
                          </span>
                        )}
                      </td>

                      <td>
                        {hasFile ? (
                          <a
                            href={`http://localhost:5000${fileUrl}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="submission-file-chip"
                          >
                            <FileText size={13} />
                            <span style={{ maxWidth: "140px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                              {fileName || "Download Work"}
                            </span>
                            <Download size={12} />
                          </a>
                        ) : (
                          <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>—</span>
                        )}
                      </td>

                      <td>
                        <div className="grade-input-wrapper">
                          <input
                            type="number"
                            min="0"
                            max={assignment.max_marks}
                            step="0.5"
                            placeholder="Marks"
                            className="grade-number-input"
                            value={stGrades.marks}
                            onChange={(e) => handleGradeChange(student.student_id, "marks", e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") handleSaveGrade(student.student_id);
                            }}
                          />
                        </div>
                        {stGrades.error && (
                          <div style={{ color: "var(--danger)", fontSize: "10px", marginTop: "2px" }}>
                            {stGrades.error}
                          </div>
                        )}
                      </td>

                      <td>
                        <input
                          type="text"
                          placeholder="Optional feedback comment..."
                          className="grade-feedback-input"
                          value={stGrades.feedback}
                          onChange={(e) => handleGradeChange(student.student_id, "feedback", e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") handleSaveGrade(student.student_id);
                          }}
                        />
                      </td>

                      <td style={{ textAlign: "right" }}>
                        <button
                          type="button"
                          className={`save-grade-action-btn ${stGrades.saved ? "saved" : ""}`}
                          disabled={stGrades.saving}
                          onClick={() => handleSaveGrade(student.student_id)}
                        >
                          <Save size={12} />
                          {stGrades.saving ? "Saving..." : stGrades.saved ? "Saved ✓" : "Grade"}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* PAGINATION */}
        <div style={{ padding: "14px 20px", borderTop: "1px solid var(--border)", display: "flex", justifyContent: "flex-end", gap: "6px" }}>
          <button
            className="flagged-view-button"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            <ChevronLeft size={15} />
          </button>

          {Array.from({ length: totalPages }, (_, i) => i + 1).map((pNum) => (
            <button
              key={pNum}
              className={`flagged-view-button ${page === pNum ? "active" : ""}`}
              style={page === pNum ? { background: "var(--primary)", color: "#0d131f" } : {}}
              onClick={() => setPage(pNum)}
            >
              {pNum}
            </button>
          ))}

          <button
            className="flagged-view-button"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            <ChevronRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}