import React, { useState } from "react";
import {
  Bell,
  ShieldCheck,
  Palette,
  Lock,
  ChevronRight,
  Check,
  Moon,
  Sun,
} from "lucide-react";

import { useTheme } from "../context/ThemeContext";

function Settings() {
  const { theme, setTheme } = useTheme();

  const [notifications, setNotifications] = useState(true);
  const [weeklySummary, setWeeklySummary] = useState(true);
  const [coachSuggestions, setCoachSuggestions] = useState(true);

  return (
    <div className="settings-page">
      <div className="settings-header">
        <div>
          <span className="dashboard-eyebrow">ACCOUNT</span>

          <h2>Settings</h2>

          <p>Control your EduGuardian experience.</p>
        </div>
      </div>

      {/* NOTIFICATIONS */}

      <section className="settings-section">
        <div className="settings-section-header">
          <div className="settings-section-icon">
            <Bell size={16} />
          </div>

          <div>
            <h3>Notifications</h3>
            <p>Choose which updates you want to receive.</p>
          </div>
        </div>

        <div className="settings-list">
          <SettingToggle
            title="Academic notifications"
            description="Receive important updates about your academic activity."
            enabled={notifications}
            onChange={setNotifications}
          />

          <SettingToggle
            title="Weekly progress summary"
            description="Receive a summary of your academic progress."
            enabled={weeklySummary}
            onChange={setWeeklySummary}
          />

          <SettingToggle
            title="AI Coach suggestions"
            description="Allow EduGuardian to show helpful coaching suggestions."
            enabled={coachSuggestions}
            onChange={setCoachSuggestions}
          />
        </div>
      </section>

      {/* PRIVACY */}

      <section className="settings-section">
        <div className="settings-section-header">
          <div className="settings-section-icon">
            <ShieldCheck size={16} />
          </div>

          <div>
            <h3>Privacy & AI</h3>
            <p>Understand how EduGuardian uses your information.</p>
          </div>
        </div>

        <div className="settings-action">
          <div>
            <strong>AI explanation preferences</strong>
            <span>Show explanations behind academic support signals.</span>
          </div>

          <ChevronRight size={15} />
        </div>

        <div className="settings-action">
          <div>
            <strong>Data & privacy</strong>
            <span>Review how your academic data is used.</span>
          </div>

          <ChevronRight size={15} />
        </div>
      </section>

      {/* APPEARANCE */}

      <section className="settings-section">
        <div className="settings-section-header">
          <div className="settings-section-icon">
            <Palette size={16} />
          </div>

          <div>
            <h3>Appearance</h3>
            <p>Choose how EduGuardian looks.</p>
          </div>
        </div>

        <div className="theme-options">
          <button
            className={`theme-option ${theme === "dark" ? "active" : ""}`}
            onClick={() => setTheme("dark")}
          >
            <div className="theme-option-icon">
              <Moon size={15} />
            </div>

            <div className="theme-option-content">
              <strong>Dark</strong>
              <span>The default EduGuardian interface.</span>
            </div>

            {theme === "dark" && (
              <div className="appearance-check">
                <Check size={12} />
              </div>
            )}
          </button>

          <button
            className={`theme-option ${theme === "light" ? "active" : ""}`}
            onClick={() => setTheme("light")}
          >
            <div className="theme-option-icon">
              <Sun size={15} />
            </div>

            <div className="theme-option-content">
              <strong>Light</strong>
              <span>A brighter interface for daytime use.</span>
            </div>

            {theme === "light" && (
              <div className="appearance-check">
                <Check size={12} />
              </div>
            )}
          </button>
        </div>
      </section>

      {/* SECURITY */}

      <section className="settings-section">
        <div className="settings-section-header">
          <div className="settings-section-icon">
            <Lock size={16} />
          </div>

          <div>
            <h3>Security</h3>
            <p>Manage your account security.</p>
          </div>
        </div>

        <button className="settings-action-button">
          Change password
          <ChevronRight size={15} />
        </button>
      </section>
    </div>
  );
}

function SettingToggle({ title, description, enabled, onChange }) {
  return (
    <div className="setting-toggle-row">
      <div>
        <strong>{title}</strong>
        <span>{description}</span>
      </div>

      <button
        className={`toggle ${enabled ? "enabled" : ""}`}
        onClick={() => onChange(!enabled)}
        aria-label={title}
      >
        <span />
      </button>
    </div>
  );
}

export default Settings;
