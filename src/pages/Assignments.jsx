import React, { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ClipboardList,
  Clock3,
  CheckCircle2,
  AlertCircle,
  CalendarDays,
  ArrowRight,
} from "lucide-react";

import { demoAssignmentList } from "../services/demoData";

const filters = [
  {
    id: "all",
    label: "All",
  },
  {
    id: "pending",
    label: "Pending",
  },
  {
    id: "submitted",
    label: "Submitted",
  },
  {
    id: "overdue",
    label: "Overdue",
  },
];

function formatDate(date) {
  return new Date(date).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function getStatusLabel(status) {
  const labels = {
    pending: "Pending",
    submitted: "Submitted",
    overdue: "Overdue",
  };

  return labels[status] || status;
}

function Assignments() {
  const [activeFilter, setActiveFilter] = useState("all");
  const navigate = useNavigate();

  const filteredAssignments = useMemo(() => {
    if (activeFilter === "all") {
      return demoAssignmentList;
    }

    return demoAssignmentList.filter(
      (assignment) => assignment.status === activeFilter,
    );
  }, [activeFilter]);

  const total = demoAssignmentList.length;

  const pending = demoAssignmentList.filter(
    (assignment) => assignment.status === "pending",
  ).length;

  const submitted = demoAssignmentList.filter(
    (assignment) => assignment.status === "submitted",
  ).length;

  const overdue = demoAssignmentList.filter(
    (assignment) => assignment.status === "overdue",
  ).length;

  return (
    <div className="page assignments-page">
      {/* HEADER */}

      <div className="page-header">
        <div>
          <span className="page-eyebrow">ACADEMIC WORK</span>

          <h1>Assignments</h1>

          <p>Track your assignments, deadlines and submissions in one place.</p>
        </div>
      </div>

      {/* SUMMARY */}

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
            <AlertCircle size={19} />
          </div>

          <div>
            <span>Overdue</span>
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
          filteredAssignments.map((assignment) => (
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

                    <span className={`assignment-status ${assignment.status}`}>
                      {getStatusLabel(assignment.status)}
                    </span>
                  </div>

                  <p className="assignment-description">
                    {assignment.description}
                  </p>

                  <div className="assignment-meta">
                    <span>
                      <CalendarDays size={14} />
                      Due {formatDate(assignment.dueDate)}
                    </span>

                    <span>
                      <ClipboardList size={14} />
                      {assignment.maxMarks} marks
                    </span>

                    {assignment.submissionStatus === "submitted" &&
                      assignment.marks !== undefined && (
                        <span className="assignment-marks">
                          {assignment.marks}/{assignment.maxMarks}
                        </span>
                      )}
                  </div>
                </div>
              </div>

              <button
                type="button"
                className="assignment-view-button"
                onClick={() => navigate(`/assignments/${assignment.id}`)}
              >
                View assignment
                <ArrowRight size={15} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default Assignments;
