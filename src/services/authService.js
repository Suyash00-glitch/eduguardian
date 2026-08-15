const DEMO_USER = {
  id: "STU-DEMO-001",
  full_name: "Pratham",
  email: "student@eduguardian.ai",
  role: "student",
  usn: "DEMOUSN001",
  department: "Information Science and Engineering",
  semester: 4,
  section: "A",
};

const DEMO_PASSWORD = "student123";

const TOKEN_KEY = "eduguardian_token";
const USER_KEY = "eduguardian_user";

export const loginUser = async (identifier, password, rememberMe = false) => {
  /*
   * DEMO ONLY
   *
   * BACKEND REPLACEMENT:
   * Replace this function with:
   *
   * POST /api/auth/login
   *
   * Expected response:
   * {
   *   token: "...",
   *   user: {
   *     id,
   *     full_name,
   *     email,
   *     role,
   *     ...
   *   }
   * }
   */

  await new Promise((resolve) => setTimeout(resolve, 900));

  const validIdentifier =
    identifier.toLowerCase() === DEMO_USER.email.toLowerCase() ||
    identifier.toLowerCase() === DEMO_USER.usn.toLowerCase();

  if (!validIdentifier || password !== DEMO_PASSWORD) {
    throw new Error("Invalid email/USN or password.");
  }

  const token = "demo-token-eduguardian";

  const session = {
    token,
    user: DEMO_USER,
  };

  const storage = rememberMe ? localStorage : sessionStorage;

  storage.setItem(TOKEN_KEY, token);
  storage.setItem(USER_KEY, JSON.stringify(DEMO_USER));

  return session;
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

  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
};

export const getAuthToken = () => {
  return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
};

function clearSession() {
  logoutUser();
}
