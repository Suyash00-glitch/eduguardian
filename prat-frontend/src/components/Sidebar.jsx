import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  TrendingUp,
  ClipboardList,
  Lightbulb,
  ClipboardCheck,
  MessageCircle,
  Target,
  BookOpen,
  User,
  Settings,
  LogOut,
  GraduationCap,
  LifeBuoy,
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
    path: "/assignments",
    label: "Assignments",
    icon: ClipboardList,
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
  {
    path: "/support",
    label: "Help & Support",
    icon: LifeBuoy,
  },
];

const accountItems = [
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
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const activePage = location.pathname.split("/")[1] || "dashboard";

  const isActive = (path) => {
    return location.pathname === path;
  };

  const handleLogout = () => {
    setShowLogoutConfirm(false);
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

          <div className="brand-version">Student Portal</div>
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

        <button
          className="logout-button"
          onClick={() => setShowLogoutConfirm(true)}
          style={{ color: "var(--danger)", display: "flex", alignItems: "center", gap: "10px", fontWeight: 600 }}
        >
          <LogOut size={17} color="var(--danger)" />
          <span>Sign out</span>
        </button>
      </div>

      {/* IN-APP CONFIRMATION MODAL */}
      {showLogoutConfirm && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.7)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999,
            padding: "20px",
          }}
          onClick={() => setShowLogoutConfirm(false)}
        >
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "16px",
              width: "100%",
              maxWidth: "420px",
              boxShadow: "0 24px 60px rgba(0, 0, 0, 0.5)",
              overflow: "hidden",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                padding: "18px 22px",
                borderBottom: "1px solid var(--border)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <LogOut size={18} color="var(--danger)" />
                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "var(--text)" }}>
                  Confirm Sign Out
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowLogoutConfirm(false)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                  padding: "4px",
                }}
              >
                ✕
              </button>
            </div>

            <div style={{ padding: "20px 22px" }}>
              <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "14px", lineHeight: 1.5 }}>
                Are you sure you want to sign out of the EduGuardian Student Portal?
              </p>
            </div>

            <div
              style={{
                padding: "14px 22px",
                borderTop: "1px solid var(--border)",
                display: "flex",
                justifyContent: "flex-end",
                gap: "10px",
                background: "var(--surface-soft)",
              }}
            >
              <button
                type="button"
                onClick={() => setShowLogoutConfirm(false)}
                style={{
                  padding: "8px 16px",
                  borderRadius: "8px",
                  border: "1px solid var(--border)",
                  background: "var(--surface)",
                  color: "var(--text)",
                  fontSize: "13px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleLogout}
                style={{
                  padding: "8px 16px",
                  borderRadius: "8px",
                  border: "none",
                  background: "var(--danger)",
                  color: "#ffffff",
                  fontSize: "13px",
                  fontWeight: 700,
                  cursor: "pointer",
                  boxShadow: "0 4px 14px rgba(239, 68, 68, 0.3)",
                }}
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}

export default Sidebar;
