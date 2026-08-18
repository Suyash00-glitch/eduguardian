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
  RotateCcw,
} from "lucide-react";

import { studentService } from "../services/studentService";

function formatDate(date) {
  return new Date(date).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function formatDateTime(date) {
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
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [submitting, setSubmitting] = useState(false);
const [submitError, setSubmitError] = useState("");

  const fileInputRef = useRef(null);

  const MAX_FILE_SIZE = 10 * 1024 * 1024;

  const ALLOWED_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
  ];

 
   
  useEffect(() => {
  async function loadAssignment() {
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
  }

  loadAssignment();
}, [assignmentId]);


  const validateFile = (file) => {
    setUploadError("");

    if (!file) {
      return false;
    }

    if (!ALLOWED_TYPES.includes(file.type)) {
      setUploadError(
        "Unsupported file type. Please upload a PDF or DOCX file.",
      );

      return false;
    }

    if (file.size > MAX_FILE_SIZE) {
      setUploadError("File is too large. The maximum allowed size is 10 MB.");

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
  const handleDragOver = (event) => {
    event.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setDragActive(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();

    setDragActive(false);

    const file = event.dataTransfer.files?.[0];

    handleFileSelect(file);
  };


 const handleSubmitAssignment = async () => {
  if (!selectedFile) {
    setSubmitError("Please select a file first.");
    return;
  }

  try {
    setSubmitting(true);
    setSubmitError("");

    const token =
      localStorage.getItem("eduguardian_token") ||
      sessionStorage.getItem("eduguardian_token");

    const formData = new FormData();

    formData.append("file", selectedFile);

    const response = await fetch(
      `http://localhost:8000/api/assignments/student/${assignmentId}/submit`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "Unable to submit assignment."
      );
    }

    setSubmitted(true);

    // reload assignment so uploaded file appears
    const updated = await studentService.getAssignment(
      assignmentId
    );

    setAssignment(updated);

  } catch (err) {
    console.error("submission failed:", err);
    setSubmitError(
      err.message || "Unable to submit assignment."
    );
  } finally {
    setSubmitting(false);
  }
};


  const resetSubmission = () => {
    setSelectedFile(null);
    setUploadProgress(0);
    setUploading(false);
    setSubmitted(false);
    setUploadError("");
  };


  if (loading) {
  return (
    <div className="assignment-details-page">
      <div className="assignment-not-found">
        <h2>Loading assignment...</h2>
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

      <div className="assignment-not-found">
        <AlertCircle size={36} />

        <h2>Assignment not found</h2>

        <p>
          {loadError || "The assignment you're looking for could not be found."}
        </p>
      </div>
    </div>
  );
}

  const isSubmitted = assignment.submissionStatus === "submitted";

  const isMissed = assignment.submissionStatus === "missed";

  return (
    <div className="assignment-details-page">
      {/* BACK */}

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
          <span className="assignment-details-eyebrow">
            {assignment.subjectCode}
          </span>

          <span className="assignment-details-subject">
            {assignment.subjectName}
          </span>

          <h1>{assignment.title}</h1>

          <p>{assignment.description}</p>
        </div>

        <span className={`assignment-status ${assignment.status}`}>
          {assignment.status === "pending" && "Pending"}

          {assignment.status === "submitted" && "Submitted"}

          {assignment.status === "overdue" && "Overdue"}
        </span>
      </div>

      {/* INFO */}

      <div className="assignment-detail-info">
        <div>
          <CalendarDays size={17} />

          <div>
            <span>Due date</span>

            <strong>{formatDate(assignment.dueDate)}</strong>
          </div>
        </div>

        <div>
          <Clock3 size={17} />

          <div>
            <span>Deadline</span>

            <strong>
              {new Date(assignment.dueDate).toLocaleTimeString("en-IN", {
                hour: "numeric",
                minute: "2-digit",
              })}
            </strong>
          </div>
        </div>

        <div>
          <ClipboardList size={17} />

          <div>
            <span>Maximum marks</span>

            <strong>{assignment.maxMarks}</strong>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}

      <div className="assignment-details-grid">
        {/* INSTRUCTIONS */}

        <section className="assignment-detail-card">
          <div className="assignment-detail-card-header">
            <div>
              <span>ASSIGNMENT</span>

              <h2>Instructions</h2>
            </div>

            <FileText size={19} />
          </div>

          <div className="assignment-instructions">
            <p>
              Complete the assignment according to the instructions provided by
              your mentor.
            </p>

            <ul>
              <li>Complete all required questions.</li>
              <li>Use the required format for your submission.</li>
              <li>Review your work before submitting.</li>
              <li>Submit the final file before the deadline.</li>
            </ul>
          </div>
        </section>

        {/* SUBMISSION */}

        <section className="assignment-detail-card">
          <div className="assignment-detail-card-header">
            <div>
              <span>SUBMISSION</span>

              <h2>Submission Status</h2>
            </div>

            {isSubmitted ? <CheckCircle2 size={19} /> : <Upload size={19} />}
          </div>

          {isSubmitted && (
            <div className="assignment-submitted-state">
              <div className="submission-success-icon">
                <CheckCircle2 size={24} />
              </div>

              <strong>Assignment submitted</strong>

             

              {assignment.marks !== undefined && (
                <div className="submission-marks">
                  <span>Marks</span>

                  <strong>
                    {assignment.marks} / {assignment.maxMarks}
                  </strong>
                </div>
              )}
            </div>
          )}

          {showSubmission && (
            <section className="assignment-submission-panel">
              <div className="submission-panel-header">
                <div>
                  <span>SUBMISSION</span>

                  <h2>Submit your assignment</h2>

                  <p>Upload your completed assignment before the deadline.</p>
                </div>

                <button
                  type="button"
                  className="submission-close-button"
                  onClick={() => {
                    if (!uploading) {
                      setShowSubmission(false);
                      resetSubmission();
                    }
                  }}
                  disabled={uploading}
                >
                  <X size={18} />
                </button>
              </div>

              {!submitted && !uploading && (
                <>
                  <div
                    className={`assignment-dropzone ${
                      dragActive ? "drag-active" : ""
                    } ${selectedFile ? "has-file" : ""}`}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.doc,.docx"
                      hidden
                      onChange={(event) => {
                        const file = event.target.files?.[0];

                        handleFileSelect(file);

                        event.target.value = "";
                      }}
                    />

                    {!selectedFile ? (
                      <>
                        <div className="dropzone-icon">
                          <UploadCloud size={26} />
                        </div>

                        <strong>Drop your assignment here</strong>

                        <span>or click to browse files</span>

                        <small>PDF or DOCX · Maximum 10 MB</small>
                      </>
                    ) : (
                      <div className="selected-file">
                        <div className="selected-file-icon">
                          <FileCheck2 size={22} />
                        </div>

                        <div className="selected-file-info">
                          <strong>{selectedFile.name}</strong>

                          <span>
                            {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                          </span>
                        </div>

                        <button
                          type="button"
                          className="remove-file-button"
                          onClick={(event) => {
                            event.stopPropagation();
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
                    <div className="submission-error">
                      <AlertCircle size={15} />

                      <span>{uploadError}</span>
                    </div>
                  )}

                  <div className="submission-actions">
                    <button
                      type="button"
                      className="submission-cancel-button"
                      onClick={() => {
                        setShowSubmission(false);
                        resetSubmission();
                      }}
                    >
                      Cancel
                    </button>

                    <button
  type="button"
  onClick={handleSubmitAssignment}
  disabled={!selectedFile || submitting}
>
  {submitting ? "Uploading..." : "Submit Assignment"}
</button>
                  </div>
                </>
              )}

              {uploading && (
                <div className="submission-uploading">
                  <div className="uploading-icon">
                    <UploadCloud size={25} />
                  </div>

                  <strong>Uploading your assignment...</strong>

                  <span>Please don't close this page.</span>

                  <div className="upload-progress">
                    <div
                      className="upload-progress-bar"
                      style={{
                        width: `${uploadProgress}%`,
                      }}
                    />
                  </div>

                  <div className="upload-progress-info">
                    <span>Uploading</span>

                    <strong>{uploadProgress}%</strong>
                  </div>
                </div>
              )}

              {submitted && (
                <div className="submission-success">
                  <div className="submission-success-large">
                    <CheckCircle2 size={32} />
                  </div>

                  <strong>Assignment submitted successfully</strong>

                  <span>
                    Your submission has been recorded locally for this demo.
                  </span>

                  <div className="submitted-file-preview">
                    <FileCheck2 size={18} />

                    <div>
                      <strong>{selectedFile?.name}</strong>

                      <span>Submission ready for mentor review</span>
                    </div>
                  </div>

                  <button
                    type="button"
                    className="submission-done-button"
                    onClick={() => {
                      setShowSubmission(false);
                      resetSubmission();
                    }}
                  >
                    Done
                  </button>
                </div>
              )}
            </section>
          )}

          {!isSubmitted && !isMissed && !showSubmission && !submitted && (
            <div className="assignment-pending-state">
              <div className="submission-pending-icon">
                <Upload size={22} />
              </div>

              <strong>Not submitted yet</strong>

              <span>
                Your submission will appear here once you upload the assignment.
              </span>

              <button
                type="button"
                className="assignment-submit-button"
                onClick={() => setShowSubmission(true)}
              >
                <Upload size={15} />
                Submit Assignment
              </button>
            </div>
          )}

          {isMissed && (
            <div className="assignment-missed-state">
              <AlertCircle size={23} />

              <strong>Submission missed</strong>

              <span>The submission deadline has passed.</span>
            </div>
          )}
        </section>
      </div>

      {/* ATTACHMENTS */}

      {assignment.resourceUrl && (
  <section className="assignment-detail-card assignment-attachments">
    <div className="assignment-detail-card-header">
      <div>
        <span>FILES</span>
        <h2>Assignment Resources</h2>
      </div>

      <FileText size={19} />
    </div>

    <div className="assignment-resource-item">
      <div className="resource-file-icon">
        <FileText size={17} />
      </div>

      <div>
        <strong>
          {assignment.resourceName || "Assignment Resource"}
        </strong>

        <span>
          {assignment.resourceName?.toLowerCase().endsWith(".pdf")
            ? "PDF"
            : assignment.resourceName?.toLowerCase().endsWith(".png")
            ? "PNG"
            : assignment.resourceName?.toLowerCase().endsWith(".jpg") ||
              assignment.resourceName?.toLowerCase().endsWith(".jpeg")
            ? "Image"
            : "File"}{" "}
          · Provided by teacher
        </span>
      </div>

      <a
        href={`http://127.0.0.1:8000${assignment.resourceUrl}`}
        target="_blank"
        rel="noopener noreferrer"
        className="resource-action"
      >
        View / Download
      </a>
    </div>
  </section>
)}
    </div>
  );
}

export default AssignmentDetails;
