const API_URL = "http://127.0.0.1:8000";

export async function loginTeacher(email, password) {
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
    throw new Error(data.detail || "login failed");
  }

  // store jwt
  localStorage.setItem("token", data.access_token);

  // optional: store user information
  localStorage.setItem("user", JSON.stringify(data));

  return data;
}

export function getToken() {
  return localStorage.getItem("token");
}

export function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

export function isLoggedIn() {
  return !!localStorage.getItem("token");
}