import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Register() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="full-center container">
      <div className="login-card">
        <h2 className="text-center fw-bold mb-4">Create Account</h2>

        {error && (
          <div className="alert alert-danger text-center py-2">{error}</div>
        )}

        <form onSubmit={handleRegister}>
          <div className="mb-3">
            <label className="form-label fw-semibold">Email</label>
            <input
              type="email"
              className="form-control"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              maxLength={100}
              required
            />
          </div>

          <div className="mb-3">
            <label className="form-label fw-semibold">Username</label>
            <input
              type="text"
              className="form-control"
              placeholder="Choose a username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              maxLength={30}
              required
            />
          </div>

          <div className="mb-3">
            <label className="form-label fw-semibold">Password</label>
            <input
              type="password"
              className="form-control"
              placeholder="Create a password (min 8 characters)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              maxLength={128}
              required
            />
          </div>

          <button
            className="btn btn-primary w-100 py-2 fw-semibold"
            disabled={loading}
          >
            {loading ? "Registering..." : "Register"}
          </button>
        </form>

        <p className="text-center mt-3">
          Already have an account?{" "}
          <Link to="/login" className="text-primary fw-semibold">
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}
