import React from "react";
import { Palette, Lock, ChevronRight, Check, Moon, Sun } from "lucide-react";

import { useTheme } from "../context/ThemeContext";

function Settings() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="settings-page">
      {/* HEADER */}

      <div className="settings-header">
        <div>
          <h2>Account Settings</h2>
          <p>Control your EduGuardian theme and preferences.</p>
        </div>
      </div>

      {/* APPEARANCE */}

      <section className="settings-section">
        <div className="settings-section-header">
          <div className="settings-section-icon">
            <Palette size={17} />
          </div>

          <div>
            <h3>Appearance</h3>
            <p>Choose how EduGuardian looks.</p>
          </div>
        </div>

        <div className="theme-options">
          {/* DARK */}

          <button
            type="button"
            className={`theme-option ${theme === "dark" ? "active" : ""}`}
            onClick={() => setTheme("dark")}
          >
            <div className="theme-option-icon">
              <Moon size={17} />
            </div>

            <div className="theme-option-content">
              <strong>Dark</strong>
              <span>The default EduGuardian interface.</span>
            </div>

            {theme === "dark" && (
              <div className="appearance-check">
                <Check size={13} />
              </div>
            )}
          </button>

          {/* LIGHT */}

          <button
            type="button"
            className={`theme-option ${theme === "light" ? "active" : ""}`}
            onClick={() => setTheme("light")}
          >
            <div className="theme-option-icon">
              <Sun size={17} />
            </div>

            <div className="theme-option-content">
              <strong>Light</strong>
              <span>A brighter interface for daytime use.</span>
            </div>

            {theme === "light" && (
              <div className="appearance-check">
                <Check size={13} />
              </div>
            )}
          </button>
        </div>
      </section>

      {/* SECURITY */}

      <section className="settings-section">
        <div className="settings-section-header">
          <div className="settings-section-icon">
            <Lock size={17} />
          </div>

          <div>
            <h3>Security</h3>
            <p>Manage your account security.</p>
          </div>
        </div>

        <button type="button" className="settings-action-button">
          <span>Change password</span>

          <ChevronRight size={16} />
        </button>
      </section>
    </div>
  );
}

export default Settings;
