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
} from "lucide-react";
import { useTeacher } from "../../context/TeacherContext";

// ── Custom Dropdown (replaces native <select> to avoid OS contrast issues) ──
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
          background: "#1e293b",
          border: "1.5px solid #334155",
          borderRadius: "8px",
          padding: "11px 14px",
          color: "#f1f5f9",
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
            color: "#94a3b8",
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
            background: "#1e293b",
            border: "1.5px solid #334155",
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
                background: opt.value === value ? "rgba(99,102,241,0.2)" : "transparent",
                border: "none",
                padding: "10px 14px",
                color: opt.value === value ? "#a5b4fc" : "#cbd5e1",
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
            color: "#64748b",
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
          background: "#1e293b",
          border: "1.5px solid #334155",
          borderRadius: "8px",
          padding: Icon ? "11px 14px 11px 34px" : "11px 14px",
          color: "#f1f5f9",
          fontSize: "13px",
          outline: "none",
          boxSizing: "border-box",
          transition: "border-color 0.2s",
        }}
        onFocus={(e) => (e.target.style.borderColor = "#6366f1")}
        onBlur={(e) => (e.target.style.borderColor = "#334155")}
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
        background: "#1e293b",
        border: "1.5px solid #334155",
        borderRadius: "8px",
        padding: "11px 14px",
        color: "#f1f5f9",
        fontSize: "13px",
        outline: "none",
        resize: "vertical",
        boxSizing: "border-box",
        fontFamily: "inherit",
        lineHeight: 1.5,
        transition: "border-color 0.2s",
      }}
      onFocus={(e) => (e.target.style.borderColor = "#6366f1")}
      onBlur={(e) => (e.target.style.borderColor = "#334155")}
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
  ALL:              { bg: "rgba(99,102,241,0.15)", color: "#a5b4fc" },
  HIGH:             { bg: "rgba(239,68,68,0.15)",  color: "#f87171" },
  MEDIUM:           { bg: "rgba(234,179,8,0.15)",  color: "#fbbf24" },
  LOW:              { bg: "rgba(34,197,94,0.15)",  color: "#4ade80" },
  MY_MENTEES:       { bg: "rgba(56,189,248,0.15)", color: "#38bdf8" },
  SPECIFIC_STUDENT: { bg: "rgba(168,85,247,0.15)", color: "#c084fc" },
};

