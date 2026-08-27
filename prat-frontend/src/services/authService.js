const RAW_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
const API_URL = RAW_URL.endsWith("/api") ? RAW_URL.slice(0, -4) : RAW_URL;

const TOKEN_KEY = "eduguardian_token";
const USER_KEY = "eduguardian_user";
const CONTEXT_KEY = "eduguardian_student_context";

/**
 * Authenticates with real Student Portal credentials via edu-backend
 */
export const portalLogin = async (mobile, password, captcha = null, rememberMe = false) => {
  const response = await fetch(`${API_URL}/api/auth/portal-login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      mobile,
      password,
      captcha,
      terms_accepted: true,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Student Portal authentication failed.");
  }

  const token = data.access_token;
  const user = data.user;

  if (!token || !user) {
    throw new Error("Invalid response from server.");
  }

  const storage = rememberMe ? localStorage : sessionStorage;
  storage.setItem(TOKEN_KEY, token);
  storage.setItem(USER_KEY, JSON.stringify(user));
  if (data.student_context) {
    storage.setItem(CONTEXT_KEY, JSON.stringify(data.student_context));
  }

  return {
    token,
    user,
    student_context: data.student_context,
    risk_evaluation: data.risk_evaluation,
  };
};

/**
 * Explicitly isolated demo account login
 */
export const demoLogin = async (identifier = "student@eduguardian.ai", rememberMe = false) => {
  const response = await fetch(`${API_URL}/api/auth/demo-login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      identifier,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Demo login failed.");
  }

  const token = data.access_token;
  const user = data.user;

  const storage = rememberMe ? localStorage : sessionStorage;
  storage.setItem(TOKEN_KEY, token);
  storage.setItem(USER_KEY, JSON.stringify(user));
  if (data.student_context) {
    storage.setItem(CONTEXT_KEY, JSON.stringify(data.student_context));
  }

  return {
    token,
    user,
    student_context: data.student_context,
    risk_evaluation: data.risk_evaluation,
  };
};

export const loginUser = async (email, password, rememberMe = false) => {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email,
      password,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Invalid email or password.");
  }

  const token = data.access_token;
  const user = data.user;

  if (!token || !user) {
    throw new Error("Invalid login response from server.");
  }

  const storage = rememberMe ? localStorage : sessionStorage;
  storage.setItem(TOKEN_KEY, token);
  storage.setItem(USER_KEY, JSON.stringify(user));

  return {
    token,
    user,
  };
};

export const getStoredSession = () => {
  const token =
    localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);

  const userData =
    localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);

  if (!token || !userData) {
    return null;
  }

  try {
    return {
      token,
      user: JSON.parse(userData),
    };
  } catch {
    clearSession();
    return null;
  }
};

export const logoutUser = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(CONTEXT_KEY);

  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
  sessionStorage.removeItem(CONTEXT_KEY);
};

export const getAuthToken = () => {
  return (
    localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY)
  );
};

function clearSession() {
  logoutUser();
}