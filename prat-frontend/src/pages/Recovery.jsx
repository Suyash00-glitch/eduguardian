import React, { useCallback, useEffect, useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  Circle,
  ClipboardCheck,
  Clock3,
  Sparkles,
} from "lucide-react";

import { recoveryService } from "../services/recoveryService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

function Recovery() {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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

  const completeTask = async (taskId) => {
    try {
      await recoveryService.completeTask(taskId);

      setPlan((current) => ({
        ...current,
        goals: current.goals.map((goal) =>
          goal.id === taskId ? { ...goal, completed: true } : goal,
        ),
      }));
    } catch {
      setError("Unable to update the task.");
    }
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

          <p>Small, focused actions to help you stay on track.</p>
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

      {/* TASKS */}

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
              className={`recovery-task ${goal.completed ? "completed" : ""}`}
              key={goal.id}
            >
              <button
                className="task-check"
                onClick={() => !goal.completed && completeTask(goal.id)}
                aria-label={goal.completed ? "Completed" : "Mark as complete"}
              >
                {goal.completed ? (
                  <CheckCircle2 size={21} />
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

              {!goal.completed && (
                <ArrowRight className="task-arrow" size={16} />
              )}
            </div>
          ))}
        </div>
      </section>

      {/* HUMAN SUPPORT */}

      <section className="recovery-support">
        <div className="recovery-support-icon">
          <CheckCircle2 size={18} />
        </div>

        <div>
          <span className="section-eyebrow">NEED EXTRA SUPPORT?</span>

          <h3>Your mentor can help you work through this plan.</h3>

          <p>
            EduGuardian provides recommendations, but academic support decisions
            remain with you and your mentor.
          </p>
        </div>

        <button className="secondary-action">
          View mentor
          <ArrowRight size={13} />
        </button>
      </section>
    </div>
  );
}

export default Recovery;
