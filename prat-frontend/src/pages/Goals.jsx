import React, { useCallback, useEffect, useState } from "react";
import {
  ArrowRight,
  Plus,
  Target,
  CheckCircle2,
  X,
  Sparkles,
  CheckSquare,
  Square,
  Trash2,
  Calendar,
  Layers,
  Clock,
  Flame,
  Award,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { studentService } from "../services/studentService";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

const CATEGORIES = ["Academic", "Attendance", "Assignment", "Exam Prep", "Personal"];

function Goals() {
  const navigate = useNavigate();
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");

  const [showForm, setShowForm] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // New Goal Form State
  const [form, setForm] = useState({
    title: "",
    category: "Academic",
    target: "",
    due_date: "",
    milestones: [""],
  });

  const [newMilestoneInput, setNewMilestoneInput] = useState("");
  const [addingMilestone, setAddingMilestone] = useState(false);

  const loadGoals = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await studentService.getGoals();
      setGoals(data || []);
    } catch (err) {
      setError(err.message || "Unable to load goals.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGoals();
  }, [loadGoals]);

  const handleAddFormMilestone = () => {
    setForm((prev) => ({
      ...prev,
      milestones: [...prev.milestones, ""],
    }));
  };

  const handleRemoveFormMilestone = (index) => {
    setForm((prev) => ({
      ...prev,
      milestones: prev.milestones.filter((_, idx) => idx !== index),
    }));
  };

  const handleFormMilestoneChange = (index, value) => {
    setForm((prev) => {
      const updated = [...prev.milestones];
      updated[index] = value;
      return { ...prev, milestones: updated };
    });
  };

  const createGoal = async (event) => {
    event.preventDefault();
    if (!form.title.trim()) return;

    setSubmitting(true);
    try {
      const cleanMilestones = form.milestones
        .map((m) => (typeof m === "string" ? m.trim() : ""))
        .filter(Boolean)
        .map((title) => ({ title, completed: false }));

      const newGoal = await studentService.createGoal({
        title: form.title.trim(),
        category: form.category,
        target: form.target.trim() || "100%",
        due_date: form.due_date || null,
        milestones: cleanMilestones,
      });

      setGoals((current) => [newGoal, ...current]);
      setForm({
        title: "",
        category: "Academic",
        target: "",
        due_date: "",
        milestones: [""],
      });
      setShowForm(false);
    } catch (err) {
      setError(err.message || "Unable to create goal.");
    } finally {
      setSubmitting(false);
    }
  };

  const toggleMilestone = async (goalId, milestoneId) => {
    try {
      // Optimistic update
      setGoals((prevGoals) =>
        prevGoals.map((g) => {
          if (g.id === goalId) {
            const updatedMilestones = (g.milestones || []).map((m) =>
              m.id === milestoneId ? { ...m, completed: !m.completed } : m
            );
            const doneCount = updatedMilestones.filter((m) => m.completed).length;
            const newProg = Math.round((doneCount / (updatedMilestones.length || 1)) * 100);
            const newStatus = newProg === 100 ? "completed" : newProg >= 50 ? "on-track" : "in-progress";

            const updatedGoal = {
              ...g,
              milestones: updatedMilestones,
              progress: newProg,
              status: newStatus,
            };

            if (selectedGoal && selectedGoal.id === goalId) {
              setSelectedGoal(updatedGoal);
            }
            return updatedGoal;
          }
          return g;
        })
      );

      const serverGoal = await studentService.toggleGoalMilestone(goalId, milestoneId);
      if (serverGoal) {
        setGoals((prev) => prev.map((g) => (g.id === goalId ? serverGoal : g)));
        if (selectedGoal && selectedGoal.id === goalId) {
          setSelectedGoal(serverGoal);
        }
      }
    } catch (err) {
      console.error("Failed to toggle milestone:", err);
      loadGoals();
    }
  };

  const handleAddMilestoneToGoal = async (goalId) => {
    if (!newMilestoneInput.trim()) return;
    setAddingMilestone(true);
    try {
      const serverGoal = await studentService.addGoalMilestone(goalId, newMilestoneInput.trim());
      if (serverGoal) {
        setGoals((prev) => prev.map((g) => (g.id === goalId ? serverGoal : g)));
        if (selectedGoal && selectedGoal.id === goalId) {
          setSelectedGoal(serverGoal);
        }
      }
      setNewMilestoneInput("");
    } catch (err) {
      console.error("Failed to add milestone:", err);
    } finally {
      setAddingMilestone(false);
    }
  };

  const handleDeleteMilestone = async (goalId, milestoneId, e) => {
    if (e) e.stopPropagation();
    try {
      const serverGoal = await studentService.deleteGoalMilestone(goalId, milestoneId);
      if (serverGoal) {
        setGoals((prev) => prev.map((g) => (g.id === goalId ? serverGoal : g)));
        if (selectedGoal && selectedGoal.id === goalId) {
          setSelectedGoal(serverGoal);
        }
      }
    } catch (err) {
      console.error("Failed to delete milestone:", err);
    }
  };

  const handleDeleteGoal = async (goalId, e) => {
    if (e) e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this goal?")) return;

    try {
      await studentService.deleteGoal(goalId);
      setGoals((prev) => prev.filter((g) => g.id !== goalId));
      if (selectedGoal && selectedGoal.id === goalId) {
        setSelectedGoal(null);
      }
    } catch (err) {
      alert(err.message || "Failed to delete goal.");
    }
  };

  if (loading) {
    return <LoadingState message="Loading your dynamic academic goals..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Unable to load goals"
        message={error}
        onRetry={loadGoals}
      />
    );
  }

  const completed = goals.filter((g) => (g.progress || 0) >= 100).length;
  const onTrack = goals.filter((g) => g.status === "on-track" && (g.progress || 0) < 100).length;
  const inProgress = goals.filter((g) => g.status === "in-progress" && (g.progress || 0) < 100).length;

  const filteredGoals = goals.filter((g) => {
    if (activeFilter === "all") return true;
    if (activeFilter === "completed") return (g.progress || 0) >= 100 || g.status === "completed";
    if (activeFilter === "on-track") return g.status === "on-track" && (g.progress || 0) < 100;
    if (activeFilter === "in-progress") return g.status === "in-progress" && (g.progress || 0) < 100;
    return true;
  });

  return (
    <div className="goals-page">
      {/* HEADER */}
      <div
        className="goals-header"
        style={{
          marginBottom: "24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div>
          <h1 style={{ fontSize: "var(--font-2xl)", fontWeight: 700, margin: 0, color: "var(--text)" }}>
            Academic Goals &amp; Action Plans
          </h1>
          <p style={{ margin: "6px 0 0", fontSize: "var(--font-base)", color: "var(--text-secondary)" }}>
            Real-time targets, actionable milestone steps, and weekly study tracking.
          </p>
        </div>

        <button
          className="create-goal-button"
          onClick={() => setShowForm(true)}
          style={{
            height: "40px",
            padding: "0 18px",
            borderRadius: "8px",
            background: "var(--primary)",
            color: "#061412",
            border: "none",
            fontSize: "var(--font-sm)",
            fontWeight: 700,
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            boxShadow: "0 2px 10px rgba(6, 214, 160, 0.2)",
            transition: "transform 0.15s ease",
          }}
        >
          <Plus size={18} />
          Create New Goal
        </button>
      </div>

      {/* SUMMARY METRICS CARDS */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "16px",
          marginBottom: "24px",
        }}
      >
        <div
          style={{
            padding: "16px 20px",
            borderRadius: "12px",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            display: "flex",
            alignItems: "center",
            gap: "16px",
          }}
        >
          <div
            style={{
              width: "42px",
              height: "42px",
              borderRadius: "10px",
              background: "var(--primary-soft)",
              color: "var(--primary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <Target size={22} />
          </div>
          <div>
            <span style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", display: "block" }}>
              Total Goals
            </span>
            <strong style={{ fontSize: "var(--font-xl)", color: "var(--text)", fontWeight: 700 }}>
              {goals.length}
            </strong>
          </div>
        </div>

        <div
          style={{
            padding: "16px 20px",
            borderRadius: "12px",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            display: "flex",
            alignItems: "center",
            gap: "16px",
          }}
        >
          <div
            style={{
              width: "42px",
              height: "42px",
              borderRadius: "10px",
              background: "rgba(6, 214, 160, 0.12)",
              color: "#06d6a0",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <Award size={22} />
          </div>
          <div>
            <span style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", display: "block" }}>
              Completed
            </span>
            <strong style={{ fontSize: "var(--font-xl)", color: "#06d6a0", fontWeight: 700 }}>
              {completed}
            </strong>
          </div>
        </div>

        <div
          style={{
            padding: "16px 20px",
            borderRadius: "12px",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            display: "flex",
            alignItems: "center",
            gap: "16px",
          }}
        >
          <div
            style={{
              width: "42px",
              height: "42px",
              borderRadius: "10px",
              background: "rgba(255, 209, 102, 0.12)",
              color: "#ffd166",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <Flame size={22} />
          </div>
          <div>
            <span style={{ fontSize: "var(--font-xs)", color: "var(--text-muted)", display: "block" }}>
              In Progress / On Track
            </span>
            <strong style={{ fontSize: "var(--font-xl)", color: "#ffd166", fontWeight: 700 }}>
              {inProgress + onTrack}
            </strong>
          </div>
        </div>
      </div>

      {/* FILTER TABS */}
      <div
        style={{
          display: "flex",
          gap: "8px",
          marginBottom: "18px",
          borderBottom: "1px solid var(--border)",
          paddingBottom: "12px",
          flexWrap: "wrap",
        }}
      >
        {[
          { id: "all", label: `All (${goals.length})` },
          { id: "in-progress", label: `In Progress (${inProgress})` },
          { id: "on-track", label: `On Track (${onTrack})` },
          { id: "completed", label: `Completed (${completed})` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveFilter(tab.id)}
            style={{
              padding: "6px 14px",
              borderRadius: "6px",
              border: "1px solid",
              borderColor: activeFilter === tab.id ? "var(--primary)" : "transparent",
              background: activeFilter === tab.id ? "var(--primary-soft)" : "transparent",
              color: activeFilter === tab.id ? "var(--primary)" : "var(--text-secondary)",
              fontSize: "var(--font-sm)",
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* CREATE GOAL MODAL */}
      {showForm && (
        <div className="goal-form-overlay" onClick={() => setShowForm(false)}>
          <form
            className="goal-form"
            onSubmit={createGoal}
            onClick={(e) => e.stopPropagation()}
            style={{
              padding: "26px",
              borderRadius: "16px",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              maxWidth: "520px",
              width: "100%",
              boxShadow: "0 20px 40px rgba(0,0,0,0.3)",
              maxHeight: "90vh",
              overflowY: "auto",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Target size={20} color="var(--primary)" />
                <h3 style={{ margin: 0, fontSize: "var(--font-lg)", fontWeight: 700, color: "var(--text)" }}>
                  Create Academic Target
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Title */}
            <div style={{ marginBottom: "16px" }}>
              <label style={{ fontSize: "var(--font-sm)", color: "var(--text)", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Goal Title *
              </label>
              <input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="e.g. Master DCN Subnetting & Routing"
                required
                style={{
                  width: "100%",
                  height: "42px",
                  padding: "0 12px",
                  borderRadius: "8px",
                  border: "1px solid var(--border)",
                  background: "var(--surface-soft)",
                  color: "var(--text)",
                  fontSize: "var(--font-base)",
                  outline: "none",
                }}
              />
            </div>

            {/* Category & Target */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px" }}>
              <div>
                <label style={{ fontSize: "var(--font-sm)", color: "var(--text)", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                  Category
                </label>
                <select
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  style={{
                    width: "100%",
                    height: "42px",
                    padding: "0 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--border)",
                    background: "var(--surface-soft)",
                    color: "var(--text)",
                    fontSize: "var(--font-sm)",
                    outline: "none",
                  }}
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: "var(--font-sm)", color: "var(--text)", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                  Target Metric
                </label>
                <input
                  value={form.target}
                  onChange={(e) => setForm({ ...form, target: e.target.value })}
                  placeholder="e.g. SGPA 8.5 or 85%"
                  style={{
                    width: "100%",
                    height: "42px",
                    padding: "0 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--border)",
                    background: "var(--surface-soft)",
                    color: "var(--text)",
                    fontSize: "var(--font-sm)",
                    outline: "none",
                  }}
                />
              </div>
            </div>

            {/* Due Date */}
            <div style={{ marginBottom: "18px" }}>
              <label style={{ fontSize: "var(--font-sm)", color: "var(--text)", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Target Completion Date
              </label>
              <input
                type="date"
                value={form.due_date}
                onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                style={{
                  width: "100%",
                  height: "42px",
                  padding: "0 12px",
                  borderRadius: "8px",
                  border: "1px solid var(--border)",
                  background: "var(--surface-soft)",
                  color: "var(--text)",
                  fontSize: "var(--font-sm)",
                  outline: "none",
                }}
              />
            </div>

            {/* Milestones list */}
            <div style={{ marginBottom: "24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <label style={{ fontSize: "var(--font-sm)", color: "var(--text)", fontWeight: 600 }}>
                  Actionable Milestones
                </label>
                <button
                  type="button"
                  onClick={handleAddFormMilestone}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "var(--primary)",
                    fontSize: "var(--font-xs)",
                    fontWeight: 600,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                  }}
                >
                  <Plus size={14} /> Add Step
                </button>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {form.milestones.map((m, idx) => (
                  <div key={idx} style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                    <input
                      value={m}
                      onChange={(e) => handleFormMilestoneChange(idx, e.target.value)}
                      placeholder={`Step ${idx + 1} (e.g. Complete Unit 2 Practice Set)`}
                      style={{
                        flex: 1,
                        height: "38px",
                        padding: "0 12px",
                        borderRadius: "6px",
                        border: "1px solid var(--border)",
                        background: "var(--surface-soft)",
                        color: "var(--text)",
                        fontSize: "var(--font-sm)",
                      }}
                    />
                    {form.milestones.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveFormMilestone(idx)}
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "var(--text-muted)",
                          cursor: "pointer",
                          padding: "4px",
                        }}
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                style={{
                  height: "40px",
                  padding: "0 16px",
                  borderRadius: "8px",
                  border: "1px solid var(--border)",
                  background: "transparent",
                  color: "var(--text-secondary)",
                  fontSize: "var(--font-sm)",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={submitting}
                style={{
                  height: "40px",
                  padding: "0 22px",
                  borderRadius: "8px",
                  border: "none",
                  background: "var(--primary)",
                  color: "#061412",
                  fontWeight: 700,
                  fontSize: "var(--font-sm)",
                  cursor: "pointer",
                  opacity: submitting ? 0.7 : 1,
                }}
              >
                {submitting ? "Saving..." : "Save Goal"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* GOALS GRID */}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
          gap: "16px",
        }}
      >
        {filteredGoals.length === 0 ? (
          <div
            style={{
              gridColumn: "1 / -1",
              textAlign: "center",
              padding: "40px 20px",
              borderRadius: "12px",
              border: "1px solid var(--border)",
              background: "var(--surface)",
              color: "var(--text-muted)",
            }}
          >
            <Target size={32} style={{ opacity: 0.5, marginBottom: "10px" }} />
            <p style={{ margin: 0, fontSize: "var(--font-base)", fontWeight: 600, color: "var(--text)" }}>
              No goals found in this category.
            </p>
            <p style={{ margin: "6px 0 0", fontSize: "var(--font-sm)" }}>
              Click "Create New Goal" above to add your first study milestone.
            </p>
          </div>
        ) : (
          filteredGoals.map((goal) => {
            const isDone = (goal.progress || 0) >= 100;
            const milestoneCount = (goal.milestones || []).length;
            const completedMilestones = (goal.milestones || []).filter((m) => m.completed).length;

            return (
              <div
                key={goal.id}
                onClick={() => setSelectedGoal(goal)}
                style={{
                  padding: "20px",
                  borderRadius: "14px",
                  border: `1px solid ${isDone ? "rgba(6, 214, 160, 0.4)" : "var(--border)"}`,
                  background: isDone ? "linear-gradient(180deg, var(--surface) 0%, rgba(6, 214, 160, 0.04) 100%)" : "var(--surface)",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  cursor: "pointer",
                  transition: "transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease",
                  position: "relative",
                }}
                className="goal-card-hover"
              >
                <div>
                  {/* Category & Status */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                    <span
                      style={{
                        fontSize: "11px",
                        padding: "2px 8px",
                        borderRadius: "12px",
                        background: "var(--surface-soft)",
                        border: "1px solid var(--border)",
                        color: "var(--text-secondary)",
                        fontWeight: 600,
                      }}
                    >
                      {goal.category || "Academic"}
                    </span>

                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <span
                        style={{
                          fontSize: "11px",
                          padding: "2px 8px",
                          borderRadius: "12px",
                          background: isDone ? "rgba(6, 214, 160, 0.15)" : "rgba(255, 209, 102, 0.15)",
                          color: isDone ? "#06d6a0" : "#ffd166",
                          fontWeight: 700,
                          textTransform: "uppercase",
                        }}
                      >
                        {isDone ? "Completed" : goal.status === "on-track" ? "On Track" : "In Progress"}
                      </span>

                      <button
                        type="button"
                        onClick={(e) => handleDeleteGoal(goal.id, e)}
                        title="Delete Goal"
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "var(--text-muted)",
                          cursor: "pointer",
                          padding: "2px",
                          display: "flex",
                        }}
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>

                  {/* Title */}
                  <h3
                    style={{
                      margin: "0 0 10px",
                      fontSize: "16px",
                      fontWeight: 700,
                      color: "var(--text)",
                      lineHeight: "1.4",
                    }}
                  >
                    {goal.title}
                  </h3>

                  {/* Target & Due date */}
                  <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", fontSize: "12px", color: "var(--text-secondary)", marginBottom: "16px" }}>
                    {goal.target && (
                      <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                        <Target size={13} color="var(--primary)" />
                        <strong>{goal.target}</strong>
                      </span>
                    )}
                    {goal.due_date && (
                      <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                        <Calendar size={13} />
                        {new Date(goal.due_date).toLocaleDateString("en-IN", { month: "short", day: "numeric" })}
                      </span>
                    )}
                  </div>
                </div>

                {/* Progress Bar & Footer */}
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "6px" }}>
                    <span style={{ color: "var(--text-muted)" }}>
                      {completedMilestones}/{milestoneCount} milestones
                    </span>
                    <strong style={{ color: isDone ? "#06d6a0" : "var(--primary)" }}>{goal.progress || 0}%</strong>
                  </div>

                  <div style={{ height: "6px", background: "rgba(255,255,255,0.08)", borderRadius: "4px", overflow: "hidden", marginBottom: "12px" }}>
                    <div
                      style={{
                        height: "100%",
                        width: `${goal.progress || 0}%`,
                        background: isDone ? "#06d6a0" : "var(--primary)",
                        borderRadius: "inherit",
                        transition: "width 0.3s ease",
                      }}
                    />
                  </div>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      paddingTop: "10px",
                      borderTop: "1px solid var(--border)",
                      fontSize: "12px",
                      color: "var(--primary)",
                      fontWeight: 600,
                    }}
                  >
                    <span>View &amp; Check Off Steps</span>
                    <ArrowRight size={14} />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </section>

      {/* GOAL ACTION DETAILS DRAWER / MODAL */}
      {selectedGoal && (
        <div className="goal-form-overlay" onClick={() => setSelectedGoal(null)}>
          <div
            style={{
              padding: "26px",
              borderRadius: "16px",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              maxWidth: "560px",
              width: "100%",
              boxShadow: "0 20px 50px rgba(0,0,0,0.4)",
              maxHeight: "90vh",
              overflowY: "auto",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "16px" }}>
              <div>
                <span
                  style={{
                    fontSize: "11px",
                    padding: "2px 8px",
                    borderRadius: "12px",
                    background: "var(--primary-soft)",
                    color: "var(--primary)",
                    fontWeight: 700,
                    display: "inline-block",
                    marginBottom: "6px",
                  }}
                >
                  {selectedGoal.category || "Academic"}
                </span>
                <h3 style={{ margin: 0, fontSize: "18px", fontWeight: 700, color: "var(--text)" }}>
                  {selectedGoal.title}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedGoal(null)}
                style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer", padding: "4px" }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Progress Display */}
            <div style={{ padding: "14px 16px", borderRadius: "10px", background: "var(--surface-soft)", border: "1px solid var(--border)", marginBottom: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", marginBottom: "8px" }}>
                <span style={{ color: "var(--text-secondary)" }}>Goal Progress</span>
                <strong style={{ color: (selectedGoal.progress || 0) >= 100 ? "#06d6a0" : "var(--primary)", fontSize: "14px" }}>
                  {selectedGoal.progress || 0}% Complete
                </strong>
              </div>
              <div style={{ height: "8px", background: "rgba(255,255,255,0.08)", borderRadius: "4px", overflow: "hidden" }}>
                <div
                  style={{
                    height: "100%",
                    width: `${selectedGoal.progress || 0}%`,
                    background: (selectedGoal.progress || 0) >= 100 ? "#06d6a0" : "var(--primary)",
                    borderRadius: "inherit",
                    transition: "width 0.3s ease",
                  }}
                />
              </div>
            </div>

            {/* Milestone Steps */}
            <div style={{ marginBottom: "20px" }}>
              <h4 style={{ fontSize: "14px", fontWeight: 700, color: "var(--text)", margin: "0 0 12px" }}>
                Actionable Milestones
              </h4>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "14px" }}>
                {(selectedGoal.milestones || []).length === 0 ? (
                  <p style={{ color: "var(--text-muted)", fontSize: "13px", margin: "4px 0" }}>
                    No milestones added yet. Add a milestone below!
                  </p>
                ) : (
                  (selectedGoal.milestones || []).map((m) => (
                    <div
                      key={m.id}
                      onClick={() => toggleMilestone(selectedGoal.id, m.id)}
                      style={{
                        padding: "12px 14px",
                        borderRadius: "10px",
                        background: m.completed ? "rgba(6,214,160,0.08)" : "var(--surface-soft)",
                        border: `1px solid ${m.completed ? "rgba(6,214,160,0.3)" : "var(--border)"}`,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        cursor: "pointer",
                        fontSize: "14px",
                        color: m.completed ? "var(--primary)" : "var(--text)",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "10px", flex: 1 }}>
                        {m.completed ? (
                          <CheckSquare size={20} style={{ color: "#06d6a0", flexShrink: 0 }} />
                        ) : (
                          <Square size={20} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
                        )}
                        <span style={{ textDecoration: m.completed ? "line-through" : "none", color: m.completed ? "var(--text-muted)" : "var(--text)" }}>
                          {m.title}
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={(e) => handleDeleteMilestone(selectedGoal.id, m.id, e)}
                        title="Delete Milestone"
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "var(--text-muted)",
                          cursor: "pointer",
                          padding: "4px",
                          display: "flex",
                        }}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))
                )}
              </div>

              {/* Add New Milestone Input */}
              <div style={{ display: "flex", gap: "8px" }}>
                <input
                  value={newMilestoneInput}
                  onChange={(e) => setNewMilestoneInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddMilestoneToGoal(selectedGoal.id)}
                  placeholder="Add another milestone step..."
                  style={{
                    flex: 1,
                    height: "38px",
                    padding: "0 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--border)",
                    background: "var(--surface-soft)",
                    color: "var(--text)",
                    fontSize: "13px",
                  }}
                />
                <button
                  type="button"
                  disabled={addingMilestone || !newMilestoneInput.trim()}
                  onClick={() => handleAddMilestoneToGoal(selectedGoal.id)}
                  style={{
                    height: "38px",
                    padding: "0 14px",
                    borderRadius: "8px",
                    background: "var(--primary-soft)",
                    color: "var(--primary)",
                    border: "1px solid var(--primary)",
                    fontWeight: 600,
                    fontSize: "13px",
                    cursor: "pointer",
                  }}
                >
                  {addingMilestone ? "Adding..." : "Add Step"}
                </button>
              </div>
            </div>

            {/* Modal Actions */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "24px", paddingTop: "14px", borderTop: "1px solid var(--border)" }}>
              <button
                type="button"
                onClick={() => {
                  setSelectedGoal(null);
                  navigate("/coach");
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--primary)",
                  fontSize: "13px",
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <Sparkles size={16} />
                Discuss Goal with AI Coach
              </button>

              <button
                type="button"
                onClick={() => setSelectedGoal(null)}
                style={{
                  height: "38px",
                  padding: "0 20px",
                  borderRadius: "8px",
                  border: "none",
                  background: "var(--primary)",
                  color: "#061412",
                  fontWeight: 700,
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Goals;
