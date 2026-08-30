import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  CalendarDays,
  ClipboardList,
  Clock3,
  FileText,
  Upload,
  CheckCircle2,
  AlertCircle,
  UploadCloud,
  X,
  FileCheck2,
  Award,
  Lock,
  Download,
  MessageSquare,
} from "lucide-react";
import { studentService } from "../services/studentService";

function formatDate(date) {
  if (!date) return "—";
  return new Date(date).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function formatDateTime(date) {
  if (!date) return "—";
  return new Date(date).toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function AssignmentDetails() {
  const navigate = useNavigate();
  const { assignmentId } = useParams();

  const [assignment, setAssignment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [showSubmission, setShowSubmission] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const fileInputRef = useRef(null);
  const MAX_FILE_SIZE = 15 * 1024 * 1024;
  const ALLOWED_EXTS = [".pdf", ".doc", ".docx", ".zip", ".jpg", ".jpeg", ".png"];

  const loadAssignment = async () => {
    try {
      setLoading(true);
      setLoadError("");
      const data = await studentService.getAssignment(assignmentId);
      setAssignment(data);
    } catch (err) {
      console.error("failed to load assignment:", err);
      setLoadError(err.message || "Unable to load assignment.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssignment();
  }, [assignmentId]);

  const validateFile = (file) => {
    setUploadError("");
    if (!file) return false;

    const name = (file.name || "").toLowerCase();
    const isAllowedExt = ALLOWED_EXTS.some((ext) => name.endsWith(ext));

    if (!isAllowedExt) {
      setUploadError("Unsupported file type. Please upload a PDF, DOCX, ZIP, JPG, or PNG file.");
      return false;
    }

    if (file.size > MAX_FILE_SIZE) {
      setUploadError("File is too large. The maximum allowed size is 15 MB.");
      return false;
    }

    return true;
  };

  const handleFileSelect = (file) => {
    if (!validateFile(file)) {
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
    setUploadError("");
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    handleFileSelect(file);
  };

  const handleSubmitAssignment = async () => {
    if (!selectedFile) {
      setSubmitError("Please select a file to submit.");
      return;
    }

    try {
      setSubmitting(true);
      setSubmitError("");

      const formData = new FormData();
      formData.append("file", selectedFile);

      await studentService.submitAssignment(assignmentId, formData);
      setSubmitSuccess(true);
      setShowSubmission(false);
      setSelectedFile(null);

      // Reload updated assignment details
      await loadAssignment();
    } catch (err) {
      console.error("Submission error:", err);
      setSubmitError(err.message || "Failed to submit assignment.");
    } finally {
      setSubmitting(false);
    }
  };

  const resetSubmission = () => {
    setSelectedFile(null);
    setUploadError("");
    setSubmitError("");
    setSubmitSuccess(false);
  };

  if (loading) {
    return (
      <div className="assignment-details-page">
        <div className="assignment-not-found" style={{ textAlign: "center", padding: "60px 20px" }}>
          <h2>Loading assignment details...</h2>
        </div>
      </div>
    );
  }

  if (loadError || !assignment) {
    return (
      <div className="assignment-details-page">
        <button
          className="assignment-back-button"
          onClick={() => navigate("/assignments")}
        >
          <ArrowLeft size={16} />
          Back to Assignments
        </button>

        <div className="assignment-not-found" style={{ textAlign: "center", padding: "60px 20px" }}>
          <AlertCircle size={36} color="var(--danger, #ef4444)" style={{ margin: "0 auto 12px" }} />
          <h2>Assignment not found</h2>
          <p>{loadError || "The assignment you are looking for could not be found."}</p>
        </div>
      </div>
    );
  }

  const isGraded = assignment.status === "graded" || (assignment.marks !== null && assignment.marks !== undefined);
  const isSubmitted = assignment.status === "submitted" || assignment.submissionStatus === "submitted";
  const isLocked = assignment.isLocked || (assignment.status === "overdue" && !isSubmitted && !isGraded);
  const maxMarks = assignment.maxMarks || 20;
  const marksObtained = assignment.marks ?? assignment.marksObtained;
  const gradePercentage = marksObtained !== null && marksObtained !== undefined ? Math.round((marksObtained / maxMarks) * 100) : null;

  return (
    <div className="assignment-details-page">
      {/* BACK BUTTON */}
      <button
        type="button"
        className="assignment-back-button"
        onClick={() => navigate("/assignments")}
      >
        <ArrowLeft size={16} />
        Back to Assignments
      </button>

      {/* HEADER */}
      <div className="assignment-details-header">
        <div>
          <span className="assignment-details-subject">
            {assignment.subjectCode} · {assignment.subjectName}
          </span>
          <h1>{assignment.title || assignment.assignmentName}</h1>
          <p>{assignment.description || `Assignment coursework for ${assignment.subjectName}`}</p>
        </div>

        <div>
          {isGraded ? (
            <span className="assignment-status graded" style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
              <Award size={14} />
              Graded: {marksObtained} / {maxMarks}
            </span>
          ) : isSubmitted ? (
            <span className="assignment-status submitted" style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
              <CheckCircle2 size={14} />
              Submitted
            </span>
          ) : isLocked ? (
            <span className="assignment-status overdue" style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
              <Lock size={14} />
              Closed / Locked
            </span>
          ) : (
            <span className="assignment-status pending" style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
              <Clock3 size={14} />
              Pending Submission
            </span>
          )}
        </div>
      </div>

      {/* TOP INFO STATS */}
      <div className="assignment-detail-info">
        <div>
          <CalendarDays size={17} />
          <div>
            <span>Due Date</span>
            <strong>{formatDate(assignment.dueDate)}</strong>
          </div>
        </div>

        <div>
          <ClipboardList size={17} />
          <div>
            <span>Maximum Marks</span>
            <strong>{maxMarks} marks</strong>
          </div>
        </div>

        <div>
          <Clock3 size={17} />
          <div>
            <span>Status</span>
            <strong style={{ textTransform: "capitalize" }}>
              {isGraded ? "Graded by Teacher" : isSubmitted ? "Submitted (Pending Review)" : isLocked ? "Closed (Deadline Passed)" : "Open for Submission"}
            </strong>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT GRID */}
      <div className="assignment-details-grid">
        {/* INSTRUCTIONS & DETAILS */}
        <section className="assignment-detail-card">
          <div className="assignment-detail-card-header">
            <div>
              <span>ASSIGNMENT</span>
              <h2>Instructions & Guidelines</h2>
            </div>
            <FileText size={19} />
          </div>

          <div className="assignment-instructions">
            <p>
              Please review all requirements carefully before submitting your coursework. Ensure all problem answers, code snippets, or diagrams are clearly labeled.
            </p>
            <ul>
              <li>Upload your work in PDF, DOCX, JPG, PNG, or ZIP format.</li>
              <li>Maximum file size allowed: 15 MB.</li>
              <li>Strict deadline: Submissions close automatically at the due date.</li>
              <li>Once graded by the faculty, your score and evaluation notes will appear here.</li>
            </ul>
          </div>

          {assignment.resourceUrl && (
            <div style={{ marginTop: "20px", paddingTop: "16px", borderTop: "1px solid var(--border)" }}>
              <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                Faculty Attached Resource
              </span>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "8px", padding: "12px", background: "var(--surface-soft)", borderRadius: "8px", border: "1px solid var(--border)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <FileText size={18} color="var(--primary)" />
                  <strong style={{ fontSize: "13px" }}>{assignment.resourceName || "Assignment Question Paper"}</strong>
                </div>
                <a
                  href={`http://localhost:5000${assignment.resourceUrl}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="attendance-save-button"
                  style={{ textDecoration: "none", fontSize: "12px", padding: "6px 12px" }}
                >
                  <Download size={13} /> View / Download
                </a>
              </div>
            </div>
          )}
        </section>

        {/* SUBMISSION & GRADING CARD */}
        <section className="assignment-detail-card">
          <div className="assignment-detail-card-header">
            <div>
              <span>EVALUATION & SUBMISSION</span>
              <h2>Submission Status</h2>
            </div>
            {isGraded ? <Award size={19} color="var(--primary)" /> : isSubmitted ? <CheckCircle2 size={19} color="var(--primary)" /> : <Upload size={19} />}
          </div>

          {/* 1. GRADED STATE */}
          {isGraded && (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div style={{ background: "rgba(34, 197, 94, 0.08)", border: "1px solid rgba(34, 197, 94, 0.25)", borderRadius: "12px", padding: "20px", textAlign: "center" }}>
                <div style={{ display: "inline-flex", padding: "10px", borderRadius: "50%", background: "rgba(34, 197, 94, 0.15)", marginBottom: "8px" }}>
                  <Award size={32} color="var(--primary)" />
                </div>
                <h3 style={{ margin: "0 0 4px", fontSize: "22px", color: "var(--text)" }}>
                  {marksObtained} / {maxMarks} Marks
                </h3>
                <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--primary)" }}>
                  Score: {gradePercentage}% · Graded & Verified
                </span>

                {assignment.feedback && (
                  <div style={{ marginTop: "14px", padding: "12px", background: "var(--surface)", borderRadius: "8px", border: "1px solid var(--border)", textAlign: "left" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "4px" }}>
                      <MessageSquare size={13} /> Faculty Feedback
                    </div>
                    <p style={{ margin: 0, fontSize: "13px", color: "var(--text)", fontStyle: "italic" }}>
                      "{assignment.feedback}"
                    </p>
                  </div>
                )}
              </div>

              {(assignment.submittedFile || assignment.submission?.fileName) && (
                <div style={{ padding: "12px", background: "var(--surface-soft)", borderRadius: "8px", border: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>YOUR SUBMITTED FILE</div>
                    <strong style={{ fontSize: "13px" }}>
                      {assignment.submittedFile?.name || assignment.submission?.fileName || "Assignment Submission"}
                    </strong>
                  </div>
                  {(assignment.submittedFile?.url || assignment.submission?.fileUrl) && (
                    <a
                      href={`http://localhost:5000${assignment.submittedFile?.url || assignment.submission?.fileUrl}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="attendance-save-button"
                      style={{ textDecoration: "none", fontSize: "12px", padding: "6px 12px" }}
                    >
                      <Download size={13} /> Download Work
                    </a>
                  )}
                </div>
              )}
            </div>
          )}

          {/* 2. SUBMITTED BUT NOT YET GRADED */}
          {!isGraded && isSubmitted && (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div style={{ background: "rgba(34, 197, 94, 0.08)", border: "1px solid rgba(34, 197, 94, 0.2)", borderRadius: "12px", padding: "20px", textAlign: "center" }}>
                <CheckCircle2 size={32} color="var(--primary)" style={{ margin: "0 auto 8px" }} />
                <h3 style={{ margin: "0 0 4px", fontSize: "18px" }}>Assignment Submitted Successfully</h3>
                <span style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                  Submitted on {formatDateTime(assignment.submissionDate || assignment.submission?.submissionDate)}
                </span>
                <p style={{ margin: "10px 0 0", fontSize: "12px", color: "var(--text-muted)" }}>
                  Your submission is queued for faculty grading and feedback.
                </p>
              </div>

              {(assignment.submittedFile || assignment.submission?.fileName) && (
                <div style={{ padding: "12px", background: "var(--surface-soft)", borderRadius: "8px", border: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>UPLOADED FILE</div>
                    <strong style={{ fontSize: "13px" }}>
                      {assignment.submittedFile?.name || assignment.submission?.fileName || "Assignment Submission"}
                    </strong>
                  </div>
                  {(assignment.submittedFile?.url || assignment.submission?.fileUrl) && (
                    <a
                      href={`http://localhost:5000${assignment.submittedFile?.url || assignment.submission?.fileUrl}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="attendance-save-button"
                      style={{ textDecoration: "none", fontSize: "12px", padding: "6px 12px" }}
                    >
                      <Download size={13} /> View File
                    </a>
                  )}
                </div>
              )}

              {!isLocked && (
                <button
                  type="button"
                  className="attendance-save-button"
                  style={{ background: "transparent", color: "var(--text-secondary)", border: "1px solid var(--border)", alignSelf: "center", marginTop: "6px" }}
                  onClick={() => setShowSubmission(true)}
                >
                  <Upload size={13} /> Resubmit Work
                </button>
              )}
            </div>
          )}

          {/* 3. DEADLINE LOCKED / MISSED */}
          {!isGraded && !isSubmitted && isLocked && (
            <div style={{ background: "rgba(239, 68, 68, 0.08)", border: "1px solid rgba(239, 68, 68, 0.25)", borderRadius: "12px", padding: "24px", textAlign: "center" }}>
              <Lock size={36} color="var(--danger, #ef4444)" style={{ margin: "0 auto 10px" }} />
              <h3 style={{ margin: "0 0 6px", color: "var(--danger, #ef4444)", fontSize: "18px" }}>
                Submission Closed & Locked
              </h3>
              <p style={{ margin: "0 0 8px", fontSize: "13px", color: "var(--text-secondary)" }}>
                The submission deadline for this assignment was <strong>{formatDate(assignment.dueDate)}</strong>.
              </p>
              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                Late uploads are disabled per academic policy. Please contact your instructor for exceptions.
              </span>
            </div>
          )}

          {/* 4. OPEN FOR SUBMISSION */}
          {!isGraded && !isSubmitted && !isLocked && !showSubmission && (
            <div className="assignment-pending-state" style={{ textAlign: "center", padding: "30px 16px" }}>
              <div className="submission-pending-icon" style={{ margin: "0 auto 12px" }}>
                <Upload size={24} />
              </div>
              <h3 style={{ margin: "0 0 6px" }}>Ready to Submit?</h3>
              <span style={{ fontSize: "13px", color: "var(--text-secondary)", display: "block", marginBottom: "16px" }}>
                Upload your solution before {formatDate(assignment.dueDate)}.
              </span>

              <button
                type="button"
                className="attendance-save-button"
                style={{ fontSize: "14px", padding: "10px 20px", display: "inline-flex", alignItems: "center", gap: "8px" }}
                onClick={() => setShowSubmission(true)}
              >
                <Upload size={16} /> Select & Upload Assignment
              </button>
            </div>
          )}

          {/* SUBMISSION UPLOAD MODAL / PANEL */}
          {showSubmission && (
            <section className="assignment-submission-panel" style={{ marginTop: "10px" }}>
              <div className="submission-panel-header">
                <div>
                  <h2>Upload Assignment</h2>
                  <p>Choose your completed file (PDF, DOCX, ZIP, or Image, max 15MB).</p>
                </div>
                <button
                  type="button"
                  className="submission-close-button"
                  onClick={() => {
                    setShowSubmission(false);
                    resetSubmission();
                  }}
                  disabled={submitting}
                >
                  <X size={18} />
                </button>
              </div>

              <div
                className={`assignment-dropzone ${dragActive ? "drag-active" : ""} ${selectedFile ? "has-file" : ""}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                style={{ cursor: "pointer" }}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.doc,.docx,.zip,.jpg,.jpeg,.png"
                  hidden
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    handleFileSelect(file);
                    e.target.value = "";
                  }}
                />

                {!selectedFile ? (
                  <>
                    <div className="dropzone-icon">
                      <UploadCloud size={28} />
                    </div>
                    <strong>Click to select file or drag & drop</strong>
                    <span>PDF, DOCX, ZIP, PNG, or JPG (max 15MB)</span>
                  </>
                ) : (
                  <div className="selected-file">
                    <div className="selected-file-icon">
                      <FileCheck2 size={22} />
                    </div>
                    <div className="selected-file-info">
                      <strong>{selectedFile.name}</strong>
                      <span>{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</span>
                    </div>
                    <button
                      type="button"
                      className="remove-file-button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedFile(null);
                        setUploadError("");
                      }}
                    >
                      <X size={16} />
                    </button>
                  </div>
                )}
              </div>

              {uploadError && (
                <div className="submission-error" style={{ marginTop: "10px", color: "var(--danger)" }}>
                  <AlertCircle size={15} />
                  <span>{uploadError}</span>
                </div>
              )}

              {submitError && (
                <div className="submission-error" style={{ marginTop: "10px", color: "var(--danger)" }}>
                  <AlertCircle size={15} />
                  <span>{submitError}</span>
                </div>
              )}

              <div className="submission-actions" style={{ marginTop: "16px", display: "flex", gap: "10px", justifyContent: "flex-end" }}>
                <button
                  type="button"
                  className="submission-cancel-button"
                  onClick={() => {
                    setShowSubmission(false);
                    resetSubmission();
                  }}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="attendance-save-button"
                  onClick={handleSubmitAssignment}
                  disabled={!selectedFile || submitting}
                  style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
                >
                  {submitting ? "Uploading..." : "Confirm & Submit Work"}
                </button>
              </div>
            </section>
          )}
        </section>
      </div>
    </div>
  );
}

export default AssignmentDetails;
