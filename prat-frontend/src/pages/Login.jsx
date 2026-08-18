import React, { useEffect, useState } from "react";
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
} from "lucide-react";

import { useAuth } from "../context/AuthContext";

function Login() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("eduguardian-theme") || "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("eduguardian-theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  };
  const { login, loginLoading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");

    if (!email.trim() || !password.trim()) {
      setError("Please enter your email/USN and password.");

      return;
    }

    const result = await login(email.trim(), password, rememberMe);

    if (!result.success) {
      setError(result.error);
    }
  };

  return (
    <div className="login-page">
      {/* LEFT SIDE */}
      <button
        type="button"
        className="login-theme-toggle"
        onClick={toggleTheme}
        aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
        title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
      >
        {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
      </button>
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
            <span className="visual-eyebrow">YOUR ACADEMIC JOURNEY</span>

            <h1>
              Understand your
              <br />
              <span>progress.</span>
              <br />
              Shape your future.
            </h1>

            <p>
              EduGuardian turns academic signals into meaningful support,
              personalized recovery plans, and practical guidance.
            </p>
          </div>

          <div className="visual-insight">
            <div className="insight-pulse">
              <span />
              <span />
              <span />
            </div>

            <div>
              <strong>Your success is a journey.</strong>

              <p>
                We help you understand where you are and what you can do next.
              </p>
            </div>
          </div>

          <div className="visual-footer">
            <span>
              <ShieldCheck size={12} />
              Privacy-first
            </span>

            <span>
              <Sparkles size={12} />
              Explainable AI
            </span>

            <span>
              <LockKeyhole size={12} />
              Secure access
            </span>
          </div>
        </div>
      </section>

      {/* RIGHT SIDE */}

      <section className="login-form-side">
        <div className="login-form-wrapper">
          <div className="mobile-brand">
            <div className="brand-symbol">
              <Sparkles size={17} />
            </div>

            <strong>EduGuardian</strong>
          </div>

          <div className="login-heading">
            <span className="form-eyebrow">STUDENT PORTAL</span>

            <h2>Welcome back.</h2>

            <p>Sign in to continue your academic journey.</p>
          </div>

          {error && (
            <div className="login-error">
              <AlertCircle size={15} />

              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Email / USN */}

            <div className="form-field">
              <label htmlFor="email">Email or USN</label>

              <div className="input-wrapper">
                <Mail size={16} />

                <input
                  id="email"
                  type="text"
                  value={email}
                  disabled={loginLoading}
                  placeholder="Enter your email or USN"
                  autoComplete="username"
                  onChange={(e) => {
                    setEmail(e.target.value);

                    if (error) {
                      setError("");
                    }
                  }}
                />
              </div>
            </div>

            {/* Password */}

            <div className="form-field">
              <div className="password-label-row">
                <label htmlFor="password">Password</label>

                <button
                  type="button"
                  className="forgot-button"
                  disabled={loginLoading}
                  onClick={() =>
                    setError(
                      "Password recovery will be connected to the backend.",
                    )
                  }
                >
                  Forgot password?
                </button>
              </div>

              <div className="input-wrapper">
                <LockKeyhole size={16} />

                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  disabled={loginLoading}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  onChange={(e) => {
                    setPassword(e.target.value);

                    if (error) {
                      setError("");
                    }
                  }}
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

            {/* Remember */}

            <label className="remember-row">
              <input
                type="checkbox"
                checked={rememberMe}
                disabled={loginLoading}
                onChange={(e) => setRememberMe(e.target.checked)}
              />

              <span>Remember me</span>
            </label>

            {/* Submit */}

            <button
              type="submit"
              className="login-submit"
              disabled={loginLoading}
            >
              {loginLoading ? (
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

          {/* Demo */}

          <div className="demo-login">
            <div className="demo-heading">DEMO ACCESS</div>

            <div className="demo-row">
              <span>Email</span>
              <code>student@eduguardian.ai</code>
            </div>

            <div className="demo-row">
              <span>Password</span>
              <code>student123</code>
            </div>
          </div>

          <div className="login-security">
            <ShieldCheck size={13} />

            <span>
              Your academic data is protected and used only to provide
              personalized support.
            </span>
          </div>

          <div className="login-copyright">
            EduGuardian · Student Success Platform
          </div>
        </div>
      </section>
    </div>
  );
}

export default Login;
