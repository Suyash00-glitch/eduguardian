import React from "react";

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider, useAuth } from "./context/AuthContext";

/* Pages */

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Progress from "./pages/Progress";
import Assignments from "./pages/Assignments";
import AssignmentDetails from "./pages/AssignmentDetails";
import Insights from "./pages/Insights";
import Recovery from "./pages/Recovery";
import Coach from "./pages/Coach";
import Goals from "./pages/Goals";
import Resources from "./pages/Resources";

import Profile from "./pages/Profile";
import Settings from "./pages/Settings";

/* Layout / Protection */

import ProtectedRoute from "./components/ProtectedRoute";
import StudentLayout from "./components/StudentLayout";

/* =====================================================
   ROUTES
   ===================================================== */

function AppRoutes() {
  const { isAuthenticated, loading } = useAuth();

  /* ---------------------------------------------
     AUTH INITIALIZATION
     --------------------------------------------- */

  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner" />

        <span>Loading EduGuardian...</span>
      </div>
    );
  }

  return (
    <Routes>
      {/* =================================================
          PUBLIC
          ================================================= */}

      <Route
        path="/login"
        element={
          isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />
        }
      />

      {/* =================================================
          PROTECTED
          ================================================= */}

      <Route element={<ProtectedRoute />}>
        <Route element={<StudentLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />

          <Route path="/progress" element={<Progress />} />

          <Route path="/assignments" element={<Assignments />} />

          <Route
            path="/assignments/:assignmentId"
            element={<AssignmentDetails />}
          />

          <Route path="/insights" element={<Insights />} />

          <Route path="/recovery" element={<Recovery />} />

          <Route path="/coach" element={<Coach />} />

          <Route path="/goals" element={<Goals />} />

          <Route path="/resources" element={<Resources />} />

          <Route path="/profile" element={<Profile />} />

          <Route path="/settings" element={<Settings />} />
        </Route>
      </Route>

      {/* =================================================
          ROOT
          ================================================= */}

      <Route
        path="/"
        element={
          <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />
        }
      />

      {/* =================================================
          UNKNOWN ROUTE
          ================================================= */}

      <Route
        path="*"
        element={
          <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />
        }
      />
    </Routes>
  );
}

/* =====================================================
   APP
   ===================================================== */

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
