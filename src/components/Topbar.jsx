import React from "react";
import { Search, Bell, Sparkles } from "lucide-react";

const pageInfo = {
  dashboard: {
    title: "Dashboard",
    subtitle: "Your academic overview",
  },

  progress: {
    title: "My Progress",
    subtitle: "Track your academic journey",
  },

  insights: {
    title: "My Insights",
    subtitle: "Understand your academic patterns",
  },

  recovery: {
    title: "Recovery Plan",
    subtitle: "Your personalized path forward",
  },

  coach: {
    title: "AI Coach",
    subtitle: "Your academic support assistant",
  },

  goals: {
    title: "Goals",
    subtitle: "Set and track your targets",
  },

  resources: {
    title: "Resources",
    subtitle: "Support available to you",
  },

  notifications: {
    title: "Notifications",
    subtitle: "Your latest updates",
  },

  profile: {
    title: "Profile",
    subtitle: "Your student information",
  },

  settings: {
    title: "Settings",
    subtitle: "Manage your preferences",
  },
};

function Topbar({ activePage, setActivePage }) {
  const current = pageInfo[activePage] || pageInfo.dashboard;

  return (
    <header className="topbar">
      <div className="page-heading">
        <h1>{current.title}</h1>

        <p>{current.subtitle}</p>
      </div>

      <div className="topbar-actions">
        <button className="search-button">
          <Search size={17} />

          <span>Search</span>

          <kbd>Ctrl K</kbd>
        </button>

        <button
          className="icon-button"
          onClick={() => setActivePage("notifications")}
        >
          <Bell size={18} />

          <span className="notification-dot" />
        </button>

        <button className="coach-button" onClick={() => setActivePage("coach")}>
          <Sparkles size={16} />

          <span>AI Coach</span>
        </button>

        <button className="profile-button">
          <div className="topbar-avatar">P</div>

          <div className="topbar-user">
            <strong>Pratham</strong>
            <span>Student</span>
          </div>
        </button>
      </div>
    </header>
  );
}

export default Topbar;
