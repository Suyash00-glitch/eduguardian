import React, { useCallback, useEffect, useState } from "react";
import { ArrowRight, Plus, Target, CheckCircle2, X } from "lucide-react";

import { studentService } from "../services/studentService";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

function Goals() {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);

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

      setForm({
        title: "",
        target: "",
      });

      setShowForm(false);
    } catch (err) {
      setError(err.message || "Unable to create goal.");
    }
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

          <p>Set small targets and keep yourself accountable.</p>
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

          <span>Keep your goals realistic and achievable.</span>
        </div>
      </div>

      {/* FORM */}

      {showForm && (
        <div className="goal-form-overlay">
          <form className="goal-form" onSubmit={createGoal}>
            <div className="goal-form-header">
              <div>
                <span className="section-eyebrow">NEW GOAL</span>

                <h3>Create a personal goal</h3>
              </div>

              <button type="button" onClick={() => setShowForm(false)}>
                <X size={15} />
              </button>
            </div>

            <label>
              Goal
              <input
                value={form.title}
                onChange={(event) =>
                  setForm({
                    ...form,
                    title: event.target.value,
                  })
                }
                placeholder="e.g. Maintain 90% attendance"
              />
            </label>

            <label>
              Target
              <input
                value={form.target}
                onChange={(event) =>
                  setForm({
                    ...form,
                    target: event.target.value,
                  })
                }
                placeholder="e.g. 90%"
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

      {/* GOALS */}

      <section className="goals-panel">
        <div className="goals-panel-header">
          <div>
            <span className="section-eyebrow">YOUR GOALS</span>

            <h3>Academic targets</h3>
          </div>

          <span>{goals.length} goals</span>
        </div>

        <div className="goal-list">
          {goals.length === 0 ? (
            <div className="goals-empty">
              <Target size={20} />

              <strong>No goals yet</strong>

              <span>Create your first academic goal.</span>
            </div>
          ) : (
            goals.map((goal) => (
              <div className="goal-row" key={goal.id}>
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

                    <span className={`goal-status ${goal.status}`}>
                      {goal.status}
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

                <button className="goal-open">
                  <ArrowRight size={14} />
                </button>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}

export default Goals;
