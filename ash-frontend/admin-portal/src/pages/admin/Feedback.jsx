import React, { useState } from "react";

export default function Feedback() {
  // TODO backend: replace with GET /api/feedback?department=&semester=&section=
  const [feedbackList] = useState([
    { id: 1, student: "Rahul Verma", type: "Academic Help", message: "I am struggling to catch up on missed LMS assignments due to medical leave.", date: "2026-08-14", status: "Pending" },
    { id: 2, student: "Priya Sharma", type: "Suggestion", message: "Could we get extra practice quizzes for upcoming midterm topics?", date: "2026-08-13", status: "Reviewed" },
  ]);

  return (
    <div className="feedback-page">
      <div className="feedback-header">
        <span className="dashboard-eyebrow">STUDENT VOICE</span>
        <h2>Student Feedback &amp; Support Log</h2>
        <p>Direct feedback, issues, and suggestions submitted by students.</p>
      </div>

      <div className="teacher-panel">
        <div className="feedback-list">
          {feedbackList.map((item) => (
            <div className="feedback-row" key={item.id}>
              <div className="feedback-main">
                <div className="feedback-meta">
                  <strong>{item.student}</strong>
                  <span className="feedback-type">{item.type}</span>
                  <span className="feedback-date">{item.date}</span>
                </div>
                <p>{item.message}</p>
              </div>
              <span className={`feedback-status ${item.status.toLowerCase()}`}>{item.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
