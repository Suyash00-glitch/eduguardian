import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  FolderPlus,
  Send,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  History,
  ChevronDown,
  Users,
  BookOpen,
  Zap,
  Target,
  FileText,
  Link2,
  Search,
  Clock,
  UploadCloud,
  File,
  X,
  Sparkles,
} from "lucide-react";
import { useTeacher } from "../../context/TeacherContext";

// ── Custom Dropdown ──
function CustomSelect({ value, onChange, options }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const selected = options.find((o) => o.value === value) || options[0];

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button
        type="button"
        onClick={() => setOpen((p) => !p)}
        style={{
          width: "100%",
          background: "var(--surface)",
          border: "1.5px solid var(--border)",
          borderRadius: "8px",
          padding: "11px 14px",
          color: "var(--text)",
          fontSize: "13px",
          fontWeight: 500,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "8px",
          textAlign: "left",
          transition: "border-color 0.2s",
        }}
      >
        <span>{selected.label}</span>
        <ChevronDown
          size={14}
          style={{
            color: "var(--text-muted)",
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.2s",
          }}
        />
      </button>

      {open && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            right: 0,
            background: "var(--surface)",
            border: "1.5px solid var(--border)",
            borderRadius: "8px",
            boxShadow: "0 12px 40px rgba(0,0,0,0.5)",
            zIndex: 9999,
            overflow: "hidden",
          }}
        >
          {options.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => {
                onChange(opt.value);
                setOpen(false);
              }}
              style={{
                width: "100%",
                background: opt.value === value ? "rgba(0,213,155,0.15)" : "transparent",
                border: "none",
                padding: "10px 14px",
                color: opt.value === value ? "var(--primary)" : "var(--text)",
                fontSize: "13px",
                cursor: "pointer",
                textAlign: "left",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                transition: "background 0.15s",
              }}
              onMouseEnter={(e) => {
                if (opt.value !== value) e.currentTarget.style.background = "rgba(255,255,255,0.05)";
              }}
              onMouseLeave={(e) => {
                if (opt.value !== value) e.currentTarget.style.background = "transparent";
              }}
            >
              <span style={{ fontSize: "15px" }}>{opt.icon}</span>
              <span>{opt.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Styled Input ──
function StyledInput({ type = "text", placeholder, value, onChange, required, icon: Icon }) {
  return (
    <div style={{ position: "relative" }}>
      {Icon && (
        <Icon
          size={13}
          style={{
            position: "absolute",
            left: "12px",
            top: "50%",
            transform: "translateY(-50%)",
            color: "var(--text-muted)",
            pointerEvents: "none",
          }}
        />
      )}
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        required={required}
        style={{
          width: "100%",
          background: "var(--surface)",
          border: "1.5px solid var(--border)",
          borderRadius: "8px",
          padding: Icon ? "11px 14px 11px 34px" : "11px 14px",
          color: "var(--text)",
          fontSize: "13px",
          outline: "none",
          boxSizing: "border-box",
          transition: "border-color 0.2s",
        }}
        onFocus={(e) => (e.target.style.borderColor = "var(--primary)")}
        onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
      />
    </div>
  );
}

// ── Styled Textarea ──
function StyledTextarea({ placeholder, value, onChange, rows = 3 }) {
  return (
    <textarea
      rows={rows}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      style={{
        width: "100%",
        background: "var(--surface)",
        border: "1.5px solid var(--border)",
        borderRadius: "8px",
        padding: "11px 14px",
        color: "var(--text)",
        fontSize: "13px",
        outline: "none",
        resize: "vertical",
        boxSizing: "border-box",
        fontFamily: "inherit",
        lineHeight: 1.5,
        transition: "border-color 0.2s",
      }}
      onFocus={(e) => (e.target.style.borderColor = "var(--primary)")}
      onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
    />
  );
}

const TARGET_OPTIONS = [
  { value: "ALL",              label: "Entire cohort (all students)",  icon: "🌐" },
  { value: "HIGH",             label: "High-risk students only",        icon: "🔴" },
  { value: "MEDIUM",           label: "Medium-risk students only",      icon: "🟡" },
  { value: "LOW",              label: "Low-risk students only",         icon: "🟢" },
  { value: "MY_MENTEES",       label: "My assigned mentees only",       icon: "👤" },
  { value: "SPECIFIC_STUDENT", label: "Specific student",               icon: "🎯" },
];

const TARGET_BADGE = {
  ALL:              { bg: "rgba(0,213,155,0.15)",  color: "var(--primary)" },
  HIGH:             { bg: "rgba(239,68,68,0.15)",  color: "#f87171" },
  MEDIUM:           { bg: "rgba(245,158,11,0.15)", color: "#fbbf24" },
  LOW:              { bg: "rgba(34,197,94,0.15)",  color: "#4ade80" },
  MY_MENTEES:       { bg: "rgba(56,189,248,0.15)", color: "#38bdf8" },
  SPECIFIC_STUDENT: { bg: "rgba(56,189,248,0.15)", color: "#38bdf8" },
};

export default function Interventions() {
  const { active } = useTeacher();
  const [dispatchMode, setDispatchMode] = useState("file"); // "file" | "url"
  const [selectedFile, setSelectedFile] = useState(null);
  const [targetAudience, setTargetAudience] = useState("ALL");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [link, setLink] = useState("");

  const [students, setStudents] = useState([]);
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [studentSearch, setStudentSearch] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  const fileInputRef = useRef(null);

  const fetchStudents = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:5000/api/students/roster?page=1&page_size=200&risk=all", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setStudents(data.students || []);
        if (data.students?.length > 0) setSelectedStudentId(data.students[0].id);
      }
    } catch (e) {
      console.warn("Could not load roster:", e);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:5000/api/interventions/history", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setHistory(data.history || []);
      }
    } catch (e) {
      console.warn("Could not load dispatch history:", e);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    fetchStudents();
    fetchHistory();
  }, [fetchStudents, fetchHistory]);

  function handleFileChange(e) {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 25 * 1024 * 1024) {
        setError("File is too large. Maximum supported size is 25 MB.");
        return;
      }
      setSelectedFile(file);
      setError("");
      if (!title) {
        const baseName = file.name.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " ");
        setTitle(baseName);
      }
    }
  }

  async function handleSend(e) {
    e.preventDefault();
    if (!title.trim()) {
      setError("Please specify the material title.");
      return;
    }
    if (dispatchMode === "file" && !selectedFile) {
      setError("Please select a file to upload.");
      return;
    }
    if (dispatchMode === "url" && !link.trim()) {
      setError("Please enter a valid resource URL link.");
      return;
    }
    if (targetAudience === "SPECIFIC_STUDENT" && !selectedStudentId) {
      setError("Please select a specific student.");
      return;
    }

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      const token = localStorage.getItem("token");
      const formData = new FormData();
      formData.append("target_category", targetAudience);
      formData.append("title", title.trim());
      formData.append("description", description.trim() || "Course learning material shared by faculty.");

      if (dispatchMode === "file" && selectedFile) {
        formData.append("file", selectedFile);
      } else if (dispatchMode === "url" && link.trim()) {
        formData.append("resource_url", link.trim());
      }

      if (targetAudience === "SPECIFIC_STUDENT" && selectedStudentId) {
        formData.append("target_student_id", selectedStudentId);
      }

      const res = await fetch("http://localhost:5000/api/interventions/resource", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.message || "Failed to dispatch resource.");

      setSuccess(`✓ Material successfully dispatched! Reached ${data.students_reached} student portal${data.students_reached !== 1 ? "s" : ""}.`);
      setTitle("");
      setDescription("");
      setLink("");
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      await fetchHistory();
      setTimeout(() => setSuccess(""), 6000);
    } catch (err) {
      setError(err.message || "Could not dispatch resource.");
    } finally {
      setSubmitting(false);
    }
  }

  const filteredStudents = students.filter(
    (s) =>
      (s.name || "").toLowerCase().includes(studentSearch.toLowerCase()) ||
      (s.usn || "").toLowerCase().includes(studentSearch.toLowerCase())
  );

  const selectedStudentObj = students.find((s) => String(s.id) === String(selectedStudentId));

  return (
    <div style={{ padding: "0" }}>
      {/* Header */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
          <span style={{ fontSize: "10px", letterSpacing: "1.5px", color: "var(--primary)", fontWeight: 700, textTransform: "uppercase" }}>
            FAST-TRACK INTERVENTION DISPATCH
          </span>
        </div>
        <h2 style={{ fontSize: "22px", fontWeight: 700, color: "#f1f5f9", margin: 0, marginBottom: "4px" }}>
          Resource Dispatch Center
        </h2>
        <p style={{ fontSize: "13px", color: "#64748b", margin: 0 }}>
          Target and deliver remediation notes, lecture slides, and practice materials directly to student portals.
        </p>
      </div>

      {/* Alerts */}
      {success && (
        <div style={{
          background: "rgba(16,185,129,0.12)",
          border: "1px solid rgba(16,185,129,0.35)",
          color: "#34d399",
          padding: "12px 16px",
          borderRadius: "10px",
          marginBottom: "16px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          fontSize: "13px",
          fontWeight: 500,
        }}>
          <CheckCircle2 size={16} />
          <span>{success}</span>
        </div>
      )}
      {error && (
        <div style={{
          background: "rgba(239,68,68,0.12)",
          border: "1px solid rgba(239,68,68,0.35)",
          color: "#f87171",
          padding: "12px 16px",
          borderRadius: "10px",
          marginBottom: "16px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          fontSize: "13px",
          fontWeight: 500,
        }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1.25fr 1fr", gap: "20px", alignItems: "start" }}>
        {/* ── DISPATCH FORM ── */}
        <div style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "14px",
          overflow: "hidden",
        }}>
          {/* Panel header */}
          <div style={{
            background: "var(--surface-soft)",
            borderBottom: "1px solid var(--border)",
            padding: "16px 20px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}>
            <div style={{
              width: "32px", height: "32px",
              background: "var(--primary-soft)",
              borderRadius: "8px",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <Send size={14} style={{ color: "var(--primary)" }} />
            </div>
            <div>
              <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--text)" }}>Create &amp; Dispatch Resource</div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Fill in the form below and hit Dispatch</div>
            </div>
          </div>

          <form onSubmit={handleSend} style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
            {/* Target audience */}
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "8px", letterSpacing: "0.5px", textTransform: "uppercase" }}>
                <Target size={10} style={{ marginRight: "5px", verticalAlign: "middle" }} />
                Target Audience
              </label>
              <CustomSelect
                value={targetAudience}
                onChange={setTargetAudience}
                options={TARGET_OPTIONS}
              />
            </div>

            {/* Specific student picker */}
            {targetAudience === "SPECIFIC_STUDENT" && (
              <div style={{
                background: "var(--primary-soft)",
                border: "1px solid rgba(0, 213, 155, 0.25)",
                borderRadius: "10px",
                padding: "14px",
              }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "var(--primary)", marginBottom: "10px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  Select Specific Student *
                </label>
                {/* Search */}
                <div style={{ position: "relative", marginBottom: "10px" }}>
                  <Search size={12} style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)", pointerEvents: "none" }} />
                  <input
                    type="text"
                    placeholder="Search by name or USN..."
                    value={studentSearch}
                    onChange={(e) => setStudentSearch(e.target.value)}
                    style={{
                      width: "100%",
                      background: "var(--surface)",
                      border: "1.5px solid var(--border)",
                      borderRadius: "7px",
                      padding: "9px 12px 9px 30px",
                      color: "var(--text)",
                      fontSize: "12px",
                      outline: "none",
                      boxSizing: "border-box",
                    }}
                    onFocus={(e) => (e.target.style.borderColor = "var(--primary)")}
                    onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
                  />
                </div>

                {/* Student list */}
                <div style={{ maxHeight: "160px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "4px" }}>
                  {filteredStudents.length === 0 ? (
                    <div style={{ textAlign: "center", color: "#64748b", fontSize: "12px", padding: "12px" }}>No students found</div>
                  ) : (
                    filteredStudents.map((s) => (
                      <button
                        key={s.id}
                        type="button"
                        onClick={() => setSelectedStudentId(s.id)}
                        style={{
                          background: String(s.id) === String(selectedStudentId) ? "rgba(99,102,241,0.2)" : "rgba(255,255,255,0.03)",
                          border: String(s.id) === String(selectedStudentId) ? "1px solid rgba(99,102,241,0.4)" : "1px solid transparent",
                          borderRadius: "7px",
                          padding: "8px 10px",
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          gap: "8px",
                          textAlign: "left",
                          width: "100%",
                          transition: "all 0.15s",
                        }}
                      >
                        <div>
                          <div style={{ fontSize: "12px", fontWeight: 600, color: String(s.id) === String(selectedStudentId) ? "var(--primary)" : "#e2e8f0" }}>
                            {s.name}
                          </div>
                          <div style={{ fontSize: "10px", color: "#64748b" }}>{s.usn}</div>
                        </div>
                        <span style={{
                          fontSize: "9px",
                          fontWeight: 700,
                          padding: "2px 5px",
                          borderRadius: "4px",
                          background: s.data_source === "student_portal" ? "rgba(34,197,94,0.15)" : "rgba(100,116,139,0.15)",
                          color: s.data_source === "student_portal" ? "#4ade80" : "#94a3b8",
                        }}>
                          {s.data_source === "student_portal" ? "PORTAL" : "DEMO"}
                        </span>
                      </button>
                    ))
                  )}
                </div>

                {selectedStudentObj && (
                  <div style={{ marginTop: "10px", padding: "8px 10px", background: "rgba(99,102,241,0.08)", borderRadius: "6px", fontSize: "11px", color: "#94a3b8" }}>
                    Selected: <strong style={{ color: "var(--primary)" }}>{selectedStudentObj.name}</strong> ({selectedStudentObj.usn})
                  </div>
                )}
              </div>
            )}

            {/* Dispatch Mode Selector */}
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "8px", letterSpacing: "0.5px", textTransform: "uppercase" }}>
                Resource Type / Delivery Mode
              </label>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                <button
                  type="button"
                  onClick={() => setDispatchMode("file")}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "8px",
                    padding: "10px 14px",
                    borderRadius: "8px",
                    border: dispatchMode === "file" ? "1.5px solid var(--primary)" : "1px solid var(--border)",
                    background: dispatchMode === "file" ? "rgba(0, 213, 155, 0.12)" : "var(--surface)",
                    color: dispatchMode === "file" ? "var(--primary)" : "var(--text-secondary)",
                    fontWeight: 600,
                    fontSize: "12px",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                  }}
                >
                  <UploadCloud size={16} />
                  <span>Upload File (PDF / DOC / PPT)</span>
                </button>

                <button
                  type="button"
                  onClick={() => setDispatchMode("url")}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "8px",
                    padding: "10px 14px",
                    borderRadius: "8px",
                    border: dispatchMode === "url" ? "1.5px solid var(--primary)" : "1px solid var(--border)",
                    background: dispatchMode === "url" ? "rgba(0, 213, 155, 0.12)" : "var(--surface)",
                    color: dispatchMode === "url" ? "var(--primary)" : "var(--text-secondary)",
                    fontWeight: 600,
                    fontSize: "12px",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                  }}
                >
                  <Link2 size={16} />
                  <span>External Link (Drive / Web)</span>
                </button>
              </div>
            </div>

            {/* File Upload Zone */}
            {dispatchMode === "file" && (
              <div>
                <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "8px", letterSpacing: "0.5px", textTransform: "uppercase" }}>
                  Select Document / Resource File *
                </label>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  style={{ display: "none" }}
                  accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.zip,.rar,.txt,.png,.jpg,.jpeg,.py,.java,.c,.cpp"
                />

                {!selectedFile ? (
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    style={{
                      border: "2px dashed var(--border)",
                      borderRadius: "10px",
                      padding: "24px 16px",
                      textAlign: "center",
                      background: "var(--surface-soft)",
                      cursor: "pointer",
                      transition: "border-color 0.2s ease, background 0.2s ease",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = "var(--primary)";
                      e.currentTarget.style.background = "rgba(0, 213, 155, 0.05)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = "var(--border)";
                      e.currentTarget.style.background = "var(--surface-soft)";
                    }}
                  >
                    <UploadCloud size={32} style={{ color: "var(--primary)", margin: "0 auto 8px", display: "block" }} />
                    <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text)" }}>
                      Click or drag files here to upload
                    </div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
                      Supports PDF, DOCX, PPTX, XLSX, ZIP, and source code (up to 25 MB)
                    </div>
                  </div>
                ) : (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "12px 16px",
                      borderRadius: "10px",
                      background: "rgba(0, 213, 155, 0.08)",
                      border: "1.5px solid rgba(0, 213, 155, 0.3)",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "10px", overflow: "hidden" }}>
                      <File size={20} style={{ color: "var(--primary)", flexShrink: 0 }} />
                      <div style={{ overflow: "hidden" }}>
                        <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text)", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                          {selectedFile.name}
                        </div>
                        <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                          {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB · {selectedFile.type || "Document"}
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedFile(null);
                        if (fileInputRef.current) fileInputRef.current.value = "";
                      }}
                      style={{
                        background: "rgba(239, 68, 68, 0.15)",
                        border: "none",
                        borderRadius: "6px",
                        color: "#ef4444",
                        padding: "6px",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                      title="Remove file"
                    >
                      <X size={14} />
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Resource Link (URL Mode) */}
            {dispatchMode === "url" && (
              <div>
                <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "8px", letterSpacing: "0.5px", textTransform: "uppercase" }}>
                  <Link2 size={10} style={{ marginRight: "5px", verticalAlign: "middle" }} />
                  Resource Web / Drive URL *
                </label>
                <StyledInput
                  type="url"
                  placeholder="https://drive.google.com/... or https://lms.university.edu/..."
                  value={link}
                  onChange={(e) => setLink(e.target.value)}
                  required
                  icon={Link2}
                />
              </div>
            )}

            {/* Material title */}
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "8px", letterSpacing: "0.5px", textTransform: "uppercase" }}>
                <FileText size={10} style={{ marginRight: "5px", verticalAlign: "middle" }} />
                Material Title *
              </label>
              <StyledInput
                placeholder="e.g. Unit 3 Remedial Notes – OS Process Synchronization"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                icon={BookOpen}
              />
            </div>

            {/* Description */}
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "8px", letterSpacing: "0.5px", textTransform: "uppercase" }}>
                Description &amp; Key Study Focus
              </label>
              <StyledTextarea
                placeholder="e.g. Focus on Semaphores, Banker's Deadlock Algorithm, and Peterson's Solution practice problems."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
              />
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={submitting}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
                background: submitting ? "var(--surface-soft)" : "var(--primary)",
                color: "#03251c",
                border: "none",
                borderRadius: "10px",
                padding: "13px",
                fontSize: "13px",
                fontWeight: 700,
                cursor: submitting ? "not-allowed" : "pointer",
                marginTop: "4px",
                letterSpacing: "0.3px",
                boxShadow: submitting ? "none" : "0 4px 20px rgba(0, 213, 155, 0.25)",
                transition: "all 0.2s",
              }}
            >
              <Send size={14} />
              <span>{submitting ? "Uploading & Dispatching to Portals..." : "Dispatch to Student Portals"}</span>
            </button>
          </form>
        </div>

        {/* ── DISPATCH HISTORY ── */}
        <div style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "14px",
          overflow: "hidden",
        }}>
          {/* Panel header */}
          <div style={{
            background: "var(--surface-soft)",
            borderBottom: "1px solid var(--border)",
            padding: "16px 20px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div style={{
                width: "32px", height: "32px",
                background: "rgba(56,189,248,0.15)",
                borderRadius: "8px",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <History size={14} style={{ color: "#38bdf8" }} />
              </div>
              <div>
                <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--text)" }}>Dispatch Audit Log</div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Live audit trail of dispatched learning resources</div>
              </div>
            </div>
            <div style={{
              background: "rgba(0,213,155,0.15)",
              color: "var(--primary)",
              fontSize: "11px",
              fontWeight: 700,
              padding: "3px 10px",
              borderRadius: "20px",
            }}>
              {history.length} {history.length === 1 ? "Item" : "Items"}
            </div>
          </div>

          <div style={{ padding: "16px", maxHeight: "560px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "10px" }}>
            {loadingHistory ? (
              <div style={{ padding: "24px", textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>
                <Zap size={16} style={{ marginBottom: "8px", display: "block", margin: "0 auto 8px" }} />
                Loading dispatch log...
              </div>
            ) : history.length === 0 ? (
              <div style={{ padding: "32px", textAlign: "center" }}>
                <FolderPlus size={28} style={{ color: "var(--text-muted)", marginBottom: "10px" }} />
                <div style={{ color: "var(--text)", fontSize: "13px", fontWeight: 600 }}>No materials dispatched yet</div>
                <div style={{ color: "var(--text-muted)", fontSize: "12px", marginTop: "4px" }}>Dispatched PDFs, notes, and links will appear here.</div>
              </div>
            ) : (
              history.map((item, idx) => {
                const badge = TARGET_BADGE[item.target] || TARGET_BADGE.ALL;
                return (
                  <div
                    key={idx}
                    style={{
                      background: "var(--surface-soft)",
                      border: "1px solid var(--border)",
                      borderRadius: "10px",
                      padding: "14px 16px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      transition: "border-color 0.2s",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "8px" }}>
                      <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text)", lineHeight: 1.4 }}>
                        {item.title}
                      </div>
                      <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                        <span style={{
                          background: "rgba(255, 255, 255, 0.08)",
                          color: "var(--text)",
                          fontSize: "9px",
                          fontWeight: 700,
                          padding: "2px 6px",
                          borderRadius: "4px",
                          textTransform: "uppercase",
                        }}>
                          {item.type || "PDF"}
                        </span>
                        <span style={{
                          background: badge.bg,
                          color: badge.color,
                          fontSize: "9px",
                          fontWeight: 700,
                          padding: "2px 6px",
                          borderRadius: "4px",
                          whiteSpace: "nowrap",
                        }}>
                          {item.target}
                        </span>
                      </div>
                    </div>

                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <Users size={11} style={{ color: "var(--text-muted)" }} />
                        <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                          Reached <strong style={{ color: "var(--text)" }}>{item.students_reached}</strong> student portal{item.students_reached !== 1 ? "s" : ""}
                        </span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "11px", color: "var(--text-muted)" }}>
                        <Clock size={10} />
                        <span>
                          {item.date
                            ? new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
                            : "Recent"}
                        </span>
                      </div>
                    </div>

                    {item.url && (
                      <div style={{ paddingTop: "4px", borderTop: "1px solid var(--border)" }}>
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "5px",
                            fontSize: "12px",
                            color: "var(--primary)",
                            textDecoration: "none",
                            fontWeight: 600,
                          }}
                        >
                          <ExternalLink size={12} />
                          <span>Open / Download Attached Material</span>
                        </a>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

