import React, { useCallback, useEffect, useState } from "react";
import {
  Users,
  UserPlus,
  Edit2,
  Trash2,
  CheckCircle2,
  XCircle,
  Shield,
  Phone,
  Mail,
  Briefcase,
  Layers,
  Search,
  AlertCircle,
  Plus
} from "lucide-react";
import { EmptyState } from "../../components/shared/Shared";

export default function MentorManagement() {
  const [mentors, setMentors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    employee_id: "",
    email: "",
    department: "ISE",
    designation: "Assistant Professor",
    capacity: 5,
    is_active: true,
    phone: "",
  });
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formError, setFormError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const fetchMentors = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:5000/api/mentors", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load mentors list.");
      const data = await res.json();
      setMentors(data.mentors || data.teachers || []);
    } catch (err) {
      console.error(err);
      setError("Unable to load mentors from backend.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMentors();
  }, [fetchMentors]);

  function openAddModal() {
    setIsEditing(false);
    setEditingId(null);
    setFormData({
      name: "",
      employee_id: "",
      email: "",
      department: "ISE",
      designation: "Assistant Professor",
      capacity: 5,
      is_active: true,
      phone: "",
    });
    setFormError("");
    setModalOpen(true);
  }

  function openEditModal(m) {
    setIsEditing(true);
    setEditingId(m.id);
    setFormData({
      name: m.name || m.full_name || "",
      employee_id: m.employee_id || "",
      email: m.email || "",
      department: m.department || "ISE",
      designation: m.designation || "Assistant Professor",
      capacity: m.capacity || m.max_capacity || 5,
      is_active: m.is_active !== undefined ? m.is_active : true,
      phone: m.phone || "",
    });
    setFormError("");
    setModalOpen(true);
  }

  async function handleFormSubmit(e) {
    e.preventDefault();
    setFormSubmitting(true);
    setFormError("");

    try {
      const token = localStorage.getItem("token");
      const url = isEditing
        ? `http://localhost:5000/api/mentors/${editingId}`
        : "http://localhost:5000/api/mentors";
      const method = isEditing ? "PUT" : "POST";

      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Failed to save mentor.");
      }

      setModalOpen(false);
      setSuccessMsg(isEditing ? "Mentor updated successfully." : "New mentor created successfully.");
      setTimeout(() => setSuccessMsg(""), 4000);
      await fetchMentors();
    } catch (err) {
      setFormError(err.message || "An error occurred.");
    } finally {
      setFormSubmitting(false);
    }
  }

  async function handleDelete(mentorId, mentorName) {
    if (!window.confirm(`Are you sure you want to deactivate mentor "${mentorName}"? Active mentee assignments will be archived.`)) {
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:5000/api/mentors/${mentorId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to delete mentor.");

      setSuccessMsg(`Mentor "${mentorName}" deactivated.`);
      setTimeout(() => setSuccessMsg(""), 4000);
      await fetchMentors();
    } catch (err) {
      alert(err.message || "Failed to delete mentor.");
    }
  }

  async function handleToggleStatus(mentor) {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:5000/api/mentors/${mentor.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ is_active: !mentor.is_active }),
      });
      if (!res.ok) throw new Error("Failed to update status.");
      await fetchMentors();
    } catch (err) {
      alert("Could not update mentor status.");
    }
  }

  const filteredMentors = mentors.filter((m) => {
    const nameMatch = (m.name || m.full_name || "").toLowerCase().includes(search.toLowerCase()) ||
      (m.employee_id || "").toLowerCase().includes(search.toLowerCase()) ||
      (m.email || "").toLowerCase().includes(search.toLowerCase());

    if (statusFilter === "active") return nameMatch && m.is_active;
    if (statusFilter === "inactive") return nameMatch && !m.is_active;
    if (statusFilter === "available") return nameMatch && m.is_active && m.current_load < m.capacity;
    if (statusFilter === "full") return nameMatch && m.is_active && m.current_load >= m.capacity;
    return nameMatch;
  });

  return (
    <div className="mentor-mgmt-page" style={{ padding: "8px 0" }}>
      {/* HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
        <div>
          <h2>Mentor Management</h2>
          <p style={{ color: "rgba(255,255,255,0.6)", fontSize: "13px", marginTop: "4px" }}>
            Add, update, and manage faculty mentors, mentee quotas, and availability.
          </p>
        </div>
        <button
          type="button"
          onClick={openAddModal}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            background: "var(--primary)",
            color: "#03251c",
            border: "none",
            borderRadius: "8px",
            padding: "10px 18px",
            fontSize: "13px",
            fontWeight: 700,
            cursor: "pointer",
            boxShadow: "0 2px 8px rgba(6, 214, 160, 0.3)"
          }}
        >
          <UserPlus size={16} />
          <span>Add New Mentor</span>
        </button>
      </div>

      {successMsg && (
        <div style={{
          background: "rgba(16, 185, 129, 0.15)",
          border: "1px solid rgba(16, 185, 129, 0.4)",
          color: "#34d399",
          padding: "12px 16px",
          borderRadius: "8px",
          marginBottom: "16px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          fontSize: "13px"
        }}>
          <CheckCircle2 size={16} />
          <span>{successMsg}</span>
        </div>
      )}

      {/* FILTER BAR */}
      <div style={{
        display: "flex",
        gap: "12px",
        marginBottom: "16px",
        flexWrap: "wrap"
      }}>
        <div style={{
          display: "flex",
          alignItems: "center",
          background: "rgba(255, 255, 255, 0.05)",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          borderRadius: "8px",
          padding: "0 12px",
          flex: "1",
          minWidth: "240px"
        }}>
          <Search size={14} color="rgba(255,255,255,0.4)" />
          <input
            type="text"
            placeholder="Search by name, employee ID, or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              background: "transparent",
              border: "none",
              color: "#fff",
              padding: "10px 8px",
              width: "100%",
              outline: "none",
              fontSize: "13px"
            }}
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.12)",
            color: "#fff",
            borderRadius: "8px",
            padding: "8px 14px",
            fontSize: "13px",
            outline: "none"
          }}
        >
          <option value="all">All Mentors</option>
          <option value="available">Available Only</option>
          <option value="full">Full Capacity</option>
          <option value="active">Active Only</option>
          <option value="inactive">Inactive Only</option>
        </select>
      </div>

      {/* MENTORS GRID */}
      {loading ? (
        <div className="ui-state"><span>Loading mentors from database...</span></div>
      ) : error ? (
        <div className="ui-state"><span className="danger-text">{error}</span></div>
      ) : filteredMentors.length === 0 ? (
        <EmptyState
          icon={<Users size={24} />}
          title="No mentors found"
          message={search ? "No mentors match your search criteria." : "Click 'Add New Mentor' to create your first faculty mentor."}
        />
      ) : (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
          gap: "16px"
        }}>
          {filteredMentors.map((m) => {
            const isFull = m.current_load >= m.capacity;
            const statusLabel = !m.is_active ? "INACTIVE" : (isFull ? "FULL" : "AVAILABLE");
            const badgeBg = !m.is_active ? "rgba(148, 163, 184, 0.15)" : (isFull ? "rgba(239, 68, 68, 0.15)" : "rgba(16, 185, 129, 0.15)");
            const badgeColor = !m.is_active ? "#94a3b8" : (isFull ? "#f87171" : "#34d399");
            const badgeBorder = !m.is_active ? "rgba(148, 163, 184, 0.3)" : (isFull ? "rgba(239, 68, 68, 0.3)" : "rgba(16, 185, 129, 0.3)");

            return (
              <div
                key={m.id}
                style={{
                  background: "rgba(18, 24, 38, 0.7)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "12px",
                  padding: "20px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  transition: "all 0.2s ease"
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                    <div>
                      <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#fff", margin: 0 }}>
                        {m.name || m.full_name}
                      </h3>
                      <div style={{ fontSize: "12px", color: "var(--primary)", marginTop: "2px", fontWeight: 500 }}>
                        {m.designation || "Assistant Professor"} · {m.department}
                      </div>
                    </div>
                    <span style={{
                      background: badgeBg,
                      color: badgeColor,
                      border: `1px solid ${badgeBorder}`,
                      borderRadius: "6px",
                      padding: "4px 8px",
                      fontSize: "11px",
                      fontWeight: 700,
                      letterSpacing: "0.05em"
                    }}>
                      {statusLabel}
                    </span>
                  </div>

                  <div style={{ fontSize: "12px", color: "rgba(255,255,255,0.7)", display: "flex", flexDirection: "column", gap: "6px", marginBottom: "16px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <Briefcase size={13} color="rgba(255,255,255,0.4)" />
                      <span>ID: <strong>{m.employee_id}</strong></span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <Mail size={13} color="rgba(255,255,255,0.4)" />
                      <span>{m.email}</span>
                    </div>
                    {m.phone && (
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <Phone size={13} color="rgba(255,255,255,0.4)" />
                        <span>{m.phone}</span>
                      </div>
                    )}
                  </div>

                  {/* CAPACITY PROGRESS */}
                  <div style={{
                    background: "rgba(255, 255, 255, 0.03)",
                    border: "1px solid rgba(255, 255, 255, 0.06)",
                    borderRadius: "8px",
                    padding: "10px 12px",
                    marginBottom: "16px"
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "6px" }}>
                      <span style={{ color: "rgba(255,255,255,0.6)" }}>Mentee Quota</span>
                      <strong style={{ color: isFull ? "#f87171" : "#fff" }}>
                        {m.current_load} / {m.capacity} mentees
                      </strong>
                    </div>
                    <div style={{ height: "6px", background: "rgba(255,255,255,0.1)", borderRadius: "3px", overflow: "hidden" }}>
                      <div style={{
                        height: "100%",
                        width: `${Math.min(100, (m.current_load / m.capacity) * 100)}%`,
                        background: isFull ? "#ef4444" : (m.current_load >= m.capacity - 1 ? "#f59e0b" : "#10b981"),
                        borderRadius: "3px"
                      }} />
                    </div>
                    <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.4)", marginTop: "4px" }}>
                      {m.available_slots} slot{m.available_slots !== 1 ? "s" : ""} remaining
                    </div>
                  </div>
                </div>

                {/* ACTIONS */}
                <div style={{ display: "flex", gap: "8px", borderTop: "1px solid rgba(255, 255, 255, 0.06)", paddingTop: "12px" }}>
                  <button
                    type="button"
                    onClick={() => openEditModal(m)}
                    style={{
                      flex: 1,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "6px",
                      background: "rgba(255, 255, 255, 0.06)",
                      border: "1px solid rgba(255, 255, 255, 0.12)",
                      color: "#fff",
                      borderRadius: "6px",
                      padding: "8px 10px",
                      fontSize: "12px",
                      cursor: "pointer"
                    }}
                  >
                    <Edit2 size={13} />
                    <span>Edit</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleToggleStatus(m)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "4px",
                      background: m.is_active ? "rgba(239, 68, 68, 0.1)" : "rgba(16, 185, 129, 0.1)",
                      border: `1px solid ${m.is_active ? "rgba(239, 68, 68, 0.25)" : "rgba(16, 185, 129, 0.25)"}`,
                      color: m.is_active ? "#f87171" : "#34d399",
                      borderRadius: "6px",
                      padding: "8px 10px",
                      fontSize: "12px",
                      cursor: "pointer"
                    }}
                    title={m.is_active ? "Deactivate Mentor" : "Activate Mentor"}
                  >
                    {m.is_active ? "Deactivate" : "Activate"}
                  </button>

                  <button
                    type="button"
                    onClick={() => handleDelete(m.id, m.name || m.full_name)}
                    style={{
                      background: "rgba(239, 68, 68, 0.08)",
                      border: "1px solid rgba(239, 68, 68, 0.2)",
                      color: "#ef4444",
                      borderRadius: "6px",
                      padding: "8px 10px",
                      cursor: "pointer"
                    }}
                    title="Archive Mentor"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ADD / EDIT MODAL */}
      {modalOpen && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: "rgba(0, 0, 0, 0.75)",
          backdropFilter: "blur(4px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000,
          padding: "20px"
        }}>
          <div style={{
            background: "#121826",
            border: "1px solid rgba(255, 255, 255, 0.15)",
            borderRadius: "16px",
            padding: "28px",
            width: "100%",
            maxWidth: "480px",
            boxShadow: "0 20px 40px rgba(0,0,0,0.5)"
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
              <h3 style={{ margin: 0, fontSize: "18px", fontWeight: 700, color: "#fff" }}>
                {isEditing ? "Edit Mentor Profile" : "Add Faculty Mentor"}
              </h3>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                style={{ background: "transparent", border: "none", color: "rgba(255,255,255,0.5)", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            {formError && (
              <div style={{
                background: "rgba(239, 68, 68, 0.15)",
                border: "1px solid rgba(239, 68, 68, 0.4)",
                color: "#f87171",
                padding: "10px 14px",
                borderRadius: "8px",
                marginBottom: "16px",
                fontSize: "12px"
              }}>
                {formError}
              </div>
            )}

            <form onSubmit={handleFormSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <label style={{ display: "block", fontSize: "12px", color: "rgba(255,255,255,0.7)", marginBottom: "4px" }}>
                  Full Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Preethi Salian K"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  style={{
                    width: "100%",
                    background: "var(--surface-soft)",
                    border: "1.5px solid var(--border)",
                    borderRadius: "8px",
                    padding: "10px 12px",
                    color: "var(--text)",
                    fontSize: "13px",
                    boxSizing: "border-box"
                  }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", color: "var(--text-secondary)", marginBottom: "4px" }}>
                    Employee ID *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="EMP-001"
                    value={formData.employee_id}
                    onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                    style={{
                      width: "100%",
                      background: "var(--surface-soft)",
                      border: "1.5px solid var(--border)",
                      borderRadius: "8px",
                      padding: "10px 12px",
                      color: "var(--text)",
                      fontSize: "13px",
                      boxSizing: "border-box"
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "12px", color: "var(--text-secondary)", marginBottom: "4px" }}>
                    Department *
                  </label>
                  <select
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    style={{
                      width: "100%",
                      background: "var(--surface-soft)",
                      border: "1.5px solid var(--border)",
                      borderRadius: "8px",
                      padding: "10px 12px",
                      color: "var(--text)",
                      fontSize: "13px",
                      boxSizing: "border-box"
                    }}
                  >
                    <option value="ISE">ISE</option>
                    <option value="CSE">CSE</option>
                    <option value="AIML">AIML</option>
                    <option value="ECE">ECE</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12px", color: "var(--text-secondary)", marginBottom: "4px" }}>
                  Email Address *
                </label>
                <input
                  type="email"
                  required
                  placeholder="sarah.jenkins@university.edu"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  style={{
                    width: "100%",
                    background: "var(--surface-soft)",
                    border: "1.5px solid var(--border)",
                    borderRadius: "8px",
                    padding: "10px 12px",
                    color: "var(--text)",
                    fontSize: "13px",
                    boxSizing: "border-box"
                  }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", color: "var(--text-secondary)", marginBottom: "4px" }}>
                    Designation
                  </label>
                  <select
                    value={formData.designation}
                    onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                    style={{
                      width: "100%",
                      background: "var(--surface-soft)",
                      border: "1.5px solid var(--border)",
                      borderRadius: "8px",
                      padding: "10px 12px",
                      color: "var(--text)",
                      fontSize: "13px",
                      boxSizing: "border-box"
                    }}
                  >
                    <option value="Assistant Professor">Assistant Professor</option>
                    <option value="Associate Professor">Associate Professor</option>
                    <option value="Professor">Professor</option>
                    <option value="Head of Department">Head of Department</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "12px", color: "var(--text-secondary)", marginBottom: "4px" }}>
                    Max Mentees / Capacity
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={formData.capacity}
                    onChange={(e) => setFormData({ ...formData, capacity: parseInt(e.target.value) || 5 })}
                    style={{
                      width: "100%",
                      background: "var(--surface-soft)",
                      border: "1.5px solid var(--border)",
                      borderRadius: "8px",
                      padding: "10px 12px",
                      color: "var(--text)",
                      fontSize: "13px",
                      boxSizing: "border-box"
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12px", color: "var(--text-secondary)", marginBottom: "4px" }}>
                  Phone Number (Optional)
                </label>
                <input
                  type="tel"
                  placeholder="+91 98765 43210"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  style={{
                    width: "100%",
                    background: "var(--surface-soft)",
                    border: "1.5px solid var(--border)",
                    borderRadius: "8px",
                    padding: "10px 12px",
                    color: "var(--text)",
                    fontSize: "13px",
                    boxSizing: "border-box"
                  }}
                />
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "4px" }}>
                <input
                  type="checkbox"
                  id="is_active_toggle"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  style={{ cursor: "pointer" }}
                />
                <label htmlFor="is_active_toggle" style={{ fontSize: "13px", color: "#fff", cursor: "pointer" }}>
                  Mentor is Available for Active Assignment
                </label>
              </div>

              <div style={{ display: "flex", gap: "10px", marginTop: "12px" }}>
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  style={{
                    flex: 1,
                    background: "rgba(255,255,255,0.08)",
                    border: "1px solid rgba(255,255,255,0.15)",
                    color: "#fff",
                    borderRadius: "8px",
                    padding: "10px",
                    fontSize: "13px",
                    cursor: "pointer"
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={formSubmitting}
                  style={{
                    flex: 2,
                    background: "var(--primary)",
                    border: "none",
                    color: "#03251c",
                    borderRadius: "8px",
                    padding: "10px",
                    fontSize: "13px",
                    fontWeight: 700,
                    cursor: "pointer"
                  }}
                >
                  {formSubmitting ? "Saving..." : (isEditing ? "Save Changes" : "Create Mentor")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
