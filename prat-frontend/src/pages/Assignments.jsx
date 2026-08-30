import React, { useCallback, useEffect, useMemo, useState } from "react";
import { studentService } from "../services/studentService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import { useNavigate } from "react-router-dom";
import {
  ClipboardList,
  Clock3,
  CheckCircle2,
  AlertCircle,
  CalendarDays,
  ArrowRight,
  Paperclip,
  Award,
  Lock,
} from "lucide-react";

const filters = [
  { id: "all", label: "All" },
  { id: "pending", label: "Pending" },
  { id: "submitted", label: "Submitted" },
  { id: "graded", label: "Graded" },
  { id: "overdue", label: "Overdue / Locked" },
];

function formatDate(date) {
  if (!date) return "—";
  return new Date(date).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function getStatusBadge(assignment) {
  if (assignment.status === "graded" || (assignment.marks !== null && assignment.marks !== undefined)) {
    return {
      label: `Graded: ${assignment.marks}/${assignment.maxMarks}`,
      className: "assignment-status graded",
      icon: <Award size={13} />,
    };
  }
  if (assignment.status === "submitted" || assignment.submissionStatus === "submitted") {
    return {
      label: "Submitted",
      className: "assignment-status submitted",
      icon: <CheckCircle2 size={13} />,
    };
  }
  if (assignment.isLocked || assignment.status === "overdue") {
    return {
      label: "Closed / Locked",
      className: "assignment-status overdue",
      icon: <Lock size={13} />,
    };
  }
  return {
    label: "Pending",
    className: "assignment-status pending",
    icon: <Clock3 size={13} />,
  };
}

function Assignments() {
  const [activeFilter, setActiveFilter] = useState("all");
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const loadAssignments = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await studentService.getAssignments();
      setAssignments(data || []);
    } catch (err) {
      setError(err.message || "Unable to load assignments.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAssignments();
  }, [loadAssignments]);

  const filteredAssignments = useMemo(() => {
    if (activeFilter === "all") return assignments;
    if (activeFilter === "graded") {
      return assignments.filter((a) => a.status === "graded" || a.marks !== null);
    }
    if (activeFilter === "overdue") {
      return assignments.filter((a) => a.status === "overdue" || a.isLocked);
    }
    return assignments.filter((a) => a.status === activeFilter);
  }, [activeFilter, assignments]);

  const total = assignments.length;
  const pending = assignments.filter((a) => a.status === "pending").length;
  const submitted = assignments.filter((a) => a.status === "submitted").length;
  const graded = assignments.filter((a) => a.status === "graded" || a.marks !== null).length;
  const overdue = assignments.filter((a) => a.status === "overdue" || a.isLocked).length;

  if (loading) {
    return <LoadingState message="Loading your assignments..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Unable to load assignments"
        message={error}
        onRetry={loadAssignments}
      />
    );
  }

  return (
    <div className="page assignments-page">
      {/* HEADER */}
      <div className="page-header">
        <div>
          <h1>Course Assignments</h1>
          <p>Track your assignments, deadlines, submissions, and faculty grades in real time.</p>
        </div>
      </div>

      {/* SUMMARY CARDS */}
      <div className="assignment-summary">
        <div className="assignment-summary-card">
          <div className="assignment-summary-icon">
            <ClipboardList size={19} />
          </div>
          <div>
            <span>Total assignments</span>
            <strong>{total}</strong>
          </div>
        </div>

        <div className="assignment-summary-card">
          <div className="assignment-summary-icon">
            <Clock3 size={19} />
          </div>
          <div>
            <span>Pending</span>
            <strong>{pending}</strong>
          </div>
        </div>

        <div className="assignment-summary-card">
          <div className="assignment-summary-icon">
            <CheckCircle2 size={19} />
          </div>
          <div>
            <span>Submitted</span>
            <strong>{submitted}</strong>
          </div>
        </div>

        <div className="assignment-summary-card">
          <div className="assignment-summary-icon">
            <Award size={19} />
          </div>
          <div>
            <span>Graded</span>
            <strong>{graded}</strong>
          </div>
        </div>

        <div className="assignment-summary-card">
          <div className="assignment-summary-icon">
            <AlertCircle size={19} />
          </div>
          <div>
            <span>Overdue / Closed</span>
            <strong>{overdue}</strong>
          </div>
        </div>
      </div>

      {/* FILTERS */}
      <div className="assignment-toolbar">
        <div>
          <h2>Your assignments</h2>
          <span>
            {filteredAssignments.length}{" "}
            {filteredAssignments.length === 1 ? "assignment" : "assignments"}
          </span>
        </div>

        <div className="assignment-filters">
          {filters.map((filter) => (
            <button
              key={filter.id}
              type="button"
              className={
                activeFilter === filter.id
                  ? "assignment-filter active"
                  : "assignment-filter"
              }
              onClick={() => setActiveFilter(filter.id)}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      {/* ASSIGNMENT LIST */}
      <div className="assignment-list">
        {filteredAssignments.length === 0 ? (
          <div className="assignment-empty-state">
            <ClipboardList size={36} />
            <h2>No assignments found</h2>
            <p>There are no assignments in this category right now.</p>
          </div>
        ) : (
          filteredAssignments.map((assignment) => {
            const badge = getStatusBadge(assignment);
            return (
              <div className="assignment-card" key={assignment.id}>
                <div className="assignment-card-main">
                  <div className="assignment-subject">
                    {assignment.subjectCode}
                  </div>

                  <div className="assignment-card-content">
                    <div className="assignment-card-title-row">
                      <div>
                        <span className="assignment-subject-name">
                          {assignment.subjectName}
                        </span>
                        <h3>{assignment.title}</h3>
                      </div>

                      <span className={badge.className} style={{ display: "inline-flex", alignItems: "center", gap: "5px" }}>
                        {badge.icon}
                        {badge.label}
                      </span>
                    </div>

                    <p className="assignment-description">
                      {assignment.description || `Coursework task for ${assignment.subjectName}`}
                    </p>

                    <div className="assignment-meta">
                      <span>
                        <CalendarDays size={14} />
                        Due {formatDate(assignment.dueDate)}
                      </span>

                      <span>
                        <ClipboardList size={14} />
                        Max {assignment.maxMarks} marks
                      </span>

                      {assignment.marks !== null && assignment.marks !== undefined && (
                        <span className="assignment-marks" style={{ color: "var(--primary)", fontWeight: 700 }}>
                          🎯 Score: {assignment.marks} / {assignment.maxMarks}
                        </span>
                      )}

                      {assignment.feedback && (
                        <span style={{ color: "var(--text-secondary)", fontSize: "12px", fontStyle: "italic" }}>
                          💬 Note: "{assignment.feedback}"
                        </span>
                      )}
                    </div>

                    {assignment.resourceUrl && (
                      <div className="assignment-resource">
                        <Paperclip size={14} />
                        <a
                          href={`http://localhost:5000${assignment.resourceUrl}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {assignment.resourceName || "View Assignment Resource"}
                        </a>
                      </div>
                    )}
                  </div>
                </div>

                <button
                  type="button"
                  className="assignment-view-button"
                  onClick={() => navigate(`/assignments/${assignment.id}`)}
                >
                  {assignment.marks !== null
                    ? "View Grade & Feedback"
                    : assignment.isLocked
                    ? "View Details"
                    : assignment.status === "submitted"
                    ? "View Submission"
                    : "Submit Assignment"}
                  <ArrowRight size={15} />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default Assignments;
