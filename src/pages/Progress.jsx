import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BookOpen,
  CheckCircle2,
  ClipboardCheck,
  TrendingUp,
} from "lucide-react";

import { studentService } from "../services/studentService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

function Progress() {
  const [attendance, setAttendance] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [quizzes, setQuizzes] = useState([]);
  const [lmsActivity, setLmsActivity] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadProgress = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [attendanceData, assignmentData, quizData, lmsData] =
        await Promise.all([
          studentService.getAttendance(),
          studentService.getAssignments(),
          studentService.getQuizResults(),
          studentService.getLmsActivity(),
        ]);

      setAttendance(attendanceData || []);
      setAssignments(assignmentData || []);
      setQuizzes(quizData || []);
      setLmsActivity(lmsData || []);
    } catch (err) {
      setError(err.message || "Unable to load progress.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProgress();
  }, [loadProgress]);

  const attendanceAverage = useMemo(() => {
    if (!attendance.length) return 0;

    const totalHeld = attendance.reduce(
      (sum, item) => sum + Number(item.classesHeld || 0),
      0,
    );

    const totalAttended = attendance.reduce(
      (sum, item) => sum + Number(item.classesAttended || 0),
      0,
    );

    return totalHeld ? ((totalAttended / totalHeld) * 100).toFixed(1) : 0;
  }, [attendance]);

  const quizAverage = useMemo(() => {
    if (!quizzes.length) return 0;

    const totalMarks = quizzes.reduce(
      (sum, item) => sum + Number(item.marks || 0),
      0,
    );

    const totalMax = quizzes.reduce(
      (sum, item) => sum + Number(item.maxMarks || 0),
      0,
    );

    return totalMax ? ((totalMarks / totalMax) * 100).toFixed(0) : 0;
  }, [quizzes]);

  const submittedAssignments = assignments.filter(
    (item) => item.status === "submitted",
  ).length;

  const totalLmsMinutes = lmsActivity.reduce(
    (sum, item) => sum + Number(item.minutes || 0),
    0,
  );

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

        <div className="progress-trend">
          <ArrowUpRight size={15} />
          Improving
        </div>
      </div>

      {/* SUMMARY */}

      <div className="progress-summary-grid">
        <ProgressCard
          icon={Activity}
          value={`${attendanceAverage}%`}
          label="Overall Attendance"
        />

        <ProgressCard
          icon={TrendingUp}
          value={`${quizAverage}%`}
          label="Quiz Average"
        />

        <ProgressCard
          icon={ClipboardCheck}
          value={`${submittedAssignments}/${assignments.length}`}
          label="Assignments Submitted"
        />

        <ProgressCard
          icon={BookOpen}
          value={`${totalLmsMinutes}m`}
          label="LMS Activity This Week"
        />
      </div>

      {/* ATTENDANCE */}

      <section className="progress-section">
        <div className="progress-section-heading">
          <div>
            <span>ATTENDANCE</span>
            <h2>Subject-wise attendance</h2>
          </div>

          <div className="target-badge">Target: 85%</div>
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

            const good = percentage >= 85;

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

      <section className="progress-section">
        <div className="progress-section-heading">
          <div>
            <span>ASSESSMENTS</span>
            <h2>Recent quiz results</h2>
          </div>
        </div>

        <div className="quiz-grid">
          {quizzes.map((quiz) => {
            const percentage =
              (Number(quiz.marks) / Number(quiz.maxMarks)) * 100;

            return (
              <div
                className="quiz-card"
                key={`${quiz.subjectCode}-${quiz.quizName}`}
              >
                <div className="quiz-icon">
                  <CheckCircle2 size={15} />
                </div>

                <div className="quiz-info">
                  <span>{quiz.subjectName}</span>

                  <strong>{quiz.quizName}</strong>
                </div>

                <div className="quiz-score">
                  <strong>
                    {quiz.marks}/{quiz.maxMarks}
                  </strong>

                  <span>{percentage.toFixed(0)}%</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* LMS */}

      <section className="progress-section">
        <div className="progress-section-heading">
          <div>
            <span>LMS ENGAGEMENT</span>
            <h2>Weekly activity</h2>
          </div>

          <span className="lms-total">{totalLmsMinutes} minutes</span>
        </div>

        <div className="lms-chart">
          {lmsActivity.map((item) => {
            const maxMinutes = Math.max(
              ...lmsActivity.map((activity) => Number(activity.minutes) || 0),
            );

            const height = maxMinutes ? (item.minutes / maxMinutes) * 100 : 0;

            return (
              <div className="lms-day" key={item.date}>
                <div className="lms-bar-container">
                  <div
                    className="lms-bar"
                    style={{
                      height: `${height}%`,
                    }}
                    title={`${item.minutes} minutes`}
                  />
                </div>

                <strong>{item.minutes}m</strong>

                <span>{item.date}</span>
              </div>
            );
          })}
        </div>
      </section>
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
