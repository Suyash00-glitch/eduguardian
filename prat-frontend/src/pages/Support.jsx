import React, { useState, useEffect, useCallback } from "react";
import {
  LifeBuoy,
  Send,
  CheckCircle2,
  AlertCircle,
  Clock,
  MessageSquare,
  Sparkles,
  BookOpen,
  Filter,
  UserCheck,
  RefreshCw,
  HelpCircle,
  MessageSquareText,
} from "lucide-react";
import { studentService } from "../services/studentService";

const CATEGORY_OPTIONS = [
  { value: "Academic Support", label: "Academic Support & Doubts", icon: "📚" },
  { value: "Attendance Query", label: "Attendance Query / Discrepancy", icon: "📅" },
  { value: "Mentorship Request", label: "Faculty Mentorship & Guidance", icon: "👤" },
  { value: "Course Material", label: "Course Notes & Material Request", icon: "📑" },
  { value: "General Query", label: "General Department Query", icon: "💬" },
];

const SUBJECT_OPTIONS = [
  { code: "none", name: "None / General Department Query" },
  { code: "IS3001-1", name: "IS3001-1 · Data Communication and Networking (Dr. Ravi B)" },
  { code: "IS2002-1", name: "IS2002-1 · Machine Learning Foundations (Dr. Ramesh G)" },
  { code: "IS3101-1", name: "IS3101-1 · Operating Systems Fundamentals (Ms. Prathyakshini)" },
  { code: "HU1011-1", name: "HU1011-1 · Universal Human Values (Dr. Preethi Salian K)" },
  { code: "IS1604-1", name: "IS1604-1 · MERN Stack Development (Mr. Krishnamoorthy C)" },
  { code: "UM1003-1", name: "UM1003-1 · Employability Skill Development (Dr. Deepa)" },
  { code: "HU1007-1", name: "HU1007-1 · Social Connect & Responsibility (Dr. Santhosh S)" },
  { code: "HU1010-1", name: "HU1010-1 · Research Methodology (Dr. Vasudeva)" },
];

