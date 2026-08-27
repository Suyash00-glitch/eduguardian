import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  AlertCircle,
  Loader2,
  Sun,
  Moon,
  GraduationCap,
} from "lucide-react";
import { loginTeacher } from "../services/auth";

const Login = () => {
  const navigate = useNavigate();

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

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();

    if (!email.trim() || !password.trim()) {
      setError("Please enter your email and password.");
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
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = () => {
    setEmail("teacher@example.com");
    setPassword("teacher123");
    setError("");
  };

  return (
    <div className="login-page">
      {/* Theme Toggle */}
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
              <GraduationCap size={22} />
            </div>
            <div>
              <strong>EduGuardian AI</strong>
              <span>Faculty & Teacher Portal</span>
            </div>
          </div>

          <div className="visual-message">
            <span className="visual-eyebrow">ACADEMIC EXCELLENCE & INTERVENTION</span>
            <h1>
              Guide your students.
              <br />
              <span>Prevent dropouts.</span>
              <br />
              Shape outcomes.
            </h1>
            <p>
              Real-time cohort risk scoring, automated recovery pathways, and AI-powered
              academic insights to empower faculty and mentors.
            </p>
          </div>

          <div className="visual-insight">
            <div className="insight-pulse">
              <span />
              <span />
              <span />
            </div>
            <div>
              <strong>Empower Every Learner</strong>
              <p>Early academic warning signals convert into actionable recovery plans before exams.</p>
            </div>
          </div>

          <div className="visual-footer">
            <span>
              <ShieldCheck size={13} />
              Privacy-first
            </span>
            <span>
              <Sparkles size={13} />
              Explainable AI
            </span>
            <span>
              <LockKeyhole size={13} />
              Role-based access
            </span>
          </div>
        </div>
      </section>

      {/* RIGHT FORM PANEL */}
      <section className="login-form-side">
        <div className="login-form-wrapper">
          <div className="mobile-brand">
            <div className="brand-symbol">
              <GraduationCap size={18} />
            </div>
            <strong>EduGuardian AI</strong>
          </div>

          <div className="login-heading">
            <span className="form-eyebrow">FACULTY & ADMIN PORTAL</span>
            <h2>Welcome back.</h2>
            <p>Sign in to access student rosters, attendance tracking, and risk analytics.</p>
          </div>

          {error && (
            <div className="login-error">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleLogin}>
            {/* Email */}
            <div className="form-field">
              <label htmlFor="teacher-email">Faculty Email</label>
              <div className="input-wrapper">
                <Mail size={16} />
                <input
                  id="teacher-email"
                  type="email"
                  value={email}
                  disabled={loading}
                  placeholder="teacher@example.com"
                  autoComplete="username"
                  className="login-input"
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (error) setError("");
                  }}
                />
              </div>
            </div>

            {/* Password */}
            <div className="form-field">
              <div className="password-label-row">
                <label htmlFor="teacher-password">Password</label>
                <button
                  type="button"
                  className="forgot-button"
                  disabled={loading}
                  onClick={() => setError("Please contact your university administrator to reset your faculty credentials.")}
                >
                  Forgot password?
                </button>
              </div>
              <div className="input-wrapper">
                <LockKeyhole size={16} />
                <input
                  id="teacher-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  disabled={loading}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  className="login-input"
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (error) setError("");
                  }}
                />
                <button
                  type="button"
                  className="password-toggle"
                  disabled={loading}
                  onClick={() => setShowPassword((current) => !current)}
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <label className="remember-row">
              <input
                type="checkbox"
                checked={rememberMe}
                disabled={loading}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              <span>Remember me</span>
            </label>

            {/* Submit */}
            <button
              type="submit"
              className="login-submit"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="spin" />
                  Signing you in...
                </>
              ) : (
                <>
                  Sign in
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          {/* Demo Access */}
          <div className="demo-login" onClick={fillDemo} style={{ cursor: "pointer" }} title="Click to autofill demo credentials">
            <div className="demo-heading">DEMO FACULTY ACCESS (CLICK TO AUTOFILL)</div>
            <div className="demo-row">
              <span>Email</span>
              <code>teacher@example.com</code>
            </div>
            <div className="demo-row">
              <span>Password</span>
              <code>teacher123</code>
            </div>
          </div>

          {/* Portal Switcher to Student Portal */}
          <div className="portal-switch-card">
            <div className="portal-switch-info">
              <span className="portal-switch-badge">STUDENT PORTAL</span>
              <p>Are you an enrolled student?</p>
            </div>
            <a
              href="http://localhost:3001/login"
              className="portal-switch-link"
              title="Switch to Student Portal"
            >
              <span>Student Login</span>
              <ArrowRight size={13} />
            </a>
          </div>

          <div className="login-security">
            <ShieldCheck size={13} />
            <span>
              Secure faculty gateway with role-based access control and encrypted communications.
            </span>
          </div>

          <div className="login-copyright">
            EduGuardian · Teacher & Faculty Administration Platform
          </div>
        </div>
      </section>
    </div>
  );
};

export default Login;