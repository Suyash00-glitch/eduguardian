import React, { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Users, UserCheck, FolderPlus, MessageSquare,
  FileDown, ClipboardCheck, ClipboardList, GraduationCap, LogOut,
  ChevronDown, ShieldCheck, HeartHandshake,
} from "lucide-react";
import { useTeacher, contextKey, contextLabel } from "../../context/TeacherContext";

const ADMIN_NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/roster", label: "Student Roster", icon: Users },
  { to: "/mentors", label: "Mentor Assignment", icon: UserCheck },
  { to: "/interventions", label: "Interventions", icon: FolderPlus },
  { to: "/feedback", label: "Student Feedback", icon: MessageSquare },
  { to: "/reports", label: "Reports & Download", icon: FileDown },
];

const SUBJECT_NAV = [
  { to: "/", label: "Attendance", icon: ClipboardCheck, end: true },
  { to: "/assignments", label: "Assignments", icon: ClipboardList },
  { to: "/marks", label: "Marks & Quizzes", icon: GraduationCap },
];

export default function AdminLayout() {
  const { assignments, active, switchContext, loading } = useTeacher();
  const [switcherOpen, setSwitcherOpen] = useState(false);
  const navigate = useNavigate();

  if (loading || !active) {
    return <div className="app-loading"><div className="loading-spinner" />Loading your classes...</div>;
  }

  const nav = active.is_class_admin ? ADMIN_NAV : SUBJECT_NAV;

  function handleLogout() {
    localStorage.removeItem("token");
    navigate("/login");
  }

  return (
    <div className="student-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon"><ShieldCheck size={18} /></div>
          <div>
            <div className="brand-name">EduGuardian AI</div>
            <div className="brand-version">TEACHER PORTAL</div>
          </div>
        </div>

        <nav className="sidebar-navigation">
          <div className="navigation-section">
            <span className="navigation-label">
              {active.is_class_admin ? "CLASS ADMIN" : "SUBJECT TEACHING"}
            </span>
            {nav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => `sidebar-item${isActive ? " active" : ""}`}
              >
                <item.icon size={16} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>

          {/* Always visible — mentorship isn't tied to a class/subject context */}
          <div className="navigation-section">
            <span className="navigation-label">MENTORSHIP</span>
            <NavLink
              to="/mentees"
              className={({ isActive }) => `sidebar-item${isActive ? " active" : ""}`}
            >
              <HeartHandshake size={16} />
              <span>My Mentees</span>
            </NavLink>
          </div>
        </nav>

        <div className="sidebar-bottom">
          <button className="logout-button" onClick={handleLogout}>
            <LogOut size={15} />
            <span>Log out</span>
          </button>
        </div>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <div className="topbar-page">
            <h1>{active.is_class_admin ? `Class Admin — Section ${active.section}` : active.subject_name}</h1>
            <span>{active.department} · Semester {active.semester} · Section {active.section}</span>
          </div>

          <div className="topbar-actions">
            <div className="context-switcher">
              <button className="context-switcher-button" onClick={() => setSwitcherOpen((v) => !v)}>
                <span className="context-switcher-label">Teaching as</span>
                <strong>{contextLabel(active)}</strong>
                <ChevronDown size={14} />
              </button>

              {switcherOpen && (
                <div className="context-switcher-menu">
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
                      <span>{contextLabel(a)}</span>
                      {a.is_class_admin && <span className="admin-pill">Admin</span>}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <button className="topbar-profile">
              <div className="topbar-avatar">AD</div>
              <div className="topbar-user">
                <strong>Admin User</strong>
                <span>Teacher Role</span>
              </div>
            </button>
          </div>
        </header>

        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
