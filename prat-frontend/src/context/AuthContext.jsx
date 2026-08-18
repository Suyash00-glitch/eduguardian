import React, { createContext, useContext, useEffect, useState } from "react";

import {
  loginUser,
  getStoredSession,
  logoutUser,
} from "../services/authService";

import { demoStudent } from "../services/demoData";

const AuthContext = createContext(null);

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === "true";

const demoUser = {
  ...demoStudent,
  full_name: demoStudent.name,
};

const DEMO_TOKEN = "demo-token";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  const [loading, setLoading] = useState(true);
  const [loginLoading, setLoginLoading] = useState(false);

  useEffect(() => {
    if (DEMO_MODE) {
      setUser(demoUser);
      setToken(DEMO_TOKEN);
      setLoading(false);
      return;
    }

    const session = getStoredSession();

    if (session) {
      setUser(session.user);
      setToken(session.token);
    }

    setLoading(false);
  }, []);

  const login = async (identifier, password, rememberMe = false) => {
    setLoginLoading(true);

    try {
      if (DEMO_MODE) {
        await new Promise((resolve) => setTimeout(resolve, 500));

        setUser(demoUser);
        setToken(DEMO_TOKEN);

        return {
          success: true,
          user: demoUser,
        };
      }

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

  const logout = () => {
    if (!DEMO_MODE) {
      logoutUser();
    }

    setUser(null);
    setToken(null);
  };

  const value = {
    user,
    token,

    isAuthenticated: Boolean(user && token),

    loading,
    loginLoading,

    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
