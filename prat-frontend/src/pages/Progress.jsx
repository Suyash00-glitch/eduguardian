import React, { useCallback, useEffect, useMemo, useState } from "react";

import {
  Activity,
  ClipboardCheck,
} from "lucide-react";

import { studentService } from "../services/studentService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

function Progress() {
  const [attendance, setAttendance] = useState([]);
  const [assignments, setAssignments] = useState([]);



  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadProgress = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [attendanceData, assignmentData] =
        await Promise.all([
          studentService.getAttendance(),
          studentService.getAssignments(),
        ]);

      setAttendance(attendanceData || []);
      setAssignments(assignmentData || []);

    } catch (err) {
      setError(err.message || "Unable to load progress.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProgress();
  }, [loadProgress]);

  const subjectsAboveThreshold = attendance.filter(
    (item) => Number(item.percentage || 0) >= 75
  ).length;

  const submittedAssignments = assignments.filter(
    (item) => item.status === "submitted",
  ).length;


  if (loading) {
    return <LoadingState message="Loading your progress..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Unable to load progress"
        message={error}
        onRetry={loadProgress}
      />
    );
  }

  return (
    <div className="progress-page">
      {/* HEADER */}

      <div className="progress-header">
        <div>
          <span className="progress-eyebrow">ACADEMIC PERFORMANCE</span>

          <h1>My Progress</h1>

          <p>
            A detailed view of your attendance, assessments and learning
            activity.
          </p>
        </div>


      </div>

      {/* SUMMARY */}

      <div className="progress-summary-grid">
        <ProgressCard
          icon={Activity}
          value={`${subjectsAboveThreshold}/${attendance.length}`}
          label="Subjects Above 75%"
        />


        <ProgressCard
          icon={ClipboardCheck}
          value={`${submittedAssignments}/${assignments.length}`}
          label="Assignments Submitted"
        />


      </div>

      {/* ATTENDANCE */}

      <section className="progress-section">
        <div className="progress-section-heading">
          <div>
            <span>ATTENDANCE</span>
            <h2>Subject-wise attendance</h2>
          </div>

          <div className="target-badge">Target: 75%</div>
        </div>

        <div className="attendance-table">
          <div className="attendance-table-head">
            <span>SUBJECT</span>
            <span>HELD</span>
            <span>ATTENDED</span>
            <span>ATTENDANCE</span>
            <span>STATUS</span>
          </div>

          {attendance.map((item) => {
            const percentage = Number(item.percentage || 0);

            const good = percentage >= 75;

            return (
              <div className="attendance-row" key={item.subjectCode}>
                <div className="subject-cell">
                  <strong>{item.subjectCode}</strong>
                  <span>{item.subjectName}</span>
                </div>

                <span>{item.classesHeld}</span>

                <span>{item.classesAttended}</span>

                <div className="attendance-progress-cell">
                  <div className="attendance-percentage">
                    {percentage.toFixed(1)}%
                  </div>

                  <div className="mini-progress">
                    <div
                      style={{
                        width: `${Math.min(percentage, 100)}%`,
                      }}
                    />
                  </div>
                </div>

                <span
                  className={`attendance-status ${good ? "good" : "warning"}`}
                >
                  {good ? "On track" : "Needs attention"}
                </span>
              </div>
            );
          })}
        </div>
      </section>

      {/* QUIZZES */}


    </div>
  );
}

function ProgressCard({ icon: Icon, value, label }) {
  return (
    <div className="progress-stat-card">
      <div className="progress-stat-icon">
        <Icon size={16} />
      </div>

      <div>
        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    </div>
  );
}

export default Progress;