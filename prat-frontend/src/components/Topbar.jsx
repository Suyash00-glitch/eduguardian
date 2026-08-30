import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Bell, ChevronDown, Sun, Moon } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

const pageTitles = {
  "/dashboard": {
    title: "Dashboard",
    subtitle: "Your academic overview",
  },
  "/progress": {
    title: "My Progress",
    subtitle: "Track your academic performance",
  },
  "/insights": {
    title: "My Insights",
    subtitle: "Understand your academic signals",
  },
  "/recovery": {
    title: "Recovery Plan",
    subtitle: "Your personalized academic action plan",
  },
  "/coach": {
    title: "AI Coach",
    subtitle: "Personalized academic guidance",
  },
  "/goals": {
    title: "Goals",
    subtitle: "Track your academic goals",
  },
  "/resources": {
    title: "Resources",
    subtitle: "Academic and campus support",
  },
  "/notifications": {
    title: "Notifications",
    subtitle: "Your latest updates",
  },
  "/profile": {
    title: "Profile",
    subtitle: "Your student information",
  },
  "/settings": {
    title: "Settings",
    subtitle: "Manage your preferences",
  },
};

function Topbar() {
  const location = useLocation();
  const navigate = useNavigate();

  const { user } = useAuth();
  const { theme, toggleTheme, isDark } = useTheme();

  const currentPage = pageTitles[location.pathname] || pageTitles["/dashboard"];

  return (
    <header className="topbar">
      {/* Page information */}
      <div className="topbar-page">
        <h1>{currentPage.title}</h1>
        <span>{currentPage.subtitle}</span>
      </div>

      {/* Actions */}
      <div className="topbar-actions">
        {/* Theme Toggle */}
        <button
          className="topbar-icon-button"
          aria-label={isDark ? "Switch to Light Theme" : "Switch to Dark Theme"}
          title={isDark ? "Switch to Light Theme" : "Switch to Dark Theme"}
          onClick={toggleTheme}
          style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
        >
          {isDark ? <Sun size={17} /> : <Moon size={17} />}
        </button>

        {/* Notifications */}
        <button
          className="topbar-icon-button notification-button"
          aria-label="Notifications"
          onClick={() => navigate("/notifications")}
        >
          <Bell size={17} />
          <span className="topbar-notification-dot" />
        </button>

        {/* Profile */}
        <button className="topbar-profile" onClick={() => navigate("/profile")}>
          <div className="topbar-avatar">
            {user?.full_name?.charAt(0) || "P"}
          </div>

          <div className="topbar-user">
            <strong>{user?.full_name || "Student"}</strong>
            <span>{user?.usn || "Student"}</span>
          </div>

          <ChevronDown size={14} />
        </button>
      </div>
    </header>
  );
}

export default Topbar;
