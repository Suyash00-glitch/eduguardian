import React, { useEffect, useState, useCallback } from "react";
import { MessageSquare, CheckCircle2, Clock, Filter, Reply, Send, Sparkles, User, AlertCircle, RefreshCw } from "lucide-react";
import { useTeacher } from "../../context/TeacherContext";
import { EmptyState } from "../../components/shared/Shared";

export default function Feedback() {
  const { active } = useTeacher();
  const [feedbackList, setFeedbackList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");
  const [replyingId, setReplyingId] = useState(null);
  const [replyText, setReplyText] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchFeedback = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const params = new URLSearchParams({
        department: active.department,
        semester: String(active.semester),
        section: active.section,
      });
      if (statusFilter !== "all") params.append("status", statusFilter);

      const res = await fetch(`http://localhost:5000/api/feedback?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setFeedbackList(data.feedback || []);
      }
    } catch (err) {
      console.error("Failed to load feedback:", err);
    } finally {
      setLoading(false);
    }
  }, [active, statusFilter]);

  useEffect(() => {
    fetchFeedback();
  }, [fetchFeedback]);

  async function handleStatusChange(id, newStatus, reply = null) {
    try {
      const token = localStorage.getItem("token");
      await fetch(`http://localhost:5000/api/feedback/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ status: newStatus, reply }),
      });
      setFeedbackList((prev) =>
        prev.map((f) => (f.id === id ? { ...f, status: newStatus, faculty_reply: reply || f.faculty_reply } : f))
      );
      setReplyingId(null);
      setReplyText("");
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  }

  async function handleSendReply(id) {
    if (!replyText.trim()) return;
    setSubmitting(true);
    await handleStatusChange(id, "Resolved", replyText.trim());
    setSubmitting(false);
  }

  return (
    <div className="feedback-page">
      <div className="feedback-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
        <div>
          <h2 style={{ fontSize: "22px", fontWeight: 700, margin: 0 }}>Student Support &amp; Feedback Inbox</h2>
          <p style={{ margin: "4px 0 0", color: "var(--text-secondary)", fontSize: "13px" }}>
            Direct queries, help requests, and academic clarification tickets from <strong>{active.department} Sem {active.semester} ({active.section})</strong>
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          {/* Status Filter Pills */}
          <div style={{ display: "flex", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px", padding: "3px" }}>
            {["all", "Pending", "In Review", "Resolved"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                style={{
                  padding: "5px 12px",
                  borderRadius: "6px",
                  border: 0,
                  fontSize: "12px",
                  fontWeight: 600,
                  cursor: "pointer",
                  background: statusFilter === st ? "var(--primary)" : "transparent",
                  color: statusFilter === st ? "#000" : "var(--text-secondary)",
                  transition: "all 0.15s ease",
                }}
              >
                {st === "all" ? "All Tickets" : st}
              </button>
            ))}
          </div>

          <button
            className="topbar-icon-button"
            onClick={fetchFeedback}
            title="Refresh tickets"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              border: "1px solid var(--border)",
              background: "var(--surface)",
              color: "var(--text)",
              cursor: "pointer",
            }}
          >
            <RefreshCw size={14} className={loading ? "spin" : ""} />
          </button>
        </div>
      </div>

      <div className="teacher-panel">
        {loading ? (
          <div className="ui-state">
            <div className="ui-spinner">Loading support tickets...</div>
          </div>
        ) : feedbackList.length === 0 ? (
          <EmptyState
            icon={<CheckCircle2 size={24} />}
            title="No support tickets found"
            message={`There are no ${statusFilter !== "all" ? statusFilter.toLowerCase() : ""} support requests for this cohort.`}
          />
        ) : (
          <div className="feedback-list" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {feedbackList.map((item) => (
              <div
                key={item.id}
                style={{
                  background: "var(--surface-soft)",
                  border: "1px solid var(--border)",
                  borderRadius: "10px",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                      <strong style={{ fontSize: "14px", color: "var(--text)" }}>{item.student_name}</strong>
                      <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>({item.usn})</span>
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 700,
                          padding: "2px 8px",
                          borderRadius: "6px",
                          background: "rgba(59, 130, 246, 0.12)",
                          color: "#60a5fa",
                        }}
                      >
                        {item.category}
                      </span>
                      {item.subject_code && (
                        <span style={{ fontSize: "11px", color: "var(--text-secondary)", background: "rgba(255,255,255,0.05)", padding: "2px 6px", borderRadius: "4px" }}>
                          {item.subject_code}
                        </span>
                      )}
                    </div>
                    <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Submitted on {item.date}</span>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span
                      className={`feedback-status ${item.status.toLowerCase().replace(" ", "-")}`}
                      style={{
                        fontSize: "11px",
                        fontWeight: 700,
                        padding: "3px 10px",
                        borderRadius: "6px",
                        background:
                          item.status === "Resolved"
                            ? "rgba(0, 213, 155, 0.15)"
                            : item.status === "In Review"
                            ? "rgba(245, 158, 11, 0.15)"
                            : "rgba(239, 68, 68, 0.15)",
                        color:
                          item.status === "Resolved"
                            ? "#00d59b"
                            : item.status === "In Review"
                            ? "#f59e0b"
                            : "#ef4444",
                      }}
                    >
                      {item.status}
                    </span>
                  </div>
                </div>

                <p style={{ margin: "4px 0", fontSize: "13px", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                  {item.message}
                </p>

                {item.faculty_reply && (
                  <div style={{ background: "rgba(0, 213, 155, 0.06)", borderLeft: "3px solid #00d59b", padding: "8px 12px", borderRadius: "4px", marginTop: "4px" }}>
                    <div style={{ fontSize: "11px", fontWeight: 700, color: "#00d59b", marginBottom: "2px" }}>Faculty Response:</div>
                    <div style={{ fontSize: "12px", color: "var(--text)" }}>{item.faculty_reply}</div>
                  </div>
                )}

                <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", marginTop: "4px" }}>
                  {item.status !== "Resolved" && (
                    <>
                      <button
                        onClick={() => setReplyingId(replyingId === item.id ? null : item.id)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                          padding: "6px 12px",
                          borderRadius: "6px",
                          border: "1px solid var(--border)",
                          background: "var(--surface)",
                          color: "var(--text)",
                          fontSize: "12px",
                          cursor: "pointer",
                        }}
                      >
                        <Reply size={12} /> {replyingId === item.id ? "Cancel" : "Reply"}
                      </button>
                      <button
                        onClick={() => handleStatusChange(item.id, "In Review")}
                        style={{
                          padding: "6px 12px",
                          borderRadius: "6px",
                          border: "1px solid rgba(245, 158, 11, 0.3)",
                          background: "rgba(245, 158, 11, 0.1)",
                          color: "#f59e0b",
                          fontSize: "12px",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        Mark In Review
                      </button>
                    </>
                  )}
                </div>

                {replyingId === item.id && (
                  <div style={{ marginTop: "10px", display: "flex", gap: "8px" }}>
                    <input
                      type="text"
                      placeholder="Type guidance or feedback response..."
                      value={replyText}
                      onChange={(e) => setReplyText(e.target.value)}
                      style={{
                        flex: 1,
                        background: "var(--surface)",
                        border: "1px solid var(--border)",
                        borderRadius: "6px",
                        padding: "8px 12px",
                        color: "var(--text)",
                        fontSize: "13px",
                      }}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleSendReply(item.id);
                      }}
                    />
                    <button
                      onClick={() => handleSendReply(item.id)}
                      disabled={submitting || !replyText.trim()}
                      className="attendance-save-button"
                      style={{ padding: "8px 16px", height: "auto" }}
                    >
                      <Send size={12} /> Send &amp; Resolve
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

