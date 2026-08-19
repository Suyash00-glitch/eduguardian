import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./styles/teacher-portal.css";
import {
  TeacherContextProvider,
  useTeacher,
} from "./context/TeacherContext";
import { isLoggedIn } from "./services/auth";

import AdminLayout from "./components/layout/AdminLayout";
import Login from "./pages/Login";
// add near your other page imports
import MyMentees from "./pages/mentor/MyMentees";
// Admin pages
import Dashboard from "./pages/admin/Dashboard";
import StudentRoster from "./pages/admin/StudentRoster";
import MentorAssignment from "./pages/admin/MentorAssignment";
import Interventions from "./pages/admin/Interventions";
import Feedback from "./pages/admin/Feedback";
import Reports from "./pages/admin/Reports";

// Subject-teacher pages
import SubjectAttendance from "./pages/subject/SubjectAttendance";
import SubjectAssignments from "./pages/subject/SubjectAssignments";
import SubjectMarks from "./pages/subject/SubjectMarks";
import SubjectAssignmentDetails from "./pages/subject/SubjectAssignmentDetails";

function RequireAuth({ children }) {
  if (!isLoggedIn()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function findSameSectionSubject(assignments, active) {
  if (!active) return null;
  return assignments.find(
    (a) =>
      !a.is_class_admin &&
      a.department === active.department &&
      a.semester === active.semester &&
      a.section === active.section
  );
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
        <Route path="mentees" element={<MyMentees />} />

        {active.is_class_admin ? (
          <>
            <Route index element={<Dashboard />} />
            <Route path="roster" element={<StudentRoster />} />
            <Route path="mentors" element={<MentorAssignment />} />
            <Route path="interventions" element={<Interventions />} />
            <Route path="feedback" element={<Feedback />} />
            <Route path="reports" element={<Reports />} />
          </>
        ) : (
          <>
            <Route index element={<SubjectAttendance />} />
            <Route path="assignments" element={<SubjectAssignments />} />
            <Route path="assignments/:assignmentId" element={<SubjectAssignmentDetails />}/>
            <Route path="marks" element={<SubjectMarks />} />
          </>
        )}

        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
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
  );
}