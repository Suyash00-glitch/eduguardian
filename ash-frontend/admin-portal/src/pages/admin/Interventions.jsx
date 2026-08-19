import React, { useState } from "react";
import { FolderPlus, Send, CheckCircle2 } from "lucide-react";

export default function Interventions() {
  const [targetAudience, setTargetAudience] = useState("ALL");
  const [title, setTitle] = useState("");
  const [link, setLink] = useState("");
  const [success, setSuccess] = useState(false);
  const [reached, setReached] = useState(0);

  async function handleSend(e) {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://127.0.0.1:8000/api/interventions/resource", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ target_category: targetAudience, title, resource_url: link }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "failed to dispatch resource");

      setReached(data.students_reached);
      setSuccess(true);
      setTitle("");
      setLink("");
      setTimeout(() => setSuccess(false), 4000);
    } catch (err) {
      console.error("resource dispatch failed:", err);
      alert(err.message);
    }
  }

  return (
    <div className="interventions-page">
      <div className="interventions-header">
        <span className="dashboard-eyebrow">SUPPORT DISPATCH</span>
        <h2>Resource &amp; Material Dispatch</h2>
        <p>Send study notes or catch-up material to the whole cohort or targeted by risk level.</p>
      </div>

      <div className="teacher-panel">
        <div className="teacher-panel-header">
          <h3><FolderPlus size={14} className="inline-icon" /> Dispatch Center</h3>
        </div>

        {success && (
          <div className="success-inline">
            <CheckCircle2 size={15} />
            <span>Resource sent to {reached} students successfully!</span>
          </div>
        )}

        <form onSubmit={handleSend} className="dispatch-form">
          <div>
            <label>Target audience</label>
            <select value={targetAudience} onChange={(e) => setTargetAudience(e.target.value)}>
              <option value="ALL">Entire cohort (all students)</option>
              <option value="HIGH">High-risk students only</option>
              <option value="MEDIUM">Medium-risk students only</option>
              <option value="LOW">Low-risk students only</option>
            </select>
          </div>

          <div>
            <label>Material title</label>
            <input
              type="text"
              placeholder="e.g. Week 4 Remedial Notes"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          <div className="dispatch-link-row">
            <div className="dispatch-link-input">
              <label>Resource link</label>
              <input
                type="url"
                placeholder="Drive / LMS link"
                value={link}
                onChange={(e) => setLink(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="dispatch-submit">
              <Send size={13} /> Dispatch
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
