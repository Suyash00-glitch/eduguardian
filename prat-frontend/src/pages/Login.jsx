import React, { useEffect, useState } from "react";
import {
  Eye,
  EyeOff,
  LockKeyhole,
  Phone,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  Loader2,
  Sun,
  Moon,
  RotateCw,
  Sparkles,
  GraduationCap,
  Activity,
  CheckCircle2,
  TrendingUp,
  BrainCircuit,
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

  const { portalLogin, loginLoading } = useAuth();

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
      setError("Please accept the Student Portal connection authorization.");
      return;
    }

    const result = await portalLogin(cleanMobile, password, captchaInput.trim(), rememberMe);
    if (!result.success) {
      setError(result.error);
      refreshCaptcha();
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

      {/* =========================================================
         LEFT SIDE: LANDING SHOWCASE & BRANDING
         ========================================================= */}
      <section className="login-visual" aria-label="EduGuardian Platform Overview">
        <div className="visual-background">
          <div className="visual-grid" />
          <div className="visual-glow glow-one" />
          <div className="visual-glow glow-two" />
        </div>

        <div className="visual-content">
          {/* BRAND BADGE */}
          <div className="brand-mark">
            <div className="brand-symbol">
              <GraduationCap size={22} />
            </div>
            <div>
              <strong>EduGuardian</strong>
              <span>STUDENT SUCCESS PLATFORM</span>
            </div>
          </div>

          {/* HERO MESSAGE */}
          <div className="visual-message">
            <span className="visual-eyebrow">ACADEMIC INTELLIGENCE PLATFORM</span>
            <h1>
              Protecting Academic <span>Trajectories</span> with AI Intelligence.
            </h1>
            <p>
              Connect your student portal to access predictive risk scoring, real-time attendance diagnostics,
              personalized recovery roadmaps, and autonomous AI coaching.
            </p>
          </div>

          {/* LIVE INSIGHT PULSE CARD */}
          <div className="visual-insight">
            <div className="insight-pulse">
              <span />
              <span />
              <span />
            </div>
            <div>
              <strong>Live Signal Synchronization Active</strong>
              <p>Continuous monitoring across attendance records, internal assessments, and historical credits.</p>
            </div>
          </div>

          {/* CAPABILITIES LIST */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "12px",
              marginTop: "24px",
              maxWidth: "480px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "10px 14px",
                borderRadius: "10px",
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid var(--border)",
                fontSize: "12px",
                color: "var(--text)",
              }}
            >
              <Activity size={15} style={{ color: "var(--primary)", flexShrink: 0 }} />
              <span>Real-Time Risk Scoring</span>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "10px 14px",
                borderRadius: "10px",
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid var(--border)",
                fontSize: "12px",
                color: "var(--text)",
              }}
            >
              <TrendingUp size={15} style={{ color: "var(--primary)", flexShrink: 0 }} />
              <span>Attendance Forensics</span>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "10px 14px",
                borderRadius: "10px",
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid var(--border)",
                fontSize: "12px",
                color: "var(--text)",
              }}
            >
              <BrainCircuit size={15} style={{ color: "var(--primary)", flexShrink: 0 }} />
              <span>AI Guidance Engine</span>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "10px 14px",
                borderRadius: "10px",
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid var(--border)",
                fontSize: "12px",
                color: "var(--text)",
              }}
            >
              <CheckCircle2 size={15} style={{ color: "var(--primary)", flexShrink: 0 }} />
              <span>Tailored Recovery Plans</span>
            </div>
          </div>

          {/* VISUAL FOOTER */}
          <div className="visual-footer">
            <span>
              <ShieldCheck size={14} />
              Institutional Grade Privacy
            </span>
            <span>
              <Sparkles size={14} />
              Real-Time Portal Synchronization
            </span>
          </div>
        </div>
      </section>

      {/* =========================================================
         RIGHT SIDE: STUDENT SIGN IN FORM
         ========================================================= */}
      <section className="login-form-side" aria-label="Student Sign In Form">
        <div className="login-form-wrapper">
          {/* MOBILE BRAND (shown when visual is collapsed) */}
          <div className="mobile-brand">
            <div className="brand-symbol">
              <GraduationCap size={18} />
            </div>
            <div>
              <strong>EduGuardian</strong>
              <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>STUDENT PORTAL</div>
            </div>
          </div>

          {/* HEADING */}
          <div className="login-heading">
            <span className="form-eyebrow">SECURE STUDENT ACCESS</span>
            <h2>Student Sign In</h2>
            <p>Enter your University Solutions credentials to synchronize your student portal.</p>
          </div>

          {/* ERROR ALERT */}
          {error && (
            <div className="login-error" role="alert">
              <AlertCircle size={16} style={{ flexShrink: 0, marginTop: "2px" }} />
              <span>{error}</span>
            </div>
          )}

          {/* FORM */}
          <form onSubmit={handlePortalSubmit}>
            {/* REGISTERED MOBILE NUMBER */}
            <div className="form-field">
              <label htmlFor="student-mobile">Registered Mobile Number</label>
              <div className="input-wrapper">
                <Phone size={16} />
                <input
                  id="student-mobile"
                  type="tel"
                  className="login-input"
                  value={mobile}
                  disabled={loginLoading}
                  placeholder="Enter 10-digit mobile number"
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

            {/* PORTAL PASSWORD */}
            <div className="form-field">
              <div className="password-label-row">
                <label htmlFor="student-password">Portal Password</label>
                <a
                  href="https://studentportal.universitysolutions.in/index.html"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="forgot-button"
                  style={{ textDecoration: "none", cursor: "pointer" }}
                >
                  Forgot Password?
                </a>
              </div>
              <div className="input-wrapper">
                <LockKeyhole size={16} />
                <input
                  id="student-password"
                  type={showPassword ? "text" : "password"}
                  className="login-input"
                  value={password}
                  disabled={loginLoading}
                  placeholder="Enter your portal password"
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
                  onClick={() => setShowPassword((curr) => !curr)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* CAPTCHA CHALLENGE */}
            <div className="form-field">
              <label htmlFor="captcha-code">Security Code (CAPTCHA)</label>
              <div className="captcha-row">
                <div className="captcha-badge" title="Verification Code">
                  {captchaTarget}
                </div>
                <button
                  type="button"
                  className="captcha-refresh"
                  onClick={refreshCaptcha}
                  title="Refresh security code"
                  aria-label="Refresh security code"
                >
                  <RotateCw size={15} />
                </button>
                <div className="captcha-input-wrap">
                  <div className="input-wrapper">
                    <input
                      id="captcha-code"
                      type="text"
                      className="login-input"
                      value={captchaInput}
                      disabled={loginLoading}
                      placeholder="6 digits"
                      maxLength={6}
                      style={{ paddingLeft: "14px" }}
                      onChange={(e) => {
                        setCaptchaInput(e.target.value.replace(/\D/g, ""));
                        if (error) setError("");
                      }}
                      required
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* AUTHORIZATION & TERMS */}
            <label className="terms-row">
              <input
                type="checkbox"
                checked={agreeTerms}
                disabled={loginLoading}
                onChange={(e) => setAgreeTerms(e.target.checked)}
                required
              />
              <span>I authorize secure live synchronization with University Solutions student records.</span>
            </label>

            {/* REMEMBER ME */}
            <label className="remember-row">
              <input
                type="checkbox"
                checked={rememberMe}
                disabled={loginLoading}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              <span>Remember this session on this device</span>
            </label>

            {/* SUBMIT BUTTON */}
            <button type="submit" className="login-submit" disabled={loginLoading}>
              {loginLoading ? (
                <>
                  <Loader2 size={16} className="spin" />
                  <span>Authenticating Portal...</span>
                </>
              ) : (
                <>
                  <span>Sign In to Dashboard</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          {/* FACULTY PORTAL SWITCHER */}
          <div className="portal-switch-card">
            <div className="portal-switch-info">
              <span className="portal-switch-badge">FACULTY & ADVISORS</span>
              <p>Looking for the Faculty & Admin Gateway?</p>
            </div>
            <a href="http://localhost:3002/login" className="portal-switch-link">
              Faculty Portal
              <ArrowRight size={12} />
            </a>
          </div>

          {/* SECURITY NOTE & COPYRIGHT */}
          <div className="login-security">
            <ShieldCheck size={14} />
            <span>Credentials are authenticated via secure HTTPS handshake and never persisted in cleartext.</span>
          </div>

          <div className="login-copyright">
            © 2026 EduGuardian AI · Student Success & Risk Protection Platform
          </div>
        </div>
      </section>
    </div>
  );
}

export default Login;
