import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  Loader2,
  Sun,
  Moon,
  GraduationCap,
  Sparkles,
  Users,
  Activity,
  FileSpreadsheet,
  BrainCircuit,
  RotateCw,
} from "lucide-react";
import { loginTeacher } from "../services/auth";

function generateCaptchaCode() {
  const chars = "0123456789";
  let code = "";
  for (let i = 0; i < 6; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
}

const Login = () => {
  const navigate = useNavigate();

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("eduguardian-admin-theme") || localStorage.getItem("eduguardian-theme") || "dark";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("eduguardian-admin-theme", theme);
    localStorage.setItem("eduguardian-theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  };

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [captchaInput, setCaptchaInput] = useState("");
  const [captchaTarget, setCaptchaTarget] = useState(() => generateCaptchaCode());
  const [agreeTerms, setAgreeTerms] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const refreshCaptcha = () => {
    setCaptchaTarget(generateCaptchaCode());
    setCaptchaInput("");
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    if (!email.trim() || !password.trim()) {
      setError("Please enter your faculty email and password.");
      return;
    }

    if (captchaInput.trim() !== captchaTarget) {
      setError("CAPTCHA code does not match. Please enter the 6-digit code shown.");
      refreshCaptcha();
      return;
    }

    if (!agreeTerms) {
      setError("Please verify institutional role and FERPA compliance authorization.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const data = await loginTeacher(email.trim(), password);
      console.log("Teacher login successful:", data);
      navigate("/");
    } catch (err) {
      console.error(err);
      setError(err.message || "Invalid credentials. Please check your faculty login details.");
      refreshCaptcha();
    } finally {
      setLoading(false);
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
         LEFT SIDE: FACULTY LANDING SHOWCASE & BRANDING
         ========================================================= */}
      <section className="login-visual" aria-label="Faculty Portal Overview">
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
              <span>FACULTY & ADVISOR GATEWAY</span>
            </div>
          </div>

          {/* HERO MESSAGE */}
          <div className="visual-message">
            <span className="visual-eyebrow">INSTITUTIONAL EARLY WARNING SYSTEM</span>
            <h1>
              Proactive Mentorship & <span>Cohort Risk</span> Intelligence.
            </h1>
            <p>
              Empowering educators with predictive student risk triage, automated mentor assignments,
              real-time attendance forensics, and institutional intervention reports.
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
              <strong>Cohort Risk Calibrator Active</strong>
              <p>Continuous regression heuristics monitoring high-risk attrition signals across academic departments.</p>
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
              <span>Multi-Signal Risk Triage</span>
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
              <Users size={15} style={{ color: "var(--primary)", flexShrink: 0 }} />
              <span>Mentor-Student Pairing</span>
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
              <FileSpreadsheet size={15} style={{ color: "var(--primary)", flexShrink: 0 }} />
              <span>Intervention Reports</span>
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
              <span>Automated Recovery Tracing</span>
            </div>
          </div>

          {/* VISUAL FOOTER */}
          <div className="visual-footer">
            <span>
              <ShieldCheck size={14} />
              Role-Based Access Control
            </span>
            <span>
              <Sparkles size={14} />
              FERPA & Institutional Privacy Compliant
            </span>
          </div>
        </div>
      </section>

      {/* =========================================================
         RIGHT SIDE: FACULTY SIGN IN FORM
         ========================================================= */}
      <section className="login-form-side" aria-label="Faculty Sign In Form">
        <div className="login-form-wrapper">
          {/* MOBILE BRAND (shown when visual is collapsed) */}
          <div className="mobile-brand">
            <div className="brand-symbol">
              <GraduationCap size={18} />
            </div>
            <div>
              <strong>EduGuardian</strong>
              <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>FACULTY & ADMIN</div>
            </div>
          </div>

          {/* HEADING */}
          <div className="login-heading">
            <span className="form-eyebrow">FACULTY PORTAL GATEWAY</span>
            <h2>Faculty Sign In</h2>
            <p>Access cohort risk scoring, attendance rosters, and student intervention dispatch.</p>
          </div>

          {/* ERROR ALERT */}
          {error && (
            <div className="login-error" role="alert">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* FORM */}
          <form onSubmit={handleLogin}>
            {/* EMAIL */}
            <div className="form-field">
              <label htmlFor="faculty-email">Faculty Email Address</label>
              <div className="input-wrapper">
                <Mail size={16} />
                <input
                  id="faculty-email"
                  type="email"
                  className="login-input"
                  value={email}
                  disabled={loading}
                  placeholder="faculty@institution.edu"
                  autoComplete="username"
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (error) setError("");
                  }}
                  required
                />
              </div>
            </div>

            {/* PASSWORD */}
            <div className="form-field">
              <div className="password-label-row">
                <label htmlFor="faculty-password">Password</label>
                <button
                  type="button"
                  className="forgot-button"
                  disabled={loading}
                  onClick={() => setError("Please contact your departmental IT administrator to reset faculty credentials.")}
                >
                  Forgot Password?
                </button>
              </div>
              <div className="input-wrapper">
                <LockKeyhole size={16} />
                <input
                  id="faculty-password"
                  type={showPassword ? "text" : "password"}
                  className="login-input"
                  value={password}
                  disabled={loading}
                  placeholder="Enter your faculty password"
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
                  disabled={loading}
                  onClick={() => setShowPassword((curr) => !curr)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* CAPTCHA CHALLENGE */}
            <div className="form-field">
              <label htmlFor="faculty-captcha-code">Security Code (CAPTCHA)</label>
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
                      id="faculty-captcha-code"
                      type="text"
                      className="login-input"
                      value={captchaInput}
                      disabled={loading}
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

            {/* INSTITUTIONAL AUTHORIZATION & TERMS */}
            <label className="terms-row">
              <input
                type="checkbox"
                checked={agreeTerms}
                disabled={loading}
                onChange={(e) => setAgreeTerms(e.target.checked)}
                required
              />
              <span>I confirm institutional authorization and FERPA data compliance.</span>
            </label>

            {/* REMEMBER ME */}
            <label className="remember-row">
              <input
                type="checkbox"
                checked={rememberMe}
                disabled={loading}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              <span>Keep me signed in on this device</span>
            </label>

            {/* SUBMIT BUTTON */}
            <button type="submit" className="login-submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 size={16} className="spin" />
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <span>Sign In to Faculty Portal</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          {/* STUDENT PORTAL SWITCHER */}
          <div className="portal-switch-card">
            <div className="portal-switch-info">
              <span className="portal-switch-badge">ENROLLED STUDENT</span>
              <p>Are you looking for the Student Success Portal?</p>
            </div>
            <a href="http://localhost:3001/login" className="portal-switch-link">
              Student Portal
              <ArrowRight size={12} />
            </a>
          </div>

          {/* SECURITY NOTE & COPYRIGHT */}
          <div className="login-security">
            <ShieldCheck size={14} />
            <span>Secure faculty gateway with encrypted tokens and live institutional audit logging.</span>
          </div>

          <div className="login-copyright">
            © 2026 EduGuardian AI · Institutional Mentorship & Risk Platform
          </div>
        </div>
      </section>
    </div>
  );
};

export default Login;