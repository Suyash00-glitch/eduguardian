import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  TrendingUp,
  Lightbulb,
  ClipboardCheck,
  MessageCircle,
  Target,
  BookOpen,
  Bell,
  User,
  Settings,
  LogOut,
  GraduationCap,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";

const mainItems = [
  {
    path: "/dashboard",
    label: "Dashboard",
    icon: LayoutDashboard,
  },
  {
    path: "/progress",
    label: "My Progress",
    icon: TrendingUp,
  },
  {
    path: "/insights",
    label: "My Insights",
    icon: Lightbulb,
  },
  {
    path: "/recovery",
    label: "Recovery Plan",
    icon: ClipboardCheck,
  },
  {
    path: "/coach",
    label: "AI Coach",
    icon: MessageCircle,
  },
  {
    path: "/goals",
    label: "Goals",
    icon: Target,
  },
  {
    path: "/resources",
    label: "Resources",
    icon: BookOpen,
  },
];

const accountItems = [
  {
    path: "/notifications",
    label: "Notifications",
    icon: Bell,
    badge: 3,
  },
  {
    path: "/profile",
    label: "Profile",
    icon: User,
  },
  {
    path: "/settings",
    label: "Settings",
    icon: Settings,
  },
];

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const { user, logout } = useAuth();

  const activePage = location.pathname.split("/")[1] || "dashboard";

  const isActive = (path) => {
    return location.pathname === path;
  };

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <aside className="sidebar">
      {/* BRAND */}

      <div className="sidebar-brand">
        <div className="brand-icon">
          <GraduationCap size={20} />
        </div>

        <div>
          <div className="brand-name">EduGuardian</div>

          <div className="brand-version">AI 2.0</div>
        </div>
      </div>

      {/* STUDENT */}

      <div
        className="student-card"
        onClick={() => navigate("/profile")}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            navigate("/profile");
          }
        }}
      >
        <div className="student-avatar">
          {user?.full_name?.charAt(0) || "P"}
        </div>

        <div className="student-info">
          <strong>{user?.full_name || "Student"}</strong>

          <span>{user?.usn || "Student ID"}</span>
        </div>
      </div>

      {/* NAVIGATION */}

      <nav className="sidebar-navigation">
        {/* MAIN */}

        <div className="navigation-section">
          <div className="navigation-label">MAIN</div>

          {mainItems.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.path}
                className={`sidebar-item ${
                  isActive(item.path) ? "active" : ""
                }`}
                onClick={() => navigate(item.path)}
              >
                <Icon size={18} />

                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* ACCOUNT */}

        <div className="navigation-section account-section">
          <div className="navigation-label">ACCOUNT</div>

          {accountItems.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.path}
                className={`sidebar-item ${
                  isActive(item.path) ? "active" : ""
                }`}
                onClick={() => navigate(item.path)}
              >
                <Icon size={18} />

                <span>{item.label}</span>

                {item.badge && (
                  <span className="notification-count">{item.badge}</span>
                )}
              </button>
            );
          })}
        </div>
      </nav>

      {/* BOTTOM */}

      <div className="sidebar-bottom">
        <div className="academic-info">
          <span>{user?.department || "Information Science"}</span>

          <strong>
            Semester {user?.semester || 4}
            {" · "}
            {user?.section || "A"}
          </strong>
        </div>

        <button className="logout-button" onClick={handleLogout}>
          <LogOut size={17} />

          <span>Sign out</span>
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
