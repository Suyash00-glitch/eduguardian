import React, { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  UserPlus,
  ClipboardList,
  MessageSquare,
  FileSpreadsheet,
  LogOut,
  GraduationCap,
  Bell,
  Sun,
  Moon,
  ChevronDown,
  BookOpen,
  HeartHandshake,
  AlertCircle,
  X,
} from "lucide-react";
import { useTeacher, contextKey, contextLabel, getInitials } from "../../context/TeacherContext";
import { useTheme } from "../../context/ThemeContext";

const ADMIN_NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/roster", label: "Student Roster", icon: Users },
  { to: "/mentors", label: "Mentor Assignment", icon: UserPlus },
  { to: "/mentor-management", label: "Mentor Directory", icon: Users },
  { to: "/interventions", label: "Action Plans", icon: ClipboardList },
  { to: "/feedback", label: "Student Support", icon: MessageSquare },
  { to: "/reports", label: "Cohort Reports", icon: FileSpreadsheet },
];

const SUBJECT_NAV = [
  { to: "/", label: "Assignments & Submissions", icon: ClipboardList, end: true },
  { to: "/marks", label: "Continuous Evaluation Marks", icon: FileSpreadsheet },
];

const pageTitles = {
  "/": {
    adminTitle: "Dashboard",
    adminSubtitle: "Your academic cohort overview",
    subjectTitle: "Course Instruction & Evaluation",
    subjectSubtitle: "Subject assignments, roster, and continuous evaluation marks",
  },
  "/roster": {
    title: "Cohort Roster & Intelligence",
    subtitle: "Student-level performance signals and risk evaluations",
  },
  "/mentors": {
    title: "Mentor Caseload & Allocation",
    subtitle: "Smart mentor matching and student distribution",
  },
  "/mentor-management": {
    title: "Faculty Mentor Directory",
    subtitle: "Active mentor capacity, workloads, and department tracking",
  },
  "/interventions": {
    title: "Academic Recovery Plans",
    subtitle: "Targeted support plans and study trackers for students",
  },
  "/feedback": {
    title: "Student Support & Feedback",
    subtitle: "Direct student counseling notes and feedback logs",
  },
  "/reports": {
    title: "Cohort Reports",
    subtitle: "Comprehensive semester progress and risk distribution reports",
  },
  "/marks": {
    title: "Internal Marks & Quizzes",
    subtitle: "Subject-level continuous evaluation and quiz scores",
  },
  "/mentees": {
    title: "My Mentees",
    subtitle: "Personal student mentorship caseload and progress",
  },
};

