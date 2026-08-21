import React, { useEffect, useState } from "react";
import {
  Eye,
  EyeOff,
  LockKeyhole,
  Phone,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  AlertCircle,
  Loader2,
  Sun,
  Moon,
  RotateCw,
  CheckCircle2,
  Building2,
  BookOpen,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";

function generateCaptchaCode() {
  const chars = "0123456789";
  let code = "";
  for (let i = 0; i < 6; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
}

function Login() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("eduguardian-theme") || "dark";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("eduguardian-theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  };

  const { portalLogin, demoLogin, loginLoading } = useAuth();

  // Login Mode: "portal" (real student portal) vs "demo"
  const [loginMode, setLoginMode] = useState("portal");

  // Portal form fields
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [captchaInput, setCaptchaInput] = useState("");
  const [captchaTarget, setCaptchaTarget] = useState(() => generateCaptchaCode());
  const [agreeTerms, setAgreeTerms] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState("");

  const refreshCaptcha = () => {
    setCaptchaTarget(generateCaptchaCode());
    setCaptchaInput("");
  };

  const handlePortalSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const cleanMobile = mobile.trim().replace(/\D/g, "");
    if (cleanMobile.length !== 10) {
      setError("Please enter your valid 10-digit registered student mobile number.");
      return;
    }

    if (!password.trim()) {
      setError("Please enter your Student Portal password.");
      return;
    }

    if (captchaInput.trim() !== captchaTarget) {
      setError("CAPTCHA code does not match. Please enter the 6-digit code shown.");
      refreshCaptcha();
      return;
    }

    if (!agreeTerms) {
      setError("Please accept the Student Portal usage terms.");
      return;
    }

    const result = await portalLogin(cleanMobile, password, captchaInput.trim(), rememberMe);
    if (!result.success) {
      setError(result.error);
      refreshCaptcha();
    }
  };

  const handleDemoSubmit = async (demoId) => {
    setError("");
    const result = await demoLogin(demoId, true);
    if (!result.success) {
      setError(result.error);
    }
  };

  return (
    <div className="login-page">
      {/* THEME TOGGLE */}
      <button
        type="button"
        className="login-theme-toggle"
        onClick={toggleTheme}
        aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
        title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
      >
        {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
      </button>

      {/* LEFT VISUAL PANEL */}
      <section className="login-visual">
        <div className="visual-background">
          <div className="visual-grid" />
          <div className="visual-glow glow-one" />
          <div className="visual-glow glow-two" />
        </div>

        <div className="visual-content">
          <div className="brand-mark">
            <div className="brand-symbol">
              <Sparkles size={18} />
            </div>
            <div>
              <strong>EduGuardian</strong>
              <span>AI-powered student success</span>
            </div>
          </div>

          <div className="visual-message">
            <span className="visual-eyebrow">AUTHENTIC STUDENT CONNECTION</span>
            <h1>
              Connect your
              <br />
              <span>Student Portal.</span>
              <br />
              Unlock your potential.
            </h1>
            <p>
              Sign in with your University Solutions Student Portal account to view real-time academic records, learning trajectory, and personalized support plans.
            </p>
          </div>

          <div className="visual-insight">
            <div className="insight-pulse">
              <span />
              <span />
              <span />
            </div>
            <div>
              <strong>Authoritative & Privacy-Protected.</strong>
              <p>
                Your portal password is used solely for live authentication and is never persisted or logged.
              </p>
            </div>
          </div>

          <div className="visual-footer">
            <span>
              <ShieldCheck size={13} />
              Zero Password Storage
            </span>
            <span>
              <Building2 size={13} />
              University Solutions Portal
            </span>
            <span>
              <Sparkles size={13} />
              Explainable AI
            </span>
          </div>
        </div>
      </section>

      {/* RIGHT LOGIN FORM */}
      <section className="login-form-side">
        <div className="login-form-wrapper">
          <div className="mobile-brand">
            <div className="brand-symbol">
              <Sparkles size={17} />
            </div>
            <strong>EduGuardian</strong>
          </div>

          <div className="login-heading">
            <span className="form-eyebrow">UNIVERSITY SOLUTIONS PORTAL</span>
            <h2>Student Sign In</h2>
            <p>Enter your student portal mobile number and password to access your dashboard.</p>
          </div>

          {/* MODE SELECTOR */}
          <div className="login-mode-tabs" style={{ display: "flex", gap: "8px", marginBottom: "18px" }}>
            <button
              type="button"
              className={`mode-tab-btn ${loginMode === "portal" ? "active" : ""}`}
              onClick={() => setLoginMode("portal")}
              style={{
                flex: 1,
                padding: "8px 12px",
                borderRadius: "8px",
                border: "1px solid var(--border)",
                background: loginMode === "portal" ? "var(--primary-soft)" : "transparent",
                color: loginMode === "portal" ? "var(--primary)" : "var(--text-muted)",
                fontSize: "12px",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              Student Portal Login
            </button>
            <button
              type="button"
              className={`mode-tab-btn ${loginMode === "demo" ? "active" : ""}`}
              onClick={() => setLoginMode("demo")}
              style={{
                flex: 1,
                padding: "8px 12px",
                borderRadius: "8px",
                border: "1px solid var(--border)",
                background: loginMode === "demo" ? "var(--primary-soft)" : "transparent",
                color: loginMode === "demo" ? "var(--primary)" : "var(--text-muted)",
                fontSize: "12px",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              Demo Profile Mode
            </button>
          </div>

          {error && (
            <div className="login-error">
              <AlertCircle size={15} />
              <span>{error}</span>
            </div>
          )}

          {loginMode === "portal" ? (
            /* REAL PORTAL LOGIN FORM */
            <form onSubmit={handlePortalSubmit}>
              {/* Registered Mobile */}
              <div className="form-field">
                <label htmlFor="portal-mobile">Registered Mobile Number (10 Digits)</label>
                <div className="input-wrapper">
                  <Phone size={16} />
                  <input
                    id="portal-mobile"
                    type="tel"
                    value={mobile}
                    disabled={loginLoading}
                    placeholder="e.g. 9876543210"
                    maxLength={10}
                    autoComplete="username"
                    onChange={(e) => {
                      setMobile(e.target.value.replace(/\D/g, ""));
                      if (error) setError("");
                    }}
                    required
                  />
                </div>
              </div>

              {/* Portal Password */}
              <div className="form-field">
                <div className="password-label-row">
                  <label htmlFor="portal-password">Student Portal Password</label>
                  <a
                    href="https://studentportal.universitysolutions.in/index.html"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="forgot-button"
                    style={{ textDecoration: "none" }}
                  >
                    Forgot on Portal?
                  </a>
                </div>
                <div className="input-wrapper">
                  <LockKeyhole size={16} />
                  <input
                    id="portal-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    disabled={loginLoading}
                    placeholder="Enter your student portal password"
                    autoComplete="current-password"
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (error) setError("");
                    }}
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    disabled={loginLoading}
                    onClick={() => setShowPassword((current) => !current)}
                  >
                    {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>

              {/* CAPTCHA CHALLENGE */}
              <div className="form-field">
                <label htmlFor="portal-captcha">Security Verification (CAPTCHA)</label>
                <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                  <div
                    style={{
                      background: "rgba(6, 214, 160, 0.1)",
                      border: "1px dashed var(--primary)",
                      borderRadius: "8px",
                      padding: "8px 16px",
                      fontSize: "18px",
                      fontWeight: 800,
                      letterSpacing: "4px",
                      color: "var(--primary)",
                      userSelect: "none",
                      fontFamily: "monospace",
                    }}
                  >
                    {captchaTarget}
                  </div>
                  <button
                    type="button"
                    onClick={refreshCaptcha}
                    title="Refresh Captcha"
                    style={{
                      background: "var(--surface-soft)",
                      border: "1px solid var(--border)",
                      borderRadius: "8px",
                      padding: "9px 12px",
                      cursor: "pointer",
                      color: "var(--text-muted)",
                    }}
                  >
                    <RotateCw size={15} />
                  </button>
                  <div className="input-wrapper" style={{ flex: 1 }}>
                    <input
                      id="portal-captcha"
                      type="text"
                      value={captchaInput}
                      disabled={loginLoading}
                      placeholder="Enter 6 digits"
                      maxLength={6}
                      onChange={(e) => {
                        setCaptchaInput(e.target.value.replace(/\D/g, ""));
                        if (error) setError("");
                      }}
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Instructions Checkbox */}
              <label className="remember-row" style={{ marginTop: "12px" }}>
                <input
                  type="checkbox"
                  checked={agreeTerms}
                  disabled={loginLoading}
                  onChange={(e) => setAgreeTerms(e.target.checked)}
                  required
                />
                <span style={{ fontSize: "11px" }}>
                  I acknowledge and authorize connection with University Solutions Student Portal.
                </span>
              </label>

              {/* Submit Button */}
              <button
                type="submit"
                className="login-submit"
                disabled={loginLoading}
              >
                {loginLoading ? (
                  <>
                    <Loader2 size={16} className="spin" />
                    Authenticating with Student Portal...
                  </>
                ) : (
                  <>
                    Connect & Sign In
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </form>
          ) : (
            /* DEMO ACCOUNT QUICK SELECT */
            <div className="demo-profile-box" style={{ marginTop: "10px" }}>
              <p style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "12px" }}>
                Select a sample student profile to explore EduGuardian with simulated records:
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <button
                  type="button"
                  onClick={() => handleDemoSubmit("Alex Johnson")}
                  disabled={loginLoading}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "10px 14px",
                    borderRadius: "9px",
                    border: "1px solid var(--border)",
                    background: "var(--surface)",
                    color: "var(--text)",
                    cursor: "pointer",
                    textAlign: "left",
                  }}
                >
                  <div>
                    <strong>Alex Johnson</strong>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>USN: 1MS21IS001 · 92.5% Attendance (On Track)</div>
                  </div>
                  <ArrowRight size={14} color="var(--primary)" />
                </button>

                <button
                  type="button"
                  onClick={() => handleDemoSubmit("David Miller")}
                  disabled={loginLoading}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "10px 14px",
                    borderRadius: "9px",
                    border: "1px solid var(--border)",
                    background: "var(--surface)",
                    color: "var(--text)",
                    cursor: "pointer",
                    textAlign: "left",
                  }}
                >
                  <div>
                    <strong>David Miller</strong>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>USN: NNM24IS019 · 52.5% Attendance (Support Plan)</div>
                  </div>
                  <ArrowRight size={14} color="var(--primary)" />
                </button>
              </div>
            </div>
          )}

          {/* FACULTY PORTAL SWITCHER */}
          <div className="portal-switch-card" style={{ marginTop: "20px" }}>
            <div className="portal-switch-info">
              <span className="portal-switch-badge">FACULTY & ADMIN</span>
              <p>Are you a teacher, mentor or department admin?</p>
            </div>
            <a
              href="http://localhost:3002/login"
              className="portal-switch-link"
              title="Switch to Teacher & Admin Portal"
            >
              <span>Teacher Login</span>
              <ArrowRight size={13} />
            </a>
          </div>

          <div className="login-security">
            <ShieldCheck size={13} />
            <span>
              Passwords are never saved. Real portal sessions are securely authenticated.
            </span>
          </div>

          <div className="login-copyright">
            EduGuardian · University Solutions Integration
          </div>
        </div>
      </section>
    </div>
  );
}

export default Login;
