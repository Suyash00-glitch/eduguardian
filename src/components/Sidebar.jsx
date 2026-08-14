import React from "react";
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

const mainItems = [
  {
    id: "dashboard",
    label: "Dashboard",
    icon: LayoutDashboard,
  },
  {
    id: "progress",
    label: "My Progress",
    icon: TrendingUp,
  },
  {
    id: "insights",
    label: "My Insights",
    icon: Lightbulb,
  },
  {
    id: "recovery",
    label: "Recovery Plan",
    icon: ClipboardCheck,
  },
  {
    id: "coach",
    label: "AI Coach",
    icon: MessageCircle,
  },
  {
    id: "goals",
    label: "Goals",
    icon: Target,
  },
  {
    id: "resources",
    label: "Resources",
    icon: BookOpen,
  },
];

const accountItems = [
  {
    id: "notifications",
    label: "Notifications",
    icon: Bell,
  },
  {
    id: "profile",
    label: "Profile",
    icon: User,
  },
  {
    id: "settings",
    label: "Settings",
    icon: Settings,
  },
];

function Sidebar({ activePage, setActivePage }) {
  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="brand-icon">
          <GraduationCap size={20} />
        </div>

        <div>
          <div className="brand-name">EduGuardian</div>

          <div className="brand-version">AI 2.0</div>
        </div>
      </div>

      {/* Student */}
      <div className="student-card">
        <div className="student-avatar">P</div>

        <div className="student-info">
          <strong>Pratham</strong>
          <span>4NM24IS001</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-navigation">
        <div className="navigation-section">
          <div className="navigation-label">MAIN</div>

          {mainItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;

            return (
              <button
                key={item.id}
                className={`sidebar-item ${isActive ? "active" : ""}`}
                onClick={() => setActivePage(item.id)}
              >
                <Icon size={18} />

                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        <div className="navigation-section account-section">
          <div className="navigation-label">ACCOUNT</div>

          {accountItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;

            return (
              <button
                key={item.id}
                className={`sidebar-item ${isActive ? "active" : ""}`}
                onClick={() => setActivePage(item.id)}
              >
                <Icon size={18} />

                <span>{item.label}</span>

                {item.id === "notifications" && (
                  <span className="notification-count">3</span>
                )}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Bottom */}
      <div className="sidebar-bottom">
        <div className="academic-info">
          <span>Information Science</span>

          <strong>Semester 4 · Section A</strong>
        </div>

        <button className="logout-button">
          <LogOut size={17} />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
