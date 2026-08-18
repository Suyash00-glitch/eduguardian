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
  User,
} from "lucide-react";

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
          `http://127.0.0.1:8000/api/assignments/teacher/${assignmentId}?${params}`,
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
        setStudents(data.submissions?.students || []);
        setTotal(data.submissions?.total || 0);
        setTotalPages(data.submissions?.total_pages || 1);
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
      <div className="assignment-details-state">
        <span>Loading assignment...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="assignment-details-state error">
        <span>{error}</span>
      </div>
    );
  }

  if (!assignment) {
    return null;
  }

  return (
    <div className="subject-page assignment-details-page">

      {/* BACK */}

      <button
        type="button"
        className="assignment-back-button"
        onClick={() => navigate(-1)}
      >
        <ArrowLeft size={15} />
        Back to Assignments
      </button>

      {/* PAGE HEADER */}

      <div className="assignment-details-heading">
        <div>
          <span className="dashboard-eyebrow">
            ASSIGNMENT DETAILS
          </span>

          <h2>{assignment.assignment_name}</h2>

          <p>
            {assignment.department}
            <span> • </span>
            Semester {assignment.semester}
            <span> • </span>
            Section {assignment.section}
            <span> • </span>
            <strong>
              {assignment.subject_name || assignment.subject_code}
            </strong>
          </p>
        </div>
      </div>

      {/* ASSIGNMENT INFORMATION */}

      <section className="assignment-info-card">

        <div className="assignment-card-heading">
          <div className="assignment-heading-icon">
            <FileText size={19} />
          </div>

          <h3>Assignment Information</h3>
        </div>

        <div className="assignment-info-grid">

          <div className="assignment-info-item">
            <span>ASSIGNMENT NAME</span>
            <strong>{assignment.assignment_name}</strong>
          </div>

          <div className="assignment-info-item">
            <span>MAX MARKS</span>
            <strong>{assignment.max_marks}</strong>
          </div>

          <div className="assignment-info-item">
            <span>CLASS</span>
            <strong>
              {assignment.department} · Semester{" "}
              {assignment.semester} · Section {assignment.section}
            </strong>
          </div>

          <div className="assignment-info-item">
            <span>CREATED BY</span>
            <strong>
              <User size={15} />
              Teacher
            </strong>
          </div>

          <div className="assignment-info-item">
            <span>SUBJECT</span>
            <strong>
              {assignment.subject_name || assignment.subject_code}
            </strong>
          </div>

          <div className="assignment-info-item">
            <span>DUE DATE</span>
            <strong>
              <CalendarDays size={15} />
              {formatDate(assignment.due_date)}
            </strong>
          </div>

          <div className="assignment-info-item">
            <span>CREATED ON</span>
            <strong>
              {formatDateTime(assignment.created_at)}
            </strong>
          </div>

          <div className="assignment-info-item">
            <span>RESOURCE</span>

            {assignment.resource_url ? (
              <div className="assignment-resource-content">

                <a
                  href={`http://127.0.0.1:8000${assignment.resource_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="assignment-resource-name"
                >
                  <FileText size={15} />
                  {assignment.resource_name || "Assignment Resource"}
                </a>

                <a
                  href={`http://127.0.0.1:8000${assignment.resource_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="assignment-resource-download"
                >
                  <Download size={14} />
                  View / Download
                </a>

              </div>
            ) : (
              <strong className="no-resource">
                No resource uploaded
              </strong>
            )}
          </div>

        </div>
      </section>

      {/* STUDENT SUBMISSIONS */}

      <section className="submission-card">

        <div className="submission-card-top">

          <div className="submission-heading">

            <div className="submission-heading-icon">
              <Users size={19} />
            </div>

            <div>
              <h3>Student Submissions</h3>

              <span>
                {total} students in this class
              </span>
            </div>

          </div>

          <div className="submission-controls">

            <div className="submission-search">
              <Search size={15} />

              <input
                type="text"
                placeholder="Search by name or USN..."
                value={search}
                onChange={handleSearch}
              />
            </div>

            <div className="page-size-box">
              10 per page
            </div>

          </div>

        </div>

        {/* TABLE */}

        <div className="submission-table-wrapper">

          <div className="submission-table">

            <div className="submission-table-header">
              <span>USN</span>
              <span>STUDENT NAME</span>
              <span>STATUS</span>
              <span>SUBMISSION DATE</span>
              <span>MARKS</span>
              <span>FILE</span>
              <span></span>
            </div>

            {students.length === 0 ? (

              <div className="submission-empty">
                <Users size={28} />

                <strong>No students found</strong>

                <span>
                  No students match your search.
                </span>
              </div>

            ) : (

              students.map((student) => {

                const submitted = Boolean(
                  student.submission_id
                );

                return (
                  <div
                    className="submission-table-row"
                    key={student.student_id}
                  >

                    <span className="student-usn">
                      {student.usn}
                    </span>

                    <span className="student-name">
                      {student.name}
                    </span>

                    <span>

                      <span
                        className={
                          submitted
                            ? "submission-status submitted"
                            : "submission-status pending"
                        }
                      >
                        {submitted ? (
                          <>
                            <span className="status-dot">✓</span>
                            Submitted
                          </>
                        ) : (
                          <>
                            <span className="status-dot">×</span>
                            Not submitted
                          </>
                        )}
                      </span>

                    </span>

                    <span className="submission-date">
                      {submitted
                        ? formatDateTime(
                            student.submission_date
                          )
                        : "—"}
                    </span>

                    <span className="submission-marks">
                      {student.marks_obtained !== null &&
                      student.marks_obtained !== undefined
                        ? `${student.marks_obtained}/${assignment.max_marks}`
                        : "—"}
                    </span>

                    <span className="submission-file">

                      {student.submission_file_url ? (
                        <a
                          href={`http://127.0.0.1:8000${student.submission_file_url}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          title="Download submission"
                        >
                          <FileText size={15} />
                          {student.submission_file_name ||
                            "View file"}
                        </a>
                      ) : (
                        "—"
                      )}

                    </span>

                    <span className="submission-download">

                      {student.submission_file_url && (
                        <a
                          href={`http://127.0.0.1:8000${student.submission_file_url}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          title="Download"
                        >
                          <Download size={15} />
                        </a>
                      )}

                    </span>

                  </div>
                );
              })
            )}

          </div>

        </div>

        {/* PAGINATION */}

        <div className="submission-pagination">

          <button
            disabled={page <= 1}
            onClick={() =>
              setPage((p) => Math.max(1, p - 1))
            }
          >
            <ChevronLeft size={16} />
          </button>

          {Array.from(
            { length: totalPages },
            (_, index) => index + 1
          ).map((pageNumber) => (
            <button
              key={pageNumber}
              className={
                page === pageNumber
                  ? "active"
                  : ""
              }
              onClick={() => setPage(pageNumber)}
            >
              {pageNumber}
            </button>
          ))}

          <button
            disabled={page >= totalPages}
            onClick={() =>
              setPage((p) =>
                Math.min(totalPages, p + 1)
              )
            }
          >
            <ChevronRight size={16} />
          </button>

        </div>

      </section>

    </div>
  );
}