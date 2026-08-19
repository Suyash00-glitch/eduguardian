import React, { createContext, useContext, useEffect, useState } from "react";

// TODO backend: replace with GET /api/teacher/assignments (Authorization: Bearer token)
// Expected shape per row: { department, semester, section, subject_code, subject_name, is_class_admin }
const MOCK_ASSIGNMENTS = [
  {
    department: "ISE",
    semester: 5,
    section: "C",
    subject_code: "CS501",
    subject_name: "Data Structures",
    is_class_admin: false,
  },
  {
    department: "ISE",
    semester: 5,
    section: "D",
    subject_code: "CS502",
    subject_name: "Operating Systems",
    is_class_admin: false,
  },
  {
    department: "ISE",
    semester: 5,
    section: "E",
    subject_code: null,
    subject_name: null,
    is_class_admin: true,
  },
];

const TeacherContext = createContext(null);

export function contextKey(a) {
  return `${a.department}-${a.semester}-${a.section}-${a.subject_code || "ADMIN"}`;
}

export function contextLabel(a) {
  if (a.is_class_admin) return `${a.section} - Class Admin`;
  return `${a.section} - ${a.subject_name || a.subject_code}`;
}

export function TeacherContextProvider({ children }) {
  const [assignments, setAssignments] = useState([]);
  const [active, setActive] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
  async function load() {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://127.0.0.1:8000/api/teacher/assignments", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        throw new Error(`teacher assignments request failed: ${res.status}`);
      }

      const data = await res.json();
      setAssignments(data.assignments || []);
      setActive(data.assignments?.[0] || null);
    } catch (err) {
      console.error("failed to load teacher assignments:", err);
      setAssignments([]);
      setActive(null);
    } finally {
      setLoading(false);
    }
  }
  load();
}, []);

  function switchContext(key) {
    const match = assignments.find((a) => contextKey(a) === key);
    if (match) setActive(match);
  }

  return (
    <TeacherContext.Provider
      value={{ assignments, active, switchContext, loading }}
    >
      {children}
    </TeacherContext.Provider>
  );
}

export function useTeacher() {
  const ctx = useContext(TeacherContext);
  if (!ctx) throw new Error("useTeacher must be used inside TeacherContextProvider");
  return ctx;
}
