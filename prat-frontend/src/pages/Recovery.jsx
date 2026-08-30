import React, { useCallback, useEffect, useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  Circle,
  ClipboardCheck,
  Clock3,
  Sparkles,
  UserCheck,
  X,
  BookOpen,
  RefreshCw,
  Send,
  Bot,
  PlusCircle,
  Check
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { studentService } from "../services/studentService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

const TASK_TIPS_MAP = {
  "task-1":
    "Focus first on lecture slides for Units 2 and 3. Break your revision into two 30-minute high-focus Pomodoro intervals.",
  "task-2":
    "Review past internal assessment question papers from your course mentor. Highlight recurring question patterns.",
  "task-3":
    "Check your portal marks breakdown to ensure your attendance marks have been recorded by the course instructor.",
};

function Recovery() {
  const navigate = useNavigate();

  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTaskModal, setActiveTaskModal] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [customPrompt, setCustomPrompt] = useState("");
  const [toastMsg, setToastMsg] = useState("");

  const loadPlan = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await studentService.getRecoveryPlan();
      setPlan(data);
    } catch (err) {
      setError(err.message || "Unable to load your recovery plan.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPlan();

    // Listen for live AI sync events across components / chatbot
    const handlePlanUpdate = (e) => {
      if (e.detail) {
        setPlan(e.detail);
        showToast("✨ AI Study Plan updated successfully!");
      }
    };

    const handleWindowMessage = (e) => {
      if (e.data && (e.data.type === "STUDY_PLAN_GENERATED" || e.data.type === "PLAN_CREATED")) {
        studentService.syncAiStudyPlan(e.data.plan).then((updated) => {
          setPlan(updated);
          showToast("✨ AI Coach study plan added to Recovery Plan!");
        });
      }
    };

    window.addEventListener("eduguardian_recovery_plan_updated", handlePlanUpdate);
    window.addEventListener("message", handleWindowMessage);

    return () => {
      window.removeEventListener("eduguardian_recovery_plan_updated", handlePlanUpdate);
      window.removeEventListener("message", handleWindowMessage);
    };
  }, [loadPlan]);

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(""), 4000);
  };

  const toggleTask = async (taskId, e) => {
    if (e) e.stopPropagation();
    try {
      const updated = await studentService.toggleRecoveryTask(taskId);
      setPlan(updated);
    } catch (err) {
      setError(err.message || "Unable to update task.");
    }
  };

  const handleGenerateAiPlan = async (e) => {
    if (e) e.preventDefault();
    setGenerating(true);
    try {
      const fresh = await studentService.generateAiRecoveryPlan(customPrompt);
      setPlan(fresh);
      setCustomPrompt("");
      showToast("✨ Fresh AI Recovery Blueprint generated!");
    } catch (err) {
      showToast("Failed to generate AI plan. Retrying...");
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return <LoadingState message="Building your personalized recovery plan..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Unable to load recovery plan"
        message={error}
        onRetry={loadPlan}
      />
    );
  }

  if (!plan) return null;

  const completed = (plan.goals || []).filter((goal) => goal.completed).length;
  const total = (plan.goals || []).length;

  return (
    <div className="recovery-page">
      {/* TOAST NOTIFICATION */}
      {toastMsg && (
        <div
          style={{
            position: "fixed",
            bottom: "24px",
            right: "24px",
            background: "#00d59b",
            color: "#03251c",
            padding: "12px 20px",
            borderRadius: "10px",
            fontWeight: 700,
            fontSize: "13px",
            boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            zIndex: 9999,
            animation: "fadeIn 0.2s ease",
          }}
        >
          <Check size={16} />
          {toastMsg}
        </div>
      )}

      {/* HEADER */}
      <div className="recovery-header" style={{ marginBottom: "20px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <h1 style={{ fontSize: "var(--font-2xl)", fontWeight: 700, margin: 0, color: "var(--text)" }}>
            Academic Recovery &amp; Study Plan
          </h1>
          <p style={{ margin: "4px 0 0", fontSize: "var(--font-base)", color: "var(--text-secondary)" }}>
            Structured actionable steps and AI-guided study milestones tailored to your academic progress.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <button
            onClick={() => handleGenerateAiPlan()}
            disabled={generating}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "12px",
              fontWeight: 700,
              padding: "7px 14px",
              borderRadius: "8px",
              background: "var(--primary)",
              color: "#03251c",
              border: "none",
              cursor: generating ? "not-allowed" : "pointer",
            }}
          >
            <RefreshCw size={13} className={generating ? "spin" : ""} />
            {generating ? "Synthesizing AI Plan..." : "✨ Regenerate AI Blueprint"}
          </button>

          <button
            onClick={() => navigate("/coach")}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "12px",
              fontWeight: 600,
              padding: "7px 14px",
              borderRadius: "8px",
              background: "var(--surface)",
              color: "var(--text)",
              border: "1px solid var(--border)",
              cursor: "pointer",
            }}
          >
            <Bot size={14} color="var(--primary)" />
            Open AI Coach
          </button>
        </div>
      </div>

      {/* AI PLAN PROMPT BAR */}
      <form
        onSubmit={handleGenerateAiPlan}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          padding: "10px 16px",
          borderRadius: "12px",
          background: "var(--surface)",
          border: "1px solid var(--border)",
          marginBottom: "20px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
        }}
      >
        <Sparkles size={18} color="var(--primary)" style={{ flexShrink: 0 }} />
        <input
          type="text"
          value={customPrompt}
          onChange={(e) => setCustomPrompt(e.target.value)}
          placeholder="Ask AI Coach for a custom study plan (e.g. 'Create a 7-day revision schedule for Operating Systems and DSA')..."
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            outline: "none",
            color: "var(--text)",
            fontSize: "13px",
          }}
        />
        <button
          type="submit"
          disabled={generating || !customPrompt.trim()}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            padding: "6px 14px",
            borderRadius: "7px",
            background: customPrompt.trim() ? "var(--primary)" : "var(--surface-soft)",
            color: customPrompt.trim() ? "#03251c" : "var(--text-muted)",
            border: "none",
            fontWeight: 700,
            fontSize: "12px",
            cursor: customPrompt.trim() ? "pointer" : "default",
          }}
        >
          <Send size={12} />
          Generate Plan
        </button>
      </form>

      {/* SUMMARY */}
      <section
        className="recovery-summary"
        style={{
          padding: "20px 22px",
          borderRadius: "12px",
          border: "1px solid var(--border)",
          background: "var(--surface)",
          display: "flex",
          alignItems: "center",
          gap: "20px",
          marginBottom: "20px",
          flexWrap: "wrap",
        }}
      >
        <div
          style={{
            width: "44px",
            height: "44px",
            borderRadius: "10px",
            background: "var(--primary-soft)",
            color: "var(--primary)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <ClipboardCheck size={22} />
        </div>

        <div style={{ flex: 1, minWidth: "240px" }}>
          <h3 style={{ fontSize: "var(--font-lg)", fontWeight: 700, margin: 0, color: "var(--text)" }}>
            {plan.title || "Academic Study Blueprint"}
          </h3>
          <p style={{ margin: "4px 0 0", fontSize: "var(--font-sm)", color: "var(--text-secondary)", lineHeight: 1.5 }}>
            {plan.summary}
          </p>
        </div>

        <div style={{ minWidth: "180px", textAlign: "right" }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--font-sm)", marginBottom: "6px" }}>
            <span style={{ color: "var(--text-muted)" }}>Plan progress</span>
            <strong style={{ color: "var(--primary)", fontWeight: 700 }}>{plan.progress || 0}%</strong>
          </div>

          <div style={{ height: "6px", background: "rgba(255,255,255,0.08)", borderRadius: "4px", overflow: "hidden", marginBottom: "6px" }}>
            <div
              style={{
                height: "100%",
                width: `${plan.progress || 0}%`,
                background: "var(--primary)",
                borderRadius: "inherit",
                transition: "width 0.3s ease",
              }}
            />
          </div>

          <span style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)" }}>
            {completed} of {total} actions completed
          </span>
        </div>
      </section>

      {/* TASKS LIST */}
      <section
        style={{
          borderRadius: "12px",
          border: "1px solid var(--border)",
          background: "var(--surface)",
          overflow: "hidden",
          marginBottom: "20px",
        }}
      >
        <div
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <h3 style={{ margin: 0, fontSize: "var(--font-md)", fontWeight: 600, color: "var(--text)" }}>
              Recommended Study &amp; Recovery Actions
            </h3>
            <p style={{ margin: "4px 0 0", fontSize: "var(--font-sm)", color: "var(--text-muted)" }}>
              Prioritized milestones automatically synchronized with your AI Coach.
            </p>
          </div>

          <span style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)" }}>
            {total} Action Items
          </span>
        </div>

        <div style={{ padding: "16px 20px" }}>
          {(plan.goals || []).map((goal) => (
            <div
              key={goal.id}
              onClick={() => setActiveTaskModal(goal)}
              style={{
                padding: "14px 16px",
                borderRadius: "10px",
                border: "1px solid var(--border)",
                background: goal.completed ? "rgba(0, 213, 155, 0.05)" : "var(--surface-soft)",
                marginBottom: "10px",
                display: "flex",
                alignItems: "flex-start",
                gap: "14px",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              <button
                type="button"
                onClick={(e) => toggleTask(goal.id, e)}
                style={{
                  background: "transparent",
                  border: "none",
                  padding: 0,
                  cursor: "pointer",
                  color: goal.completed ? "var(--primary)" : "var(--text-muted)",
                  marginTop: "2px",
                }}
              >
                {goal.completed ? <CheckCircle2 size={20} color="var(--primary)" /> : <Circle size={20} />}
              </button>

              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px" }}>
                  <h4
                    style={{
                      margin: 0,
                      fontSize: "var(--font-base)",
                      fontWeight: 600,
                      color: goal.completed ? "var(--text-muted)" : "var(--text)",
                      textDecoration: goal.completed ? "line-through" : "none",
                    }}
                  >
                    {goal.title}
                  </h4>

                  <span
                    style={{
                      fontSize: "11px",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      background: "rgba(255,255,255,0.06)",
                      color: "var(--text-secondary)",
                      fontWeight: 600,
                    }}
                  >
                    {goal.category || "Study"}
                  </span>
                </div>

                <p style={{ margin: "6px 0 0", fontSize: "var(--font-sm)", color: "var(--text-secondary)", lineHeight: 1.4 }}>
                  {goal.description}
                </p>

                <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "8px", fontSize: "var(--font-xs)", color: "var(--text-muted)" }}>
                  <Clock3 size={12} />
                  <span>Target: {goal.dueDate || "This week"}</span>
                  {goal.timeEstimate && <span>· {goal.timeEstimate}</span>}
                </div>
              </div>

              <div style={{ color: "var(--text-muted)", marginTop: "4px" }}>
                <ArrowRight size={16} />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* HUMAN FACULTY SUPPORT */}
      <section
        style={{
          padding: "18px 22px",
          borderRadius: "12px",
          border: "1px solid var(--border)",
          background: "var(--surface)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "14px", flex: 1, minWidth: "260px" }}>
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "10px",
              background: "var(--primary-soft)",
              color: "var(--primary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <UserCheck size={20} />
          </div>

          <div>
            <h3 style={{ fontSize: "var(--font-base)", fontWeight: 600, margin: 0, color: "var(--text)" }}>
              Faculty Mentorship Available
            </h3>
            <p style={{ margin: "4px 0 0", fontSize: "var(--font-sm)", color: "var(--text-secondary)" }}>
              Your assigned faculty advisor is available to review your recovery milestones and study progress.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => navigate("/coach")}
          style={{
            height: "38px",
            padding: "0 18px",
            borderRadius: "8px",
            border: "none",
            background: "var(--primary)",
            color: "#03251c",
            fontWeight: 700,
            fontSize: "var(--font-sm)",
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          Chat with AI Coach
          <ArrowRight size={14} />
        </button>
      </section>

      {/* TASK GUIDANCE MODAL */}
      {activeTaskModal && (
        <div className="goal-form-overlay" onClick={() => setActiveTaskModal(null)}>
          <div
            style={{
              padding: "24px",
              borderRadius: "14px",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              maxWidth: "540px",
              width: "100%",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
              <h3 style={{ margin: 0, fontSize: "var(--font-lg)", fontWeight: 600, color: "var(--text)" }}>
                {activeTaskModal.title}
              </h3>
              <button
                type="button"
                onClick={() => setActiveTaskModal(null)}
                style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ display: "flex", gap: "10px", marginBottom: "16px" }}>
              <span style={{ fontSize: "var(--font-xs)", padding: "4px 10px", borderRadius: "20px", background: "var(--surface-soft)", border: "1px solid var(--border)", color: "var(--text-secondary)", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                <Clock3 size={12} />
                Target: {activeTaskModal.dueDate || "This week"}
              </span>
              <span style={{ fontSize: "var(--font-xs)", padding: "4px 10px", borderRadius: "20px", background: "var(--surface-soft)", border: "1px solid var(--border)", color: "var(--text-secondary)", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                <BookOpen size={12} />
                {activeTaskModal.category || "Study"}
              </span>
            </div>

            <div style={{ marginBottom: "18px" }}>
              <h4 style={{ fontSize: "var(--font-sm)", fontWeight: 600, color: "var(--text)", margin: "0 0 6px" }}>
                Instructions
              </h4>
              <p style={{ fontSize: "var(--font-sm)", lineHeight: "1.6", color: "var(--text-secondary)", margin: 0 }}>
                {activeTaskModal.description}
              </p>
            </div>

            {activeTaskModal.steps && activeTaskModal.steps.length > 0 && (
              <div style={{ marginBottom: "18px" }}>
                <h4 style={{ fontSize: "var(--font-sm)", fontWeight: 600, color: "var(--text)", margin: "0 0 6px" }}>
                  Action Checklist
                </h4>
                <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "var(--font-sm)", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                  {activeTaskModal.steps.map((st, i) => (
                    <li key={i}>{st}</li>
                  ))}
                </ul>
              </div>
            )}

            <div
              style={{
                padding: "14px 16px",
                borderRadius: "10px",
                background: "rgba(0, 213, 155, 0.06)",
                border: "1px solid rgba(0, 213, 155, 0.2)",
                marginBottom: "20px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--primary)", fontSize: "var(--font-xs)", fontWeight: 700, marginBottom: "4px" }}>
                <Sparkles size={13} />
                Smart Study Recommendation
              </div>
              <p style={{ fontSize: "var(--font-sm)", color: "var(--text-secondary)", margin: 0, lineHeight: 1.5 }}>
                {TASK_TIPS_MAP[activeTaskModal.id] ||
                  "Dedicate a 30-minute uninterrupted study block to complete this milestone today."}
              </p>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <button
                type="button"
                onClick={() => {
                  setActiveTaskModal(null);
                  navigate("/coach");
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--primary)",
                  fontSize: "var(--font-sm)",
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <Sparkles size={14} />
                Coach me on this
              </button>

              <button
                type="button"
                onClick={() => {
                  toggleTask(activeTaskModal.id);
                  setActiveTaskModal(null);
                }}
                style={{
                  height: "36px",
                  padding: "0 18px",
                  borderRadius: "8px",
                  border: "none",
                  background: "var(--primary)",
                  color: "#03251c",
                  fontWeight: 700,
                  fontSize: "var(--font-sm)",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <CheckCircle2 size={14} />
                {activeTaskModal.completed ? "Mark as Incomplete" : "Mark as Completed"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Recovery;
