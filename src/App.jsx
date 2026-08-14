import React, { useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import Topbar from "./components/Topbar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Progress from "./pages/Progress.jsx";

function App() {
  const [activePage, setActivePage] = useState("dashboard");

  const renderPage = () => {
    switch (activePage) {
      case "dashboard":
        return <Dashboard />;

      case "progress":
        return <Progress />;

      default:
        return (
          <div className="placeholder-page">
            <div className="placeholder-icon">✦</div>

            <h2>{getPageName(activePage)}</h2>

            <p>This section will be built next.</p>
          </div>
        );
    }
  };

  return (
    <div className="app-shell">
      <Sidebar activePage={activePage} setActivePage={setActivePage} />

      <div className="main-area">
        <Topbar activePage={activePage} setActivePage={setActivePage} />

        <main className="page-content">{renderPage()}</main>
      </div>
    </div>
  );
}

function getPageName(page) {
  const names = {
    dashboard: "Dashboard",
    progress: "My Progress",
    insights: "My Insights",
    recovery: "Recovery Plan",
    coach: "AI Coach",
    goals: "Goals",
    resources: "Resources",
    notifications: "Notifications",
    profile: "Profile",
    settings: "Settings",
  };

  return names[page] || "Dashboard";
}

export default App;