export default function Support() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [filterStatus, setFilterStatus] = useState("all");

  const [category, setCategory] = useState("Academic Support");
  const [subjectCode, setSubjectCode] = useState("none");
  const [message, setMessage] = useState("");

  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const loadTickets = useCallback(async () => {
    setLoading(true);
    try {
      const data = await studentService.getSupportTickets();
      setTickets(data || []);
    } catch (err) {
      console.error("Failed to load tickets:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!message.trim()) {
      setError("Please describe your issue or query.");
      return;
    }

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      await studentService.createSupportTicket({
        category,
        subject_code: subjectCode !== "none" ? subjectCode : null,
        message: message.trim(),
      });

      setSuccess("Your support ticket has been submitted to your faculty advisor! You can track replies below.");
      setMessage("");
      setSubjectCode("none");
      await loadTickets();
      setTimeout(() => setSuccess(""), 6000);
    } catch (err) {
      setError(err.message || "Failed to submit support ticket.");
    } finally {
      setSubmitting(false);
    }
  }

  const filteredTickets = tickets.filter((t) => {
    if (filterStatus === "all") return true;
    return (t.status || "").toLowerCase() === filterStatus.toLowerCase();
  });

  const pendingCount = tickets.filter((t) => (t.status || "").toLowerCase() === "pending").length;
  const resolvedCount = tickets.filter((t) => (t.status || "").toLowerCase() === "resolved").length;

  return (
    <div className="support-page" style={{ padding: "0 0 32px" }}>
      {/* Header */}
      <div style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <span style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "1.2px", color: "var(--primary)", textTransform: "uppercase" }}>
              STUDENT SUPPORT &amp; HELP DESK
            </span>
          </div>
          <h1 style={{ fontSize: "24px", fontWeight: 700, color: "var(--text)", margin: 0 }}>
            Faculty Query &amp; Support Center
          </h1>
          <p style={{ margin: "6px 0 0", fontSize: "13px", color: "var(--text-secondary)" }}>
            Submit academic doubts, attendance clarifications, and mentorship requests directly to your class advisor and teachers.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <div style={{ padding: "8px 14px", borderRadius: "10px", background: "var(--surface)", border: "1px solid var(--border)", display: "flex", alignItems: "center", gap: "8px" }}>
            <Clock size={16} style={{ color: "#f59e0b" }} />
            <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text)" }}>{pendingCount} Pending</span>
          </div>
          <div style={{ padding: "8px 14px", borderRadius: "10px", background: "var(--surface)", border: "1px solid var(--border)", display: "flex", alignItems: "center", gap: "8px" }}>
            <CheckCircle2 size={16} style={{ color: "var(--primary)" }} />
            <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text)" }}>{resolvedCount} Resolved</span>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {success && (
        <div style={{ background: "rgba(0, 213, 155, 0.12)", border: "1px solid rgba(0, 213, 155, 0.3)", color: "var(--primary)", padding: "12px 16px", borderRadius: "10px", marginBottom: "16px", display: "flex", alignItems: "center", gap: "10px", fontSize: "13px" }}>
          <CheckCircle2 size={16} />
          <span>{success}</span>
        </div>
      )}

      {error && (
        <div style={{ background: "rgba(239, 68, 68, 0.12)", border: "1px solid rgba(239, 68, 68, 0.3)", color: "#ef4444", padding: "12px 16px", borderRadius: "10px", marginBottom: "16px", display: "flex", alignItems: "center", gap: "10px", fontSize: "13px" }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1.3fr", gap: "24px", alignItems: "start" }}>
        {/* Ticket Submission Form */}
        <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "14px", overflow: "hidden" }}>
          <div style={{ padding: "18px 20px", borderBottom: "1px solid var(--border)", background: "var(--surface-soft)", display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "rgba(0, 213, 155, 0.15)", color: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Send size={15} />
            </div>
            <div>
              <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--text)" }}>Create Support Ticket</div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Directly sent to Class Advisor Dr. Preethi Salian K &amp; subject teachers</div>
            </div>
          </div>

          <form onSubmit={handleSubmit} style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
            {/* Category */}
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                Request Category *
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                style={{
                  width: "100%",
                  background: "var(--surface-soft)",
                  border: "1.5px solid var(--border)",
                  borderRadius: "8px",
                  padding: "11px 14px",
                  color: "var(--text)",
                  fontSize: "13px",
                  outline: "none",
                  cursor: "pointer",
                }}
              >
                {CATEGORY_OPTIONS.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.icon} {cat.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Related Subject */}
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                Related Course / Subject
              </label>
              <select
                value={subjectCode}
                onChange={(e) => setSubjectCode(e.target.value)}
                style={{
                  width: "100%",
                  background: "var(--surface-soft)",
                  border: "1.5px solid var(--border)",
                  borderRadius: "8px",
                  padding: "11px 14px",
                  color: "var(--text)",
                  fontSize: "13px",
                  outline: "none",
                  cursor: "pointer",
                }}
              >
                {SUBJECT_OPTIONS.map((sub) => (
                  <option key={sub.code} value={sub.code}>
                    {sub.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Message Description */}
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                Detailed Query / Description *
              </label>
              <textarea
                rows={5}
                required
                placeholder="Describe your query, specific doubt, or clarification needed in detail..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                style={{
                  width: "100%",
                  background: "var(--surface-soft)",
                  border: "1.5px solid var(--border)",
                  borderRadius: "8px",
                  padding: "12px 14px",
                  color: "var(--text)",
                  fontSize: "13px",
                  outline: "none",
                  resize: "vertical",
                  fontFamily: "inherit",
                  lineHeight: 1.5,
                  boxSizing: "border-box",
                }}
              />
            </div>

            {/* Submit Button */}
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
                boxShadow: submitting ? "none" : "0 4px 20px rgba(0, 213, 155, 0.25)",
                transition: "all 0.2s ease",
              }}
            >
              <Send size={14} />
              <span>{submitting ? "Submitting Request..." : "Send Ticket to Faculty"}</span>
            </button>
          </form>
        </div>

        {/* Ticket List / Replies */}
        <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "14px", overflow: "hidden" }}>
          {/* Header & Filter Tabs */}
          <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)", background: "var(--surface-soft)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <MessageSquareText size={15} />
              </div>
              <div>
                <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--text)" }}>My Support History</div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Track status and read faculty responses</div>
              </div>
            </div>

            {/* Filter Tabs */}
            <div style={{ display: "flex", gap: "4px", background: "var(--surface)", padding: "3px", borderRadius: "8px", border: "1px solid var(--border)" }}>
              {["all", "pending", "in review", "resolved"].map((st) => (
                <button
                  key={st}
                  type="button"
                  onClick={() => setFilterStatus(st)}
                  style={{
                    padding: "4px 10px",
                    borderRadius: "6px",
                    border: "none",
                    background: filterStatus === st ? "var(--primary)" : "transparent",
                    color: filterStatus === st ? "#03251c" : "var(--text-secondary)",
                    fontWeight: 700,
                    fontSize: "11px",
                    textTransform: "capitalize",
                    cursor: "pointer",
                  }}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {/* Tickets List */}
          <div style={{ padding: "16px", maxHeight: "600px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "12px" }}>
            {loading ? (
              <div style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>
                <RefreshCw size={18} className="spin" style={{ margin: "0 auto 8px", display: "block" }} />
                Loading your support history...
              </div>
            ) : filteredTickets.length === 0 ? (
              <div style={{ padding: "40px 20px", textAlign: "center" }}>
                <HelpCircle size={32} style={{ color: "var(--text-muted)", margin: "0 auto 10px", display: "block", opacity: 0.6 }} />
                <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--text)" }}>No tickets in this view</div>
                <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
                  Submit a query on the left to ask for help from your teachers.
                </div>
              </div>
            ) : (
              filteredTickets.map((t) => {
                const isResolved = (t.status || "").toLowerCase() === "resolved";
                const isInReview = (t.status || "").toLowerCase() === "in review";

                const statusColor = isResolved ? "#00d59b" : isInReview ? "#38bdf8" : "#f59e0b";
                const statusBg = isResolved ? "rgba(0, 213, 155, 0.15)" : isInReview ? "rgba(56, 189, 248, 0.15)" : "rgba(245, 158, 11, 0.15)";

                return (
                  <div
                    key={t.id}
                    style={{
                      background: "var(--surface-soft)",
                      border: "1px solid var(--border)",
                      borderRadius: "12px",
                      padding: "16px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                    }}
                  >
                    {/* Header */}
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
                      <div>
                        <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text)" }}>
                          {t.category}
                        </div>
                        <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                          {t.subject_name || "General Department"} · {t.date || "Recent"}
                        </div>
                      </div>
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 700,
                          padding: "3px 8px",
                          borderRadius: "6px",
                          background: statusBg,
                          color: statusColor,
                          border: `1px solid ${statusColor}40`,
                        }}
                      >
                        {t.status}
                      </span>
                    </div>

                    {/* Query Message */}
                    <div style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: 1.5, background: "var(--surface)", padding: "10px 12px", borderRadius: "8px", border: "1px solid var(--border)" }}>
                      {t.message}
                    </div>

                    {/* Faculty Reply */}
                    {t.faculty_reply ? (
                      <div
                        style={{
                          background: "rgba(0, 213, 155, 0.08)",
                          border: "1.5px solid rgba(0, 213, 155, 0.3)",
                          borderRadius: "10px",
                          padding: "12px 14px",
                          marginTop: "4px",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--primary)", fontSize: "12px", fontWeight: 700, marginBottom: "4px" }}>
                          <UserCheck size={14} />
                          <span>Faculty Advisor Reply:</span>
                        </div>
                        <p style={{ margin: 0, fontSize: "13px", color: "var(--text)", lineHeight: 1.5 }}>
                          {t.faculty_reply}
                        </p>
                      </div>
                    ) : (
                      <div style={{ fontSize: "11px", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "5px", marginTop: "2px" }}>
                        <Clock size={12} />
                        <span>Awaiting faculty review...</span>
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
