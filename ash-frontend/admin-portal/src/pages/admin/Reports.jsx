import React, { useState } from "react";
import { FileDown, FileText, Clock, CheckCircle2 } from "lucide-react";

export default function Reports() {
  const [downloadHistory, setDownloadHistory] = useState([
    { id: 1, fileName: "EduGuardian_Cohort_Report_2026-08-14.csv", type: "CSV Batch Export", timestamp: "2026-08-14 10:15 AM", status: "Completed" },
  ]);

  async function handleDownload(fileType) {
    let fileContent = "";
    let fileName = "";
    const dateStr = new Date().toISOString().split("T")[0];

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:5000/api/students/roster?page=1&page_size=200", {
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
      });

      let studentList = [];
      if (res.ok) {
        const data = await res.json();
        studentList = data.students || [];
      }

      if (fileType === "CSV") {
        fileName = `EduGuardian_Cohort_Report_${dateStr}.csv`;
        const headers = "USN,StudentName,Department,Semester,CGPA,LatestSGPA,Attendance,Backlogs,RiskLevel,RiskScore,Confidence,RiskBasis\n";
        const rows = studentList.map((s) => {
          const att = s.attendance !== null && s.attendance !== undefined ? `${s.attendance}%` : "Pending";
          return `"${s.usn || ""}","${s.name || ""}","${s.department || "ISE"}",${s.semester || 5},${s.cgpa || ""},${s.latest_sgpa || ""},"${att}",${s.backlogs ?? 0},"${s.risk_level || "LOW"}",${s.risk_score || 0},"${s.confidence || "LOW"}","${s.risk_basis || "historical"}"`;
        });
        fileContent = headers + rows.join("\n");
      } else {
        fileName = `EduGuardian_Cohort_Brief_${dateStr}.txt`;
        const lines = [
          "================================================================================",
          "EDUGUARDIAN AI - FACULTY COHORT RISK & INTERVENTION SUMMARY",
          `Generated: ${new Date().toLocaleString()}`,
          "================================================================================",
          "",
          `Total Students Evaluated: ${studentList.length}`,
          `High Risk Flags: ${studentList.filter((s) => s.risk_level === "HIGH").length}`,
          `Medium Risk: ${studentList.filter((s) => s.risk_level === "MEDIUM").length}`,
          `Low Risk / Stable: ${studentList.filter((s) => s.risk_level === "LOW").length}`,
          "",
          "--- HIGH RISK STUDENTS REQUIRING ATTENTION ---",
          ...studentList
            .filter((s) => s.risk_level === "HIGH")
            .map(
              (s) =>
                `• ${s.name} (${s.usn}) | CGPA: ${s.cgpa || "—"} | Latest SGPA: ${s.latest_sgpa || "—"} | Backlogs: ${s.backlogs ?? 0} | Factors: ${(s.factors || []).join("; ")}`
            ),
          "",
          "Notice: Current-semester attendance and assessment data are pending publication for early-semester profiles.",
        ];
        fileContent = lines.join("\n");
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

      setDownloadHistory((prev) => [
        {
          id: Date.now(),
          fileName,
          type: fileType === "CSV" ? "CSV Batch Export" : "Student Brief (.TXT)",
          timestamp: new Date().toLocaleString(),
          status: "Completed",
        },
        ...prev,
      ]);
    } catch (err) {
      console.error("Export error:", err);
      alert("Failed to generate report: " + err.message);
    }
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
