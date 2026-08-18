import React, { useState } from "react";
import { FileDown, FileText, Clock, CheckCircle2 } from "lucide-react";

export default function Reports() {
  const [downloadHistory, setDownloadHistory] = useState([
    { id: 1, fileName: "EduGuardian_Cohort_Report_2026-08-14.csv", type: "CSV Batch Export", timestamp: "2026-08-14 10:15 AM", status: "Completed" },
  ]);

  function handleDownload(fileType) {
    let fileContent = "";
    let fileName = "";

    if (fileType === "CSV") {
      fileName = `EduGuardian_Cohort_Report_${new Date().toISOString().split("T")[0]}.csv`;
      fileContent =
        "StudentID,StudentName,RiskLevel,Attendance,QuizAvg\nSTU-101,Rahul Verma,High,24%,48%\nSTU-102,Priya Sharma,Medium,68%,61%\nSTU-103,Arjun N.,High,20%,40%\nSTU-104,Meera Iyer,Low,94%,88%";
    } else {
      fileName = `EduGuardian_Student_Brief_${new Date().toISOString().split("T")[0]}.txt`;
      fileContent =
        "EDUGUARDIAN AI 2.0 - INDIVIDUAL COMPLIANCE & INTERVENTION BRIEF\n\nStudent: Rahul Verma (STU-101)\nRisk Level: High Risk\nPrimary Drivers: Attendance decline (-35%), Missed LMS submissions (-22%)\nFaculty Recommendation: Assign mentor immediately. Estimated recovery probability: 89%.";
    }

    const blob = new Blob([fileContent], { type: fileType === "CSV" ? "text/csv;charset=utf-8;" : "text/plain;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", fileName);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setDownloadHistory([
      {
        id: Date.now(),
        fileName,
        type: fileType === "CSV" ? "CSV Batch Export" : "Student Brief (.TXT)",
        timestamp: new Date().toLocaleString(),
        status: "Completed",
      },
      ...downloadHistory,
    ]);
  }

  return (
    <div className="reports-page">
      <div className="reports-header">
        <span className="dashboard-eyebrow">EXPORTS</span>
        <h2>Reports &amp; Download Center</h2>
        <p>Batch or individual exports for compliance and audit review.</p>
      </div>

      <div className="reports-grid">
        <div className="teacher-panel report-card">
          <div className="report-card-icon primary"><FileDown size={20} /></div>
          <div>
            <h3>Full Cohort Data (.CSV)</h3>
            <p>Batch export of all student metrics, risk levels, and attendance logs.</p>
          </div>
          <button className="report-download-button primary" onClick={() => handleDownload("CSV")}>
            <FileDown size={14} /> Download Cohort CSV
          </button>
        </div>

        <div className="teacher-panel report-card">
          <div className="report-card-icon neutral"><FileText size={20} /></div>
          <div>
            <h3>Individual Student Brief (.TXT)</h3>
            <p>Compliance and intervention summary report for review.</p>
          </div>
          <button className="report-download-button neutral" onClick={() => handleDownload("PDF")}>
            <FileText size={14} /> Download Student Brief
          </button>
        </div>
      </div>

      <div className="teacher-panel">
        <div className="teacher-panel-header">
          <h3><Clock size={14} className="inline-icon" /> Download History &amp; Audit Log</h3>
        </div>

        <div className="history-table">
          <div className="history-table-head">
            <span>File name</span>
            <span>Export type</span>
            <span>Generated</span>
            <span>Status</span>
          </div>
          {downloadHistory.map((log) => (
            <div className="history-row" key={log.id}>
              <span className="history-filename">{log.fileName}</span>
              <span>{log.type}</span>
              <span>{log.timestamp}</span>
              <span className="history-status"><CheckCircle2 size={12} /> {log.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
