import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";

function computePasswordStrength(pwd) {
  if (!pwd) return 0;
  if (pwd.length < 8) return 1;
  const hasNumber = /[0-9]/.test(pwd);
  const hasSpecial = /[^a-zA-Z0-9]/.test(pwd);
  const hasUpper = /[A-Z]/.test(pwd);
  if (hasNumber && hasSpecial && hasUpper) return 4;
  if (hasNumber || hasSpecial) return 3;
  return 2;
}

function validateUsername(name) {
  if (!name) return null;
  if (name.length < 3 || name.length > 30) return false;
  if (!/^[a-zA-Z0-9_]+$/.test(name)) return false;
  return true;
}

const strengthLabel = ["", "Weak", "Fair", "Good", "Strong"];

export default function Register() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [usernameValid, setUsernameValid] = useState(null);
  const [passwordStrength, setPasswordStrength] = useState(0);

  const handleUsernameChange = (e) => {
    const val = e.target.value;
    setUsername(val);
    setUsernameValid(val.length === 0 ? null : validateUsername(val));
  };

  const handlePasswordChange = (e) => {
    const val = e.target.value;
    setPassword(val);
    setPasswordStrength(computePasswordStrength(val));
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");

    if (!email || !username || !password) {
      setError("All fields are required");
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError("Please enter a valid email address");
      return;
    }

    if (username.length < 3 || username.length > 30) {
      setError("Username must be between 3 and 30 characters");
      return;
    }

    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      setError("Username can only contain letters, numbers, and underscores");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setLoading(true);
    try {
      await api("/auth/register", {
        method: "POST",
        body: { email, username, password },
      });
      navigate("/login", { state: { registered: true } });
    } catch (err) {
      const msg = err.message || "";
      if (msg.includes("unavailable") || msg.includes("already")) {
        setError("Email or username is already taken. Please choose different ones.");
      } else if (msg.includes("Rate limit") || msg.includes("429")) {
        setError("Too many registration attempts. Please wait a minute.");
      } else if (msg.includes("fetch") || msg.includes("network") || msg.includes("Failed")) {
        setError("Unable to connect to the server. Please check your connection.");
      } else if (msg.includes("Password must") || msg.includes("Username")) {
        setError(msg);
      } else {
        setError("Registration failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      {/* ── Left brand panel ── */}
      <div className="auth-left">
        <div className="auth-logo-wrap">
          <svg width="44" height="44" viewBox="0 0 44 44" fill="none" aria-hidden="true">
            <rect width="44" height="44" rx="14" fill="url(#rg-grad)" />
            <path
              d="M10 15c0-2.21 1.79-4 4-4h16c2.21 0 4 1.79 4 4v10c0 2.21-1.79 4-4 4h-6l-6 5v-5h-4c-2.21 0-4-1.79-4-4V15z"
              fill="white"
              fillOpacity="0.92"
            />
            <circle cx="17" cy="20" r="2" fill="url(#rg-grad)" />
            <circle cx="22" cy="20" r="2" fill="url(#rg-grad)" />
            <circle cx="27" cy="20" r="2" fill="url(#rg-grad)" />
            <defs>
              <linearGradient id="rg-grad" x1="0" y1="0" x2="44" y2="44" gradientUnits="userSpaceOnUse">
                <stop stopColor="#6C5CE7" />
                <stop offset="1" stopColor="#A29BFE" />
              </linearGradient>
            </defs>
          </svg>
          <span className="auth-app-name">Rchat.ai</span>
        </div>

        <p className="auth-tagline">Join the AI-powered conversation</p>

        <ul className="auth-features">
          <li className="auth-feature-pill">✦ Free forever, no credit card</li>
          <li className="auth-feature-pill">⚡ Set up in under a minute</li>
          <li className="auth-feature-pill">🤖 AI agent activated on signup</li>
          <li className="auth-feature-pill">🔒 End-to-end secured</li>
        </ul>
      </div>

      {/* ── Right form panel ── */}
      <div className="auth-right">
        {/* Mobile-only header */}
        <div className="auth-mobile-header">
          <svg width="28" height="28" viewBox="0 0 44 44" fill="none" aria-hidden="true">
            <rect width="44" height="44" rx="14" fill="url(#rg-mob)" />
            <path
              d="M10 15c0-2.21 1.79-4 4-4h16c2.21 0 4 1.79 4 4v10c0 2.21-1.79 4-4 4h-6l-6 5v-5h-4c-2.21 0-4-1.79-4-4V15z"
              fill="white"
              fillOpacity="0.92"
            />
            <defs>
              <linearGradient id="rg-mob" x1="0" y1="0" x2="44" y2="44" gradientUnits="userSpaceOnUse">
                <stop stopColor="#6C5CE7" />
                <stop offset="1" stopColor="#A29BFE" />
              </linearGradient>
            </defs>
          </svg>
          <span>Rchat.ai</span>
        </div>

        <div className="auth-form-wrap">
          <h2 className="auth-heading">Create your account</h2>
          <p className="auth-subheading">Start chatting with AI superpowers</p>

          {error && <div className="auth-error">{error}</div>}

          <form onSubmit={handleRegister} noValidate>
            {/* Email */}
            <div className="auth-field">
              <div className="auth-input-wrap">
                <span className="auth-input-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <rect x="2" y="4" width="20" height="16" rx="2" />
                    <polyline points="2,4 12,13 22,4" />
                  </svg>
                </span>
                <input
                  type="email"
                  className="auth-input"
                  placeholder="Email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  maxLength={100}
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            {/* Username */}
            <div className="auth-field">
              <div className="auth-input-wrap">
                <span className="auth-input-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                </span>
                <input
                  type="text"
                  className="auth-input"
                  placeholder="Username (3–30 chars, letters/numbers/_)"
                  value={username}
                  onChange={handleUsernameChange}
                  maxLength={30}
                  autoComplete="username"
                  required
                />
              </div>
              {usernameValid === true && (
                <p className="auth-field-hint valid">Username looks good</p>
              )}
              {usernameValid === false && (
                <p className="auth-field-hint invalid">
                  3–30 characters, letters, numbers and underscores only
                </p>
              )}
            </div>

            {/* Password */}
            <div className="auth-field">
              <div className="auth-input-wrap">
                <span className="auth-input-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                </span>
                <input
                  type={showPassword ? "text" : "password"}
                  className="auth-input"
                  placeholder="Password (min 8 characters)"
                  value={password}
                  onChange={handlePasswordChange}
                  minLength={8}
                  maxLength={128}
                  autoComplete="new-password"
                  required
                />
                <button
                  type="button"
                  className="auth-eye-btn"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>

              {/* Strength bar — only render when user has typed */}
              {password.length > 0 && (
                <div className="auth-password-strength">
                  {[1, 2, 3, 4].map((seg) => (
                    <div
                      key={seg}
                      className={`auth-strength-seg${passwordStrength >= seg ? ` filled-${passwordStrength}` : ""}`}
                    />
                  ))}
                  <span className="auth-field-hint" style={{ marginTop: 0, marginLeft: 6 }}>
                    {strengthLabel[passwordStrength]}
                  </span>
                </div>
              )}
            </div>

            <button
              type="submit"
              className="auth-submit-btn"
              disabled={loading}
            >
              {loading ? (
                <span className="auth-submit-spinner" aria-label="Creating account…" />
              ) : (
                "Create account"
              )}
            </button>
          </form>

          <p className="auth-footer-link">
            Already have an account?{" "}
            <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
