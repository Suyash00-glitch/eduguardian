import React, { useCallback, useEffect, useState } from "react";
import {
  ArrowRight,
  Plus,
  Target,
  CheckCircle2,
  X,
  Sparkles,
  Calendar,
  ChevronRight,
  CheckSquare,
  Square,
  TrendingUp,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { studentService } from "../services/studentService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

const GOAL_MILESTONES = {
  "Maintain 85% attendance": [
    { title: "Attend all DCN lectures this week (4/4)", completed: true },
    { title: "Attend all ML Foundations lectures (3/3)", completed: true },
    { title: "Check OS attendance record on portal by Friday", completed: false },
  ],
  "Complete all pending assignments": [
    { title: "Submit Search Algorithms Assignment in AI", completed: true },
    { title: "Complete Protocol Analysis Report for DCN", completed: false },
    { title: "Verify submission status with course mentor", completed: false },
  ],
  "Improve weekly LMS activity": [
    { title: "Complete 2 hours of self-study on portal modules", completed: true },
    { title: "Participate in DBMS discussion forum", completed: true },
    { title: "Download and review week 6 lecture slides", completed: false },
  ],
};

function Goals() {
  const navigate = useNavigate();
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState(null);
  const [milestonesState, setMilestonesState] = useState(GOAL_MILESTONES);

  const [form, setForm] = useState({
    title: "",
    target: "",
  });

  const loadGoals = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await studentService.getGoals();
      setGoals(data);
    } catch (err) {
      setError(err.message || "Unable to load goals.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGoals();
  }, [loadGoals]);

  const createGoal = async (event) => {
    event.preventDefault();

    if (!form.title.trim()) return;

    try {
      const newGoal = await studentService.createGoal({
        title: form.title,
        target: form.target,
      });

      setGoals((current) => [...current, newGoal]);

      setMilestonesState((prev) => ({
        ...prev,
        [newGoal.title]: [
          { title: `Set daily 30-min block for ${newGoal.title}`, completed: false },
          { title: `Track progress on Friday`, completed: false },
        ],
      }));

      setForm({
        title: "",
        target: "",
      });

      setShowForm(false);
    } catch (err) {
      setError(err.message || "Unable to create goal.");
    }
  };

  const toggleMilestone = (goalTitle, idx) => {
    setMilestonesState((prev) => {
      const currentList = prev[goalTitle] || [];
      const updated = currentList.map((m, i) =>
        i === idx ? { ...m, completed: !m.completed } : m
      );

      const compCount = updated.filter((m) => m.completed).length;
      const newPct = Math.round((compCount / updated.length) * 100);

      setGoals((gPrev) =>
        gPrev.map((g) => (g.title === goalTitle ? { ...g, progress: newPct } : g))
      );

      return {
        ...prev,
        [goalTitle]: updated,
      };
    });
  };

  if (loading) {
    return <LoadingState message="Loading your goals..." />;
  }

  if (error && !goals.length) {
    return (
      <ErrorState
        title="Unable to load goals"
        message={error}
        onRetry={loadGoals}
      />
    );
  }

  const completed = goals.filter((goal) => goal.progress >= 100).length;

  return (
    <div className="goals-page">
      {/* HEADER */}
      <div className="goals-header">
        <div>
          <span className="dashboard-eyebrow">PERSONAL TARGETS</span>
          <h2>My Goals</h2>
          <p>Set structured academic milestones and track your progress consistently.</p>
        </div>

        <button
          className="create-goal-button"
          onClick={() => setShowForm(true)}
        >
          <Plus size={14} />
          New goal
        </button>
      </div>

      {/* SUMMARY */}
      <div className="goals-summary">
        <div className="goals-summary-icon">
          <Target size={18} />
        </div>

        <div>
          <span>ACTIVE GOALS</span>
          <strong>{goals.length}</strong>
        </div>

        <div className="goal-summary-divider" />

        <div>
          <span>COMPLETED</span>
          <strong>{completed}</strong>
        </div>

        <div className="goal-summary-message">
          <CheckCircle2 size={14} />
          <span>Keep your goals realistic and actionable.</span>
        </div>
      </div>

      {/* CREATE GOAL MODAL FORM */}
      {showForm && (
        <div className="goal-form-overlay" onClick={() => setShowForm(false)}>
          <form className="goal-form" onSubmit={createGoal} onClick={(e) => e.stopPropagation()}>
            <div className="goal-form-header">
              <div>
                <span className="section-eyebrow">NEW GOAL</span>
                <h3>Create a personal academic goal</h3>
              </div>

              <button type="button" onClick={() => setShowForm(false)}>
                <X size={15} />
              </button>
            </div>

            <label>
              Goal Title
              <input
                value={form.title}
                onChange={(event) =>
                  setForm({
                    ...form,
                    title: event.target.value,
                  })
                }
                placeholder="e.g. Maintain 90% attendance"
                required
              />
            </label>

            <label>
              Target Target
              <input
                value={form.target}
                onChange={(event) =>
                  setForm({
                    ...form,
                    target: event.target.value,
                  })
                }
                placeholder="e.g. 90% by Semester End"
              />
            </label>

            <div className="goal-form-actions">
              <button
                type="button"
                className="goal-cancel"
                onClick={() => setShowForm(false)}
              >
                Cancel
              </button>

              <button type="submit" className="goal-save">
                Create goal
              </button>
            </div>
          </form>
        </div>
      )}

      {/* GOALS LIST */}
      <section className="goals-panel">
        <div className="goals-panel-header">
          <div>
            <span className="section-eyebrow">YOUR GOALS</span>
            <h3>Academic targets</h3>
          </div>

          <span>{goals.length} targets</span>
        </div>

        <div className="goal-list">
          {goals.length === 0 ? (
            <div className="goals-empty">
              <Target size={20} />
              <strong>No goals yet</strong>
              <span>Create your first academic target to get started.</span>
            </div>
          ) : (
            goals.map((goal) => (
              <div
                className="goal-row clickable-goal-row"
                key={goal.id}
                onClick={() => setSelectedGoal(goal)}
              >
                <div className="goal-icon">
                  {goal.progress >= 100 ? (
                    <CheckCircle2 size={16} />
                  ) : (
                    <Target size={16} />
                  )}
                </div>

                <div className="goal-info">
                  <div className="goal-title">
                    <strong>{goal.title}</strong>
                    <span className={`goal-status ${goal.status || "in-progress"}`}>
                      {goal.progress >= 100 ? "Completed" : "On Track"}
                    </span>
                  </div>

                  <div className="goal-progress">
                    <div className="goal-progress-track">
                      <span
                        style={{
                          width: `${Math.min(goal.progress || 0, 100)}%`,
                        }}
                      />
                    </div>

                    <strong>{goal.progress || 0}%</strong>
                  </div>
                </div>

                <button
                  type="button"
                  className="goal-open"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedGoal(goal);
                  }}
                  title="View action plan"
                >
                  <ArrowRight size={15} />
                </button>
              </div>
            ))
          )}
        </div>
      </section>

      {/* GOAL ACTION DETAILS MODAL */}
      {selectedGoal && (
        <div className="resource-modal-overlay" onClick={() => setSelectedGoal(null)}>
          <div className="resource-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="resource-modal-header">
              <div className="resource-modal-title">
                <span className="section-eyebrow">TARGET ACTION PLAN</span>
                <h3>{selectedGoal.title}</h3>
              </div>
              <button
                type="button"
                className="resource-modal-close"
                onClick={() => setSelectedGoal(null)}
              >
                <X size={18} />
              </button>
            </div>

            <div className="resource-modal-body">
              <div className="goal-modal-stat-bar">
                <div>
                  <span>Current Completion</span>
                  <strong>{selectedGoal.progress || 0}%</strong>
                </div>
                <div className="goal-modal-track">
                  <div
                    className="goal-modal-fill"
                    style={{ width: `${selectedGoal.progress || 0}%` }}
                  />
                </div>
              </div>

              <div className="resource-section-block">
                <h4>Actionable Milestone Steps (Click to complete)</h4>
                <div className="goal-milestones-list">
                  {(
                    milestonesState[selectedGoal.title] || [
                      { title: "Review weekly notes for 30 minutes", completed: false },
                      { title: "Submit pending practice quiz questions", completed: false },
                    ]
                  ).map((m, idx) => (
                    <div
                      className={`goal-milestone-item ${m.completed ? "done" : ""}`}
                      key={idx}
                      onClick={() => toggleMilestone(selectedGoal.title, idx)}
                    >
                      {m.completed ? (
                        <CheckSquare size={17} className="milestone-icon checked" />
                      ) : (
                        <Square size={17} className="milestone-icon" />
                      )}
                      <span>{m.title}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="resource-section-block study-tip-box">
                <div className="tip-header">
                  <Sparkles size={14} />
                  <strong>AI Coach Guidance</strong>
                </div>
                <p>
                  Breaking your target into 15-minute daily focus sprints significantly boosts retention and avoids last-minute stress.
                </p>
              </div>
            </div>

            <div className="resource-modal-actions">
              <button
                type="button"
                className="modal-ai-btn"
                onClick={() => {
                  setSelectedGoal(null);
                  navigate("/coach");
                }}
              >
                <Sparkles size={14} />
                <span>Coach me on this target</span>
              </button>

              <button
                type="button"
                className="modal-primary-btn"
                onClick={() => setSelectedGoal(null)}
              >
                <span>Save & Close</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Goals;