export default function Interventions() {
  const { active } = useTeacher();
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

  async function handleSend(e) {
    e.preventDefault();
    if (!title.trim() || !link.trim()) {
      setError("Please fill in both the material title and resource link.");
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
      const payload = {
        target_category: targetAudience,
        title: title.trim(),
        resource_url: link.trim(),
        description: description.trim() || "Course remedial notes and study reference shared by faculty.",
        target_student_id: targetAudience === "SPECIFIC_STUDENT" ? parseInt(selectedStudentId) : null,
      };
      const res = await fetch("http://localhost:5000/api/interventions/resource", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.message || "Failed to dispatch.");
      setSuccess(`✓ Resource dispatched to ${data.students_reached} student portal${data.students_reached !== 1 ? "s" : ""}!`);
      setTitle("");
      setDescription("");
      setLink("");
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
          <span style={{ fontSize: "10px", letterSpacing: "1.5px", color: "#6366f1", fontWeight: 700, textTransform: "uppercase" }}>
            Support &amp; Intervention
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
          background: "#0f172a",
          border: "1px solid #1e293b",
          borderRadius: "14px",
          overflow: "hidden",
        }}>
          {/* Panel header */}
          <div style={{
            background: "linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.08))",
            borderBottom: "1px solid #1e293b",
            padding: "16px 20px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}>
            <div style={{
              width: "32px", height: "32px",
              background: "rgba(99,102,241,0.2)",
              borderRadius: "8px",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <Send size={14} style={{ color: "#a5b4fc" }} />
            </div>
            <div>
              <div style={{ fontSize: "14px", fontWeight: 700, color: "#f1f5f9" }}>Create &amp; Dispatch Resource</div>
              <div style={{ fontSize: "11px", color: "#64748b" }}>Fill in the form below and hit Dispatch</div>
            </div>
          </div>

          <form onSubmit={handleSend} style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
            {/* Target audience */}
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "#94a3b8", marginBottom: "8px", letterSpacing: "0.5px", textTransform: "uppercase" }}>
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
                background: "rgba(99,102,241,0.06)",
                border: "1px solid rgba(99,102,241,0.2)",
                borderRadius: "10px",
                padding: "14px",
              }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "#a5b4fc", marginBottom: "10px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  🎯 Select Student
                </label>
                {/* Search */}
                <div style={{ position: "relative", marginBottom: "10px" }}>
                  <Search size={12} style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "#64748b", pointerEvents: "none" }} />
                  <input
                    type="text"
                    placeholder="Search by name or USN..."
                    value={studentSearch}
                    onChange={(e) => setStudentSearch(e.target.value)}
                    style={{
                      width: "100%",
                      background: "#1e293b",
                      border: "1.5px solid #334155",
                      borderRadius: "7px",
                      padding: "9px 12px 9px 30px",
                      color: "#f1f5f9",
                      fontSize: "12px",
                      outline: "none",
                      boxSizing: "border-box",
                    }}
                    onFocus={(e) => (e.target.style.borderColor = "#6366f1")}
                    onBlur={(e) => (e.target.style.borderColor = "#334155")}
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
                          <div style={{ fontSize: "12px", fontWeight: 600, color: String(s.id) === String(selectedStudentId) ? "#a5b4fc" : "#e2e8f0" }}>
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
                    Selected: <strong style={{ color: "#a5b4fc" }}>{selectedStudentObj.name}</strong> ({selectedStudentObj.usn})
                  </div>
                )}
              </div>
            )}

            {/* Material title */}
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "#94a3b8", marginBottom: "8px", letterSpacing: "0.5px", textTransform: "uppercase" }}>
                <FileText size={10} style={{ marginRight: "5px", verticalAlign: "middle" }} />
                Material Title *
              </label>
              <StyledInput
                placeholder="e.g. Week 4 Remedial Notes – OS Scheduling"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                icon={BookOpen}
              />
            </div>

            {/* Description */}
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "#94a3b8", marginBottom: "8px", letterSpacing: "0.5px", textTransform: "uppercase" }}>
                Description &amp; Study Focus
              </label>
              <StyledTextarea
                placeholder="e.g. Focus on CPU scheduling algorithms – Round Robin, FCFS, SJF, and Priority Inversion."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
              />
            </div>

            {/* Resource link */}
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "#94a3b8", marginBottom: "8px", letterSpacing: "0.5px", textTransform: "uppercase" }}>
                <Link2 size={10} style={{ marginRight: "5px", verticalAlign: "middle" }} />
                Resource Link (Drive / LMS / URL) *
              </label>
              <StyledInput
                type="url"
                placeholder="https://drive.google.com/..."
                value={link}
                onChange={(e) => setLink(e.target.value)}
                required
                icon={Link2}
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
                background: submitting ? "#334155" : "linear-gradient(135deg, #6366f1, #8b5cf6)",
                color: "#fff",
                border: "none",
                borderRadius: "10px",
                padding: "13px",
                fontSize: "13px",
                fontWeight: 700,
                cursor: submitting ? "not-allowed" : "pointer",
                marginTop: "4px",
                letterSpacing: "0.3px",
                boxShadow: submitting ? "none" : "0 4px 20px rgba(99,102,241,0.4)",
                transition: "all 0.2s",
              }}
            >
              <Send size={14} />
              <span>{submitting ? "Dispatching to portals..." : "Dispatch to Student Portals"}</span>
            </button>
          </form>
        </div>

        {/* ── DISPATCH HISTORY ── */}
        <div style={{
          background: "#0f172a",
          border: "1px solid #1e293b",
          borderRadius: "14px",
          overflow: "hidden",
        }}>
          {/* Panel header */}
          <div style={{
            background: "linear-gradient(135deg, rgba(56,189,248,0.1), rgba(99,102,241,0.06))",
            borderBottom: "1px solid #1e293b",
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
                <div style={{ fontSize: "14px", fontWeight: 700, color: "#f1f5f9" }}>Dispatch History</div>
                <div style={{ fontSize: "11px", color: "#64748b" }}>Audit trail of dispatched resources</div>
              </div>
            </div>
            <div style={{
              background: "rgba(99,102,241,0.15)",
              color: "#a5b4fc",
              fontSize: "11px",
              fontWeight: 700,
              padding: "3px 10px",
              borderRadius: "20px",
            }}>
              {history.length} dispatches
            </div>
          </div>

          <div style={{ padding: "16px", maxHeight: "520px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "8px" }}>
            {loadingHistory ? (
              <div style={{ padding: "24px", textAlign: "center", color: "#64748b", fontSize: "13px" }}>
                <Zap size={16} style={{ marginBottom: "8px", display: "block", margin: "0 auto 8px" }} />
                Loading audit log...
              </div>
            ) : history.length === 0 ? (
              <div style={{ padding: "32px", textAlign: "center" }}>
                <FolderPlus size={28} style={{ color: "#334155", marginBottom: "10px" }} />
                <div style={{ color: "#475569", fontSize: "13px", fontWeight: 600 }}>No dispatches yet</div>
                <div style={{ color: "#334155", fontSize: "12px", marginTop: "4px" }}>Dispatched resources will appear here</div>
              </div>
            ) : (
              history.map((item, idx) => {
                const badge = TARGET_BADGE[item.target] || TARGET_BADGE.ALL;
                return (
                  <div
                    key={idx}
                    style={{
                      background: "#0c1a2e",
                      border: "1px solid #1e293b",
                      borderRadius: "10px",
                      padding: "12px 14px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "8px",
                      transition: "border-color 0.2s",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#334155")}
                    onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#1e293b")}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "8px" }}>
                      <div style={{ fontSize: "13px", fontWeight: 600, color: "#e2e8f0", lineHeight: 1.4 }}>
                        {item.title}
                      </div>
                      <span style={{
                        background: badge.bg,
                        color: badge.color,
                        fontSize: "9px",
                        fontWeight: 700,
                        padding: "3px 7px",
                        borderRadius: "5px",
                        whiteSpace: "nowrap",
                        flexShrink: 0,
                        letterSpacing: "0.5px",
                      }}>
                        {item.target}
                      </span>
                    </div>

                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <Users size={11} style={{ color: "#64748b" }} />
                        <span style={{ fontSize: "12px", color: "#94a3b8" }}>
                          Reached <strong style={{ color: "#f1f5f9" }}>{item.students_reached}</strong> student{item.students_reached !== 1 ? "s" : ""}
                        </span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "11px", color: "#475569" }}>
                        <Clock size={10} />
                        <span>
                          {item.date
                            ? new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
                            : "Recent"}
                        </span>
                      </div>
                    </div>

                    {item.url && (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                          fontSize: "11px",
                          color: "#38bdf8",
                          textDecoration: "none",
                          fontWeight: 500,
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.color = "#7dd3fc")}
                        onMouseLeave={(e) => (e.currentTarget.style.color = "#38bdf8")}
                      >
                        <ExternalLink size={10} />
                        <span>Open resource link</span>
                      </a>
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
