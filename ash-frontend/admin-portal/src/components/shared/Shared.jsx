import React from "react";

export function RiskBadge({ risk }) {
  const level = (risk || "low").toLowerCase().replace(/_/g, " ");
  let label = "Low Risk";
  let tone = "primary";

  if (level.includes("high")) {
    label = "High Risk";
    tone = "danger";
  } else if (level.includes("medium")) {
    label = "Medium Risk";
    tone = "warning";
  } else if (level.includes("insufficient")) {
    label = "Insufficient Data";
    tone = "neutral";
  } else {
    label = "Low Risk / Stable";
    tone = "primary";
  }

  const colors = {
    danger: { bg: "rgba(239, 68, 68, 0.15)", text: "#ef4444", border: "rgba(239, 68, 68, 0.3)" },
    warning: { bg: "rgba(245, 158, 11, 0.15)", text: "#f59e0b", border: "rgba(245, 158, 11, 0.3)" },
    primary: { bg: "rgba(0, 213, 155, 0.15)", text: "#00d59b", border: "rgba(0, 213, 155, 0.3)" },
    neutral: { bg: "rgba(148, 163, 184, 0.12)", text: "#94a3b8", border: "rgba(148, 163, 184, 0.25)" },
  };

  const style = colors[tone] || colors.neutral;

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "3px 10px",
        borderRadius: "6px",
        fontSize: "12px",
        fontWeight: 700,
        background: style.bg,
        color: style.text,
        border: `1px solid ${style.border}`,
        whiteSpace: "nowrap",
      }}
    >
      {label}
    </span>
  );
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
      style={{
        fontSize: "11px",
        fontWeight: 600,
        padding: "3px 8px",
        borderRadius: "6px",
        background: tone === "primary" ? "rgba(0, 213, 155, 0.12)" : tone === "warning" ? "rgba(245, 158, 11, 0.12)" : "rgba(255, 255, 255, 0.08)",
        color: tone === "primary" ? "#00d59b" : tone === "warning" ? "#f59e0b" : "#94a3b8",
        border: `1px solid ${tone === "primary" ? "rgba(0, 213, 155, 0.25)" : tone === "warning" ? "rgba(245, 158, 11, 0.25)" : "rgba(255, 255, 255, 0.1)"}`,
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
  const toneColors = {
    danger: { text: "#ef4444", bg: "rgba(239, 68, 68, 0.12)", border: "rgba(239, 68, 68, 0.2)" },
    warning: { text: "#f59e0b", bg: "rgba(245, 158, 11, 0.12)", border: "rgba(245, 158, 11, 0.2)" },
    primary: { text: "#00d59b", bg: "rgba(0, 213, 155, 0.12)", border: "rgba(0, 213, 155, 0.2)" },
    neutral: { text: "#f1f7f6", bg: "rgba(255, 255, 255, 0.06)", border: "rgba(255, 255, 255, 0.08)" },
  };

  const style = toneColors[tone] || toneColors.neutral;

  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "12px",
        padding: "18px 20px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        minHeight: "110px",
        transition: "transform 0.2s ease, border-color 0.2s ease",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-secondary)" }}>{label}</span>
        <div
          style={{
            width: "32px",
            height: "32px",
            borderRadius: "8px",
            background: style.bg,
            color: style.text,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {icon}
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
        <span style={{ fontSize: "28px", fontWeight: 800, color: style.text, lineHeight: 1 }}>{value}</span>
        {suffix && <span style={{ fontSize: "13px", color: "var(--text-muted)", fontWeight: 500 }}>{suffix}</span>}
      </div>
    </div>
  );
}

// data: [{ label, value, color }]
export function RiskDonut({ data }) {
  const total = data.reduce((s, d) => s + (Number(d.value) || 0), 0);

  // SVG Circular progress dimensions
  const size = 160;
  const strokeWidth = 22;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  let cumulativePercent = 0;

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-around", padding: "16px 8px", gap: "24px", flexWrap: "wrap" }}>
      {/* SVG Donut */}
      <div style={{ position: "relative", width: `${size}px`, height: `${size}px`, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg width={size} height={size} style={{ transform: "rotate(-90deg)", overflow: "visible" }}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="rgba(255, 255, 255, 0.05)"
            strokeWidth={strokeWidth}
          />
          {total > 0 ? (
            data.map((slice, i) => {
              const val = Number(slice.value) || 0;
              if (val <= 0) return null;
              const percent = val / total;
              const strokeDasharray = `${percent * circumference} ${circumference}`;
              const strokeDashoffset = -cumulativePercent * circumference;
              cumulativePercent += percent;

              return (
                <circle
                  key={slice.label || i}
                  cx={size / 2}
                  cy={size / 2}
                  r={radius}
                  fill="transparent"
                  stroke={slice.color}
                  strokeWidth={strokeWidth}
                  strokeDasharray={strokeDasharray}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  style={{ transition: "stroke-dasharray 0.5s ease" }}
                />
              );
            })
          ) : (
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="transparent"
              stroke="rgba(255, 255, 255, 0.1)"
              strokeWidth={strokeWidth}
            />
          )}
        </svg>

        {/* Center Label */}
        <div style={{ position: "absolute", textAlign: "center", pointerEvents: "none" }}>
          <div style={{ fontSize: "24px", fontWeight: 800, color: "var(--text)", lineHeight: 1 }}>
            {total}
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "3px", textTransform: "uppercase", fontWeight: 600 }}>
            {total === 1 ? "Student" : "Students"}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px", minWidth: "160px" }}>
        {data.map((d) => {
          const val = Number(d.value) || 0;
          const pct = total > 0 ? Math.round((val / total) * 100) : 0;
          return (
            <div
              key={d.label}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "6px 10px",
                borderRadius: "8px",
                background: "var(--surface-soft)",
                border: "1px solid var(--border)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ width: "10px", height: "10px", borderRadius: "50%", background: d.color, display: "inline-block" }} />
                <span style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 500 }}>{d.label}</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <strong style={{ fontSize: "13px", color: "var(--text)" }}>{val}</strong>
                <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>({pct}%)</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// data: [{ week, attendance, engagement }]
export function EngagementChart({ data, maxValue = 100 }) {
  if (!data || data.length === 0) {
    return (
      <div style={{ padding: "30px 20px", textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>
        No weekly engagement timeline data available yet.
      </div>
    );
  }

  return (
    <div style={{ padding: "16px 8px" }}>
      {/* Legend */}
      <div style={{ display: "flex", justifyContent: "flex-end", gap: "16px", marginBottom: "16px", fontSize: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "2px", background: "var(--primary)" }} />
          <span style={{ color: "var(--text-secondary)" }}>Attendance Rate</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "2px", background: "#3b82f6" }} />
          <span style={{ color: "var(--text-secondary)" }}>LMS Activity</span>
        </div>
      </div>

      {/* Bar Chart Container */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", height: "140px", borderBottom: "1px solid var(--border)", paddingBottom: "8px", gap: "12px" }}>
        {data.map((w) => {
          const attHeight = Math.min(Math.max((Number(w.attendance) || 0) / maxValue * 100, 4), 100);
          const engHeight = Math.min(Math.max((Number(w.engagement) || 0) / maxValue * 100, 4), 100);

          return (
            <div key={w.week} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", height: "100%", justifyContent: "flex-end", gap: "6px" }}>
              <div style={{ display: "flex", alignItems: "flex-end", gap: "4px", height: "110px", width: "100%", justifyContent: "center" }}>
                {/* Attendance Bar */}
                <div
                  title={`Attendance: ${w.attendance}%`}
                  style={{
                    width: "16px",
                    height: `${attHeight}%`,
                    background: "var(--primary)",
                    borderRadius: "4px 4px 0 0",
                    transition: "height 0.4s ease",
                  }}
                />
                {/* Engagement Bar */}
                <div
                  title={`LMS Engagement: ${w.engagement}%`}
                  style={{
                    width: "16px",
                    height: `${engHeight}%`,
                    background: "#3b82f6",
                    borderRadius: "4px 4px 0 0",
                    transition: "height 0.4s ease",
                  }}
                />
              </div>
              <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 600 }}>{w.week}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function EmptyState({ icon, title, message }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px 20px",
        textAlign: "center",
        background: "var(--surface-soft)",
        borderRadius: "12px",
        border: "1px dashed var(--border)",
        margin: "12px 0",
      }}
    >
      <div style={{ color: "var(--primary)", marginBottom: "12px", opacity: 0.85 }}>{icon}</div>
      <strong style={{ fontSize: "14px", color: "var(--text)", marginBottom: "4px" }}>{title}</strong>
      <span style={{ fontSize: "12px", color: "var(--text-muted)", maxWidth: "340px", lineHeight: 1.5 }}>
        {message}
      </span>
    </div>
  );
}