export default function AdminLayout() {
  const { assignments, active, user, switchContext, loading } = useTeacher();
  const { toggleTheme, isDark } = useTheme();
  const [switcherOpen, setSwitcherOpen] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  if (loading || !active) {
    return (
      <div className="app-loading">
        <div className="loading-spinner" />
        <span>Loading faculty portal...</span>
      </div>
    );
  }

  const nav = active.is_class_admin ? ADMIN_NAV : SUBJECT_NAV;
  const facultyName = user?.full_name || (active.is_class_admin ? "Dr. Preethi Salian K" : "Faculty Member");
  const facultyDesignation = active.is_class_admin ? "Class Advisor" : (active.subject_code || "Subject Teacher");
  const initials = getInitials(facultyName);

  const pageInfo = pageTitles[location.pathname] || {
    title: active.is_class_admin ? "Dashboard" : (active.subject_name || active.subject_code),
    subtitle: `${active.department} · Semester ${active.semester} · Section ${active.section}`,
  };

  const currentTitle = location.pathname === "/"
    ? (active.is_class_admin ? pageInfo.adminTitle : pageInfo.subjectTitle)
    : (pageInfo.title || "Dashboard");

  const currentSubtitle = location.pathname === "/"
    ? (active.is_class_admin ? pageInfo.adminSubtitle : pageInfo.subjectSubtitle)
    : (pageInfo.subtitle || `${active.department} · Semester ${active.semester} · Section ${active.section}`);

  function performLogout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("eduguardian_active_teacher_context_key");
    setShowLogoutConfirm(false);
    navigate("/login");
  }

  return (
    <div className="app-shell">
      {/* SIDEBAR */}
      <aside className="sidebar">
        {/* BRAND */}
        <div className="sidebar-brand">
          <div className="brand-icon">
            <GraduationCap size={20} />
          </div>
          <div>
            <div className="brand-name">EduGuardian</div>
            <div className="brand-version">Faculty Portal</div>
          </div>
        </div>

        {/* TEACHER PROFILE MINI-CARD (Identical to Student Portal) */}
        <div className="student-card">
          <div className="student-avatar">
            {initials.charAt(0) || "P"}
          </div>
          <div className="student-info">
            <strong>{facultyName}</strong>
            <span>{active.is_class_admin ? `Class Advisor · ${active.department}` : `${active.subject_code} · ${active.department}`}</span>
          </div>
        </div>

        {/* SIDEBAR NAVIGATION */}
        <nav className="sidebar-navigation">
          <div className="navigation-section">
            <div className="navigation-label">
              {active.is_class_admin ? "MAIN" : "SUBJECT INSTRUCTION"}
            </div>
            {nav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => `sidebar-item${isActive ? " active" : ""}`}
              >
                <item.icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>

          {/* Mentorship Section */}
          <div className="navigation-section account-section">
            <div className="navigation-label">STUDENT MENTORING</div>
            <NavLink
              to="/mentees"
              className={({ isActive }) => `sidebar-item${isActive ? " active" : ""}`}
            >
              <HeartHandshake size={18} />
              <span>My Mentees</span>
            </NavLink>
          </div>
        </nav>

        {/* SIDEBAR BOTTOM WITH ACADEMIC INFO & SINGLE RED LOGOUT */}
        <div className="sidebar-bottom">
          <div className="academic-info">
            <span>{active.department} · NMAMIT</span>
            <strong>
              Semester {active.semester} · Section {active.section}
            </strong>
          </div>

          <button
            type="button"
            className="logout-button"
            onClick={() => setShowLogoutConfirm(true)}
          >
            <LogOut size={16} />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <div className="main-area">
        {/* TOPBAR (Identical to Student Portal) */}
        <header className="topbar">
          <div className="topbar-page">
            <h1>{currentTitle}</h1>
            <span>{currentSubtitle}</span>
          </div>

          <div className="topbar-actions">
            {/* Theme Toggle Button */}
            <button
              className="topbar-icon-button"
              aria-label={isDark ? "Switch to Light Theme" : "Switch to Dark Theme"}
              title={isDark ? "Switch to Light Theme" : "Switch to Dark Theme"}
              onClick={toggleTheme}
            >
              {isDark ? <Sun size={17} /> : <Moon size={17} />}
            </button>

            {/* Notification Bell */}
            <button
              className="topbar-icon-button notification-button"
              aria-label="Notifications"
              title="Notifications"
            >
              <Bell size={17} />
              <span className="topbar-notification-dot" />
            </button>

            {/* Profile Dropdown / Active Role Switcher */}
            <div style={{ position: "relative" }}>
              <button
                className="topbar-profile"
                onClick={() => setSwitcherOpen((v) => !v)}
                title="Switch active teaching / advisor role"
              >
                <div className="topbar-avatar">{initials.charAt(0) || "P"}</div>
                <div className="topbar-user">
                  <strong>{facultyName}</strong>
                  <span>{active.is_class_admin ? "Class Advisor" : (active.subject_code || "Subject Teacher")}</span>
                </div>
                <ChevronDown size={14} />
              </button>

              {switcherOpen && (
                <div className="context-switcher-menu" style={{ right: 0, top: "calc(100% + 8px)" }}>
                  <div style={{ padding: "6px 12px", fontSize: "10px", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                    Select Teaching Role
                  </div>
                  {assignments.map((a) => (
                    <button
                      key={contextKey(a)}
                      className={`context-switcher-item${contextKey(a) === contextKey(active) ? " active" : ""}`}
                      onClick={() => {
                        switchContext(contextKey(a));
                        setSwitcherOpen(false);
                        navigate("/");
                      }}
                    >
                      <div style={{ display: "flex", flexDirection: "column" }}>
                        <span style={{ fontWeight: 600 }}>{contextLabel(a)}</span>
                        <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                          {a.is_class_admin ? "Full Cohort Management" : (a.subject_name || a.subject_code)}
                        </span>
                      </div>
                      {a.is_class_admin && <span className="admin-pill">Admin</span>}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </header>

        {/* MAIN PAGE OUTLET */}
        <main className="page-content">
          <Outlet />
        </main>
      </div>

      {/* CUSTOM IN-APP SIGN OUT CONFIRMATION MODAL */}
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
                  fontSize: "14px",
                }}
              >
                ✕
              </button>
            </div>

            <div style={{ padding: "20px 22px" }}>
              <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "14px", lineHeight: 1.5 }}>
                Are you sure you want to sign out of the EduGuardian Faculty Portal?
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
                onClick={performLogout}
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
    </div>
  );
}
