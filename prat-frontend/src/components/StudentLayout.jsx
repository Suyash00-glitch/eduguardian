import React from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

function StudentLayout() {
  return (
    <div className="student-layout">
      <Sidebar />

      <div className="student-main">
        <Topbar />

        <main className="student-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default StudentLayout;
