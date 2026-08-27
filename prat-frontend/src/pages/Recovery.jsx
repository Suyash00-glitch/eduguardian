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
  MessageSquare,
  BookOpen,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { recoveryService } from "../services/recoveryService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

const TASK_TIPS_MAP = {
  1: "Start by reviewing the search tree examples from Unit 2. Spend 20 minutes drafting the pseudocode before writing the program.",
  2: "Aim to arrive 5 minutes before class starts. Attending the remaining 3 lectures this week will boost your attendance above 88%.",
  3: "Use the interactive study cards in the Resources section for 15-minute quick review sprints.",
  4: "Prepare 2 specific questions about recent concepts to discuss during your mentor session.",
};

function Recovery() {
  const navigate = useNavigate();
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTaskModal, setActiveTaskModal] = useState(null);

  const loadPlan = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await recoveryService.getPlan();
      setPlan(data);
    } catch (err) {
      setError(err.message || "Unable to load your recovery plan.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPlan();
  }, [loadPlan]);

  const toggleTask = (taskId, e) => {
    if (e) e.stopPropagation();

    setPlan((current) => {
      if (!current) return current;
      const updatedGoals = current.goals.map((goal) =>
        goal.id === taskId ? { ...goal, completed: !goal.completed } : goal
      );
      const comp = updatedGoals.filter((g) => g.completed).length;
      const newProgress = Math.round((comp / updatedGoals.length) * 100);

      return {
        ...current,
        goals: updatedGoals,
        progress: newProgress,
      };
    });
  };

  if (loading) {
    return <LoadingState message="Preparing your recovery plan..." />;
  }

  if (error && !plan) {
    return (
      <ErrorState
        title="Unable to load recovery plan"
        message={error}
        onRetry={loadPlan}
      />
    );
  }

  if (!plan) return null;

  const completed = plan.goals.filter((goal) => goal.completed).length;
  const total = plan.goals.length;

  return (
    <div className="recovery-page">
      {/* HEADER */}
      <div className="recovery-header">
        <div>
          <span className="dashboard-eyebrow">PERSONALIZED SUPPORT</span>
          <h2>Recovery Plan</h2>
          <p>Small, focused actionable steps to help you stay on track and maintain steady growth.</p>
        </div>

        <div className="recovery-ai-label">
          <Sparkles size={13} />
          AI assisted
        </div>
      </div>

      {/* SUMMARY */}
      <section className="recovery-summary">
        <div className="recovery-summary-icon">
          <ClipboardCheck size={20} />
        </div>

        <div className="recovery-summary-text">
          <span className="section-eyebrow">YOUR PLAN</span>
          <h3>{plan.title}</h3>
          <p>{plan.summary}</p>
        </div>

        <div className="recovery-progress">
          <div className="recovery-progress-top">
            <span>Plan progress</span>
            <strong>{plan.progress}%</strong>
          </div>

          <div className="progress-track">
            <div
              className="progress-fill"
              style={{
                width: `${plan.progress}%`,
              }}
            />
          </div>

          <span className="recovery-task-count">
            {completed} of {total} actions completed
          </span>
        </div>
      </section>

      {/* TASKS LIST */}
      <section className="recovery-panel">
        <div className="recovery-panel-header">
          <div>
            <span className="section-eyebrow">RECOMMENDED ACTIONS</span>
            <h3>Focus on these next</h3>
          </div>

          <span className="recovery-count">{total} actions</span>
        </div>

        <div className="recovery-task-list">
          {plan.goals.map((goal) => (
            <div
              className={`recovery-task ${goal.completed ? "completed" : ""} clickable-task`}
              key={goal.id}
              onClick={() => setActiveTaskModal(goal)}
            >
              <button
                type="button"
                className="task-check"
                onClick={(e) => toggleTask(goal.id, e)}
                aria-label={goal.completed ? "Completed" : "Mark as complete"}
              >
                {goal.completed ? (
                  <CheckCircle2 size={21} className="checked-icon" />
                ) : (
                  <Circle size={21} />
                )}
              </button>

              <div className="recovery-task-info">
                <div className="recovery-task-title">
                  <h4>{goal.title}</h4>
                  <span className="task-category">{goal.category}</span>
                </div>

                <p>{goal.description}</p>

                <div className="task-due">
                  <Clock3 size={12} />
                  Due {goal.dueDate}
                </div>
              </div>

              <button
                type="button"
                className="task-arrow-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  setActiveTaskModal(goal);
                }}
                title="View action guidance"
              >
                <ArrowRight className="task-arrow" size={16} />
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* HUMAN FACULTY SUPPORT */}
      <section className="recovery-support">
        <div className="recovery-support-icon">
          <UserCheck size={20} />
        </div>

        <div>
          <span className="section-eyebrow">NEED EXTRA SUPPORT?</span>
          <h3>Your faculty mentor can help you work through this plan.</h3>
          <p>
            EduGuardian provides AI recommendations, but academic support decisions
            remain with you and your faculty mentor.
          </p>
        </div>

        <button
          type="button"
          className="secondary-action"
          onClick={() => navigate("/coach")}
        >
          <span>Ask AI Coach</span>
          <ArrowRight size={13} />
        </button>
      </section>

      {/* TASK GUIDANCE MODAL */}
      {activeTaskModal && (
        <div className="resource-modal-overlay" onClick={() => setActiveTaskModal(null)}>
          <div className="resource-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="resource-modal-header">
              <div className="resource-modal-title">
                <span className="section-eyebrow">ACTION STEP GUIDANCE</span>
                <h3>{activeTaskModal.title}</h3>
              </div>
              <button
                type="button"
                className="resource-modal-close"
                onClick={() => setActiveTaskModal(null)}
              >
                <X size={18} />
              </button>
            </div>

            <div className="resource-modal-body">
              <div className="resource-meta-bar">
                <div className="meta-pill">
                  <Clock3 size={13} />
                  <span>Due: {activeTaskModal.dueDate}</span>
                </div>
                <div className="meta-pill">
                  <BookOpen size={13} />
                  <span>Category: {activeTaskModal.category}</span>
                </div>
              </div>

              <div className="resource-section-block">
                <h4>Description & Instructions</h4>
                <p style={{ fontSize: "13px", lineHeight: "1.6", color: "var(--text-secondary)" }}>
                  {activeTaskModal.description}
                </p>
              </div>

              <div className="resource-section-block study-tip-box">
                <div className="tip-header">
                  <Sparkles size={14} />
                  <strong>Smart Study Recommendation</strong>
                </div>
                <p>
                  {TASK_TIPS_MAP[activeTaskModal.id] ||
                    "Dedicate a 30-minute uninterrupted study block to complete this milestone today."}
                </p>
              </div>
            </div>

            <div className="resource-modal-actions">
              <button
                type="button"
                className="modal-ai-btn"
                onClick={() => {
                  setActiveTaskModal(null);
                  navigate("/coach");
                }}
              >
                <Sparkles size={14} />
                <span>Coach me on this</span>
              </button>

              <button
                type="button"
                className="modal-primary-btn"
                onClick={() => {
                  toggleTask(activeTaskModal.id);
                  setActiveTaskModal(null);
                }}
              >
                <CheckCircle2 size={14} />
                <span>{activeTaskModal.completed ? "Mark as Incomplete" : "Mark as Completed"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Recovery;
