import { useState } from "react";

export default function Login() {
  const [emailOrUsername, setEmailOrUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = (e) => {
    e.preventDefault();
    setError("");

    if (!emailOrUsername || !password) {
      setError("All fields are required");
      return;
    }

    console.log("Login:", emailOrUsername, password);
  };

  return (
    <div className="full-center container">

      <div className="login-card">

        <h2 className="text-center fw-bold mb-4">Login</h2>

        {error && (
          <div className="alert alert-danger text-center py-2">{error}</div>
        )}

        <form onSubmit={handleLogin}>

          <div className="mb-3">
            <label className="form-label fw-semibold">Email or Username</label>
            <input
              type="text"
              className="form-control"
              placeholder="Enter your email or username"
              value={emailOrUsername}
              onChange={(e) => setEmailOrUsername(e.target.value)}
            />
          </div>

          <div className="mb-3">
            <label className="form-label fw-semibold">Password</label>
            <input
              type="password"
              className="form-control"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button className="btn btn-primary w-100 py-2 fw-semibold">
            Login
          </button>
        </form>

        <p className="text-center mt-3">
          New to Rchat.ai?{" "}
          <a href="/register" className="text-primary fw-semibold">
            Create an account
          </a>
        </p>
      </div>
    </div>
  );
}