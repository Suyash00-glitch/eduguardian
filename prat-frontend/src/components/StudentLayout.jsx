import React from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

function StudentLayout() {
  const location = useLocation();
  const isCoach = location.pathname === "/coach";

  return (
    <div className="student-layout">
      <Sidebar />

      <div
        className="student-main"
        style={isCoach ? { paddingTop: 0, height: "100vh", overflow: "hidden" } : undefined}
      >
        {!isCoach && <Topbar />}

        <main
          className="student-content"
          style={
            isCoach
              ? {
                  padding: "10px 14px 0 14px",
                  height: "100vh",
                  maxHeight: "100vh",
                  overflow: "hidden",
                }
              : undefined
          }
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default StudentLayout;
