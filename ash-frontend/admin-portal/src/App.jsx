import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./styles/teacher-portal.css";
import {
  TeacherContextProvider,
  useTeacher,
} from "./context/TeacherContext";
import { ThemeProvider } from "./context/ThemeContext";
import { isLoggedIn } from "./services/auth";

import AdminLayout from "./components/layout/AdminLayout";
import Login from "./pages/Login";
import MyMentees from "./pages/mentor/MyMentees";

// Admin pages
import Dashboard from "./pages/admin/Dashboard";
import StudentRoster from "./pages/admin/StudentRoster";
import MentorAssignment from "./pages/admin/MentorAssignment";
import MentorManagement from "./pages/admin/MentorManagement";
import Interventions from "./pages/admin/Interventions";
import Feedback from "./pages/admin/Feedback";
import Reports from "./pages/admin/Reports";

// Subject-teacher pages
import SubjectAssignments from "./pages/subject/SubjectAssignments";
import SubjectMarks from "./pages/subject/SubjectMarks";
import SubjectAssignmentDetails from "./pages/subject/SubjectAssignmentDetails";

function RequireAuth({ children }) {
  if (!isLoggedIn()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function ContextRouter() {
  const { active, loading } = useTeacher();

  if (loading) {
    return null;
  }

  if (!active) {
    return null;
  }

  return (
    <Routes>
      <Route element={<AdminLayout />}>
        {/* Dynamic Index based on active role */}
        <Route index element={active.is_class_admin ? <Dashboard /> : <SubjectAssignments />} />

        {/* Advisor & Cohort routes */}
        <Route path="roster" element={<StudentRoster />} />
        <Route path="mentors" element={<MentorAssignment />} />
        <Route path="mentor-management" element={<MentorManagement />} />
        <Route path="interventions" element={<Interventions />} />
        <Route path="feedback" element={<Feedback />} />
        <Route path="reports" element={<Reports />} />

        {/* Subject teacher routes */}
        <Route path="assignments" element={<SubjectAssignments />} />
        <Route path="assignments/:assignmentId" element={<SubjectAssignmentDetails />} />
        <Route path="marks" element={<SubjectMarks />} />

        {/* Mentorship route */}
        <Route path="mentees" element={<MyMentees />} />

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          {/* LOGIN DOES NOT USE TEACHER CONTEXT */}
          <Route path="/login" element={<Login />} />

          {/* AUTHENTICATED TEACHER PORTAL */}
          <Route
            path="/*"
            element={
              <RequireAuth>
                <TeacherContextProvider>
                  <ContextRouter />
                </TeacherContextProvider>
              </RequireAuth>
            }
          />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}