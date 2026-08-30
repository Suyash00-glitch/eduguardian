import React, { createContext, useContext, useEffect, useState, useCallback } from "react";

const TeacherContext = createContext(null);

export function contextKey(a) {
  if (!a) return "DEFAULT";
  return `${a.department}-${a.semester}-${a.section}-${a.subject_code || "ADMIN"}`;
}

export function contextLabel(a) {
  if (!a) return "Select Class";
  if (a.is_class_admin) return `${a.department} Sem ${a.semester} (${a.section}) · Class Advisor`;
  return `${a.department} Sem ${a.semester} (${a.section}) · ${a.subject_code}`;
}

export function getInitials(name) {
  if (!name) return "FC";
  const parts = name.replace(/^(Dr\.|Mr\.|Ms\.|Mrs\.|Prof\.)\s+/i, "").trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

export function TeacherContextProvider({ children }) {
  const [assignments, setAssignments] = useState([]);
  const [active, setActive] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadProfileAndAssignments = useCallback(async () => {
    setLoading(true);
    try {
      const rawUser = localStorage.getItem("user");
      let currentUser = null;
      if (rawUser) {
        try {
          const parsed = JSON.parse(rawUser);
          currentUser = parsed.user || parsed;
          setUser(currentUser);
        } catch {
          // ignore
        }
      }

      const token = localStorage.getItem("token");
      if (!token) {
        setLoading(false);
        return;
      }

      const res = await fetch("http://localhost:5000/api/teacher/assignments", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        throw new Error(`teacher assignments request failed: ${res.status}`);
      }

      const data = await res.json();
      const assList = data.assignments || [];
      setAssignments(assList);
      
      // Check persisted context in localStorage first, then fallback to class admin or first assignment
      const savedKey = localStorage.getItem("eduguardian_active_teacher_context_key");
      setActive((prev) => {
        if (savedKey && assList.some((a) => contextKey(a) === savedKey)) {
          return assList.find((a) => contextKey(a) === savedKey);
        }
        if (prev && assList.some((a) => contextKey(a) === contextKey(prev))) {
          return assList.find((a) => contextKey(a) === contextKey(prev));
        }
        const adminAss = assList.find((a) => a.is_class_admin);
        return adminAss || assList[0] || null;
      });
    } catch (err) {
      console.error("failed to load teacher context:", err);
      setAssignments([]);
      setActive(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProfileAndAssignments();
  }, [loadProfileAndAssignments]);

  function switchContext(key) {
    const match = assignments.find((a) => contextKey(a) === key);
    if (match) {
      setActive(match);
      localStorage.setItem("eduguardian_active_teacher_context_key", key);
    }
  }

  return (
    <TeacherContext.Provider
      value={{
        assignments,
        active,
        user,
        switchContext,
        refresh: loadProfileAndAssignments,
        loading,
      }}
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

