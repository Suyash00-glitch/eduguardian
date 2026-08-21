export function RiskBadge({ risk }) {
  const level = (risk || "low").toLowerCase().replace(/_/g, " ");
  let label = "Low Risk";
  let badgeClass = "low";

  if (level.includes("high")) {
    label = "High Risk";
    badgeClass = "danger";
  } else if (level.includes("medium")) {
    label = "Medium Risk";
    badgeClass = "warning";
  } else if (level.includes("insufficient")) {
    label = "Insufficient Data";
    badgeClass = "neutral";
  } else {
    label = "Low Risk";
    badgeClass = "primary";
  }

  return <span className={`risk-badge ${badgeClass}`}>{label}</span>;
}

export function ConfidenceBadge({ confidence }) {
  const conf = (confidence || "LOW").toUpperCase();
  let tone = "neutral";
  let label = "Low Confidence";

  if (conf === "FULL" || conf === "HIGH") {
    tone = "primary";
    label = "High (Multi-Signal)";
  } else if (conf === "PARTIAL" || conf === "MEDIUM") {
    tone = "warning";
    label = "Partial Signal";
  } else {
    tone = "neutral";
    label = "Low (Early-Semester)";
  }

  return (
    <span
      className={`confidence-badge ${tone}`}
      style={{
        fontSize: "11px",
        fontWeight: 600,
        padding: "3px 8px",
        borderRadius: "6px",
        background: tone === "primary" ? "rgba(6,214,160,0.12)" : tone === "warning" ? "rgba(255,209,102,0.12)" : "rgba(255,255,255,0.08)",
        color: tone === "primary" ? "var(--primary)" : tone === "warning" ? "var(--warning)" : "var(--text-muted)",
        border: `1px solid ${tone === "primary" ? "rgba(6,214,160,0.25)" : tone === "warning" ? "rgba(255,209,102,0.25)" : "rgba(255,255,255,0.1)"}`,
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
      }}
    >
      {label}
    </span>
  );
}

export function StatCard({ label, value, icon, tone = "neutral", suffix }) {
  return (
    <div className="teacher-stat-card">
      <div className="teacher-stat-top">
        <span className={tone !== "neutral" ? `${tone}-text` : ""}>{label}</span>
        <div className={`teacher-stat-icon ${tone}`}>{icon}</div>
      </div>
      <strong className={tone !== "neutral" ? `${tone}-text` : ""}>
        {value} {suffix && <small>{suffix}</small>}
      </strong>
    </div>
  );
}

// data: [{ label, value, color }]
export function RiskDonut({ data }) {
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  let acc = 0;
  const stops = data.map((d) => {
    const start = (acc / total) * 360;
    acc += d.value;
    const end = (acc / total) * 360;
    return `${d.color} ${start}deg ${end}deg`;
  });

  return (
    <div className="risk-donut-wrap">
      <div className="risk-donut" style={{ background: `conic-gradient(${stops.join(",")})` }}>
        <div className="risk-donut-hole" />
      </div>
      <div className="risk-legend">
        {data.map((d) => (
          <div className="risk-legend-item" key={d.label}>
            <span className="dot" style={{ background: d.color }} />
            {d.label}
            <strong>{d.value}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

// data: [{ week, attendance, engagement }]
export function EngagementChart({ data, maxValue = 100 }) {
  return (
    <div className="engagement-chart">
      <div className="engagement-chart-legend">
        <span><i className="dot attendance" />Attendance</span>
        <span><i className="dot engagement" />Engagement</span>
      </div>
      <div className="engagement-bars">
        {data.map((w) => (
          <div className="engagement-bar-group" key={w.week}>
            <div className="engagement-bar-pair">
              <div className="bar attendance" style={{ height: `${(w.attendance / maxValue) * 100}%` }} />
              <div className="bar engagement" style={{ height: `${(w.engagement / maxValue) * 100}%` }} />
            </div>
            <span>{w.week}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function EmptyState({ icon, title, message }) {
  return (
    <div className="ui-state">
      <div className="ui-state-icon">{icon}</div>
      <strong>{title}</strong>
      <span>{message}</span>
    </div>
  );
}
