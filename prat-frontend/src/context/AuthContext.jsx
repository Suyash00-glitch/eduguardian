import React, { createContext, useContext, useEffect, useState } from "react";

import {
  portalLogin as apiPortalLogin,
  demoLogin as apiDemoLogin,
  loginUser,
  getStoredSession,
  logoutUser,
} from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [studentContext, setStudentContext] = useState(null);

  const [loading, setLoading] = useState(true);
  const [loginLoading, setLoginLoading] = useState(false);

  /* =====================================================
     INITIAL SESSION
     ===================================================== */

  useEffect(() => {
    const session = getStoredSession();

    if (session) {
      setUser(session.user);
      setToken(session.token);
      const storedCtx =
        localStorage.getItem("eduguardian_student_context") ||
        sessionStorage.getItem("eduguardian_student_context");
      if (storedCtx) {
        try {
          setStudentContext(JSON.parse(storedCtx));
        } catch {
          // ignore
        }
      }
    }

    setLoading(false);
  }, []);

  /* =====================================================
     PORTAL LOGIN
     ===================================================== */

  const portalLogin = async (mobile, password, captcha = null, rememberMe = false) => {
    setLoginLoading(true);

    try {
      const session = await apiPortalLogin(mobile, password, captcha, rememberMe);

      setUser(session.user);
      setToken(session.token);
      setStudentContext(session.student_context);

      return {
        success: true,
        user: session.user,
        student_context: session.student_context,
      };
    } catch (error) {
      return {
        success: false,
        error: error.message || "Portal login failed.",
      };
    } finally {
      setLoginLoading(false);
    }
  };

  /* =====================================================
     DEMO LOGIN
     ===================================================== */

  const demoLogin = async (identifier = "student@eduguardian.ai", rememberMe = false) => {
    setLoginLoading(true);

    try {
      const session = await apiDemoLogin(identifier, rememberMe);

      setUser(session.user);
      setToken(session.token);
      setStudentContext(session.student_context);

      return {
        success: true,
        user: session.user,
        student_context: session.student_context,
      };
    } catch (error) {
      return {
        success: false,
        error: error.message || "Demo login failed.",
      };
    } finally {
      setLoginLoading(false);
    }
  };

  /* =====================================================
     STANDARD LOGIN
     ===================================================== */

  const login = async (identifier, password, rememberMe = false) => {
    setLoginLoading(true);

    try {
      const session = await loginUser(identifier, password, rememberMe);

      setUser(session.user);
      setToken(session.token);

      return {
        success: true,
        user: session.user,
      };
    } catch (error) {
      return {
        success: false,
        error: error.message || "Login failed.",
      };
    } finally {
      setLoginLoading(false);
    }
  };

  /* =====================================================
     LOGOUT
     ===================================================== */

  const logout = () => {
    logoutUser();
    setUser(null);
    setToken(null);
    setStudentContext(null);
  };

  /* =====================================================
     CONTEXT VALUE
     ===================================================== */

  const value = {
    user,
    token,
    studentContext,

    isAuthenticated: Boolean(user && token),

    loading,
    loginLoading,

    portalLogin,
    demoLogin,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/* =====================================================
   useAuth HOOK
   ===================================================== */

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
