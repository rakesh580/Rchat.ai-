import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const location = useLocation();
  const navigate = useNavigate();
  const { login } = useAuth();
  const justRegistered = location.state?.registered;

  const [emailOrUsername, setEmailOrUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    if (!emailOrUsername || !password) {
      setError("All fields are required");
      return;
    }

    setLoading(true);
    try {
      const data = await api("/auth/login", {
        method: "POST",
        body: { username_or_email: emailOrUsername, password },
      });
      login(data.access_token, data.user || null);
      navigate("/chat");
    } catch (err) {
      // Map known error patterns to user-friendly messages
      const msg = err.message || "";
      if (msg.includes("Session expired")) {
        setError("Your session has expired. Please log in again.");
      } else if (msg.includes("Invalid username") || msg.includes("Invalid password") || msg.includes("401")) {
        setError("Invalid email/username or password. Please try again.");
      } else if (msg.includes("Rate limit") || msg.includes("429")) {
        setError("Too many login attempts. Please wait a minute and try again.");
      } else if (msg.includes("fetch") || msg.includes("network") || msg.includes("Failed")) {
        setError("Unable to connect to the server. Please check your connection.");
      } else {
        setError("Login failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">

      {/* ── Left brand panel (hidden on mobile) ── */}
      <div className="auth-left">
        <div className="auth-logo-wrap">
          {/* Chat bubble SVG icon */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-hidden="true"
          >
            <path d="M12 2C6.477 2 2 6.163 2 11.333c0 2.742 1.2 5.21 3.12 6.942L4 22l4.547-2.274A11.23 11.23 0 0 0 12 20.667c5.523 0 10-4.164 10-9.334C22 6.163 17.523 2 12 2Z" />
          </svg>
          <span className="auth-app-name">Rchat.ai</span>
        </div>

        <p className="auth-tagline">Your AI-powered inbox that never sleeps</p>

        <ul className="auth-features">
          <li className="auth-feature-pill" style={{ animationDelay: "0ms" }}>
            ✦ Auto-replies while you&apos;re away
          </li>
          <li className="auth-feature-pill" style={{ animationDelay: "120ms" }}>
            ⚡ Urgency detection &amp; forwarding
          </li>
          <li className="auth-feature-pill" style={{ animationDelay: "240ms" }}>
            📋 Smart briefings on return
          </li>
          <li className="auth-feature-pill" style={{ animationDelay: "360ms" }}>
            🤖 Powered by LangGraph
          </li>
        </ul>
      </div>

      {/* ── Right form panel ── */}
      <div className="auth-right">

        {/* Mobile-only header */}
        <div className="auth-mobile-header">
          <div className="auth-logo-wrap">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M12 2C6.477 2 2 6.163 2 11.333c0 2.742 1.2 5.21 3.12 6.942L4 22l4.547-2.274A11.23 11.23 0 0 0 12 20.667c5.523 0 10-4.164 10-9.334C22 6.163 17.523 2 12 2Z" />
            </svg>
            <span className="auth-app-name">Rchat.ai</span>
          </div>
        </div>

        <div className="auth-form-wrap">
          <h1 className="auth-heading">Welcome back</h1>
          <p className="auth-subheading">Sign in to continue</p>

          {justRegistered && (
            <div className="auth-success">
              Account created! Please log in.
            </div>
          )}

          {error && (
            <div className="auth-error">{error}</div>
          )}

          <form onSubmit={handleLogin} noValidate>

            {/* Email / Username field */}
            <div className="auth-field">
              <div className="auth-input-wrap">
                <span className="auth-input-icon">
                  {/* User SVG icon */}
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <circle cx="12" cy="8" r="4" />
                    <path d="M4 20c0-4 3.582-7 8-7s8 3 8 7" />
                  </svg>
                </span>
                <input
                  className="auth-input"
                  type="text"
                  placeholder="Email or username"
                  value={emailOrUsername}
                  onChange={(e) => setEmailOrUsername(e.target.value)}
                  maxLength={100}
                  autoComplete="username"
                  required
                />
              </div>
            </div>

            {/* Password field */}
            <div className="auth-field">
              <div className="auth-input-wrap">
                <span className="auth-input-icon">
                  {/* Lock SVG icon */}
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                </span>
                <input
                  className="auth-input"
                  type={showPassword ? "text" : "password"}
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  maxLength={128}
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="auth-eye-btn"
                  onClick={() => setShowPassword((prev) => !prev)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    /* Eye-off SVG */
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    /* Eye SVG */
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M1 12S5 4 12 4s11 8 11 8-4 8-11 8S1 12 1 12Z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="auth-submit-btn"
              disabled={loading}
            >
              {loading ? (
                <span className="auth-submit-spinner" aria-hidden="true" />
              ) : (
                "Sign in"
              )}
            </button>

          </form>

          <p className="auth-footer-link">
            New to Rchat.ai?{" "}
            <Link to="/register">Create an account</Link>
          </p>
        </div>
      </div>

    </div>
  );
}
