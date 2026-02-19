import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { FaSun, FaMoon, FaUser } from "react-icons/fa";
import { useAuth } from "../context/AuthContext";
import ProfileModal from "./ProfileModal";

const API_BASE = "http://localhost:8000";

export default function Navbar() {
  const [theme, setTheme] = useState("dark");
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const [showDropdown, setShowDropdown] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme") || "dark";
    setTheme(savedTheme);
    document.body.className = savedTheme + "-theme";
  }, []);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    document.body.className = newTheme + "-theme";
    localStorage.setItem("theme", newTheme);
  };

  const handleLogout = () => {
    setShowDropdown(false);
    logout();
    navigate("/login");
  };

  const handleOpenProfile = () => {
    setShowDropdown(false);
    setShowProfile(true);
  };

  const initials = user?.display_name
    ? user.display_name.charAt(0).toUpperCase()
    : user?.username
      ? user.username.charAt(0).toUpperCase()
      : "?";

  const avatarSrc = user?.avatar_url ? `${API_BASE}${user.avatar_url}` : null;

  return (
    <>
      <nav className="navbar navbar-expand-lg navbar-custom px-4 py-3 shadow-sm">
        <a className="navbar-brand fw-bold fs-3" href="/">
          <svg width="28" height="28" viewBox="0 0 32 32" style={{ marginRight: 6, verticalAlign: "middle", marginTop: -4 }}>
            <defs>
              <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#6C5CE7" />
                <stop offset="100%" stopColor="#A29BFE" />
              </linearGradient>
            </defs>
            <rect x="2" y="4" width="28" height="20" rx="10" fill="url(#logoGrad)" />
            <polygon points="8,24 14,24 8,30" fill="url(#logoGrad)" />
            <circle cx="10" cy="14" r="2.2" fill="white" />
            <circle cx="16" cy="14" r="2.2" fill="white" />
            <circle cx="22" cy="14" r="2.2" fill="white" />
          </svg>
          Rchat<span className="brand-dot-ai">.ai</span>
        </a>

        <div className="ms-auto d-flex align-items-center gap-2">
          <button onClick={toggleTheme} className="btn btn-outline-secondary" style={{ border: "none" }}>
            {theme === "dark" ? (
              <FaSun size={18} color="#FDCB6E" />
            ) : (
              <FaMoon size={18} color="#6C5CE7" />
            )}
          </button>

          {isAuthenticated && (
            <div ref={dropdownRef} style={{ position: "relative" }}>
              <div
                className="profile-trigger"
                onClick={() => setShowDropdown(!showDropdown)}
                title="Profile"
              >
                {avatarSrc ? (
                  <img src={avatarSrc} alt="avatar" />
                ) : (
                  initials
                )}
              </div>

              {showDropdown && (
                <div className="profile-dropdown">
                  <div className="profile-dropdown-header">
                    <div className="profile-trigger" style={{ width: 40, height: 40, fontSize: "0.9rem", cursor: "default", border: "none" }}>
                      {avatarSrc ? (
                        <img src={avatarSrc} alt="avatar" />
                      ) : (
                        initials
                      )}
                    </div>
                    <div>
                      <div className="profile-dropdown-name">
                        {user?.display_name || user?.username}
                      </div>
                      <div className="profile-dropdown-username">
                        @{user?.username}
                      </div>
                    </div>
                  </div>
                  <button className="profile-dropdown-item" onClick={handleOpenProfile}>
                    <FaUser size={14} style={{ opacity: 0.6 }} />
                    My Profile
                  </button>
                  <div className="profile-dropdown-divider" />
                  <button className="profile-dropdown-item danger" onClick={handleLogout}>
                    Logout
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </nav>

      {showProfile && <ProfileModal onClose={() => setShowProfile(false)} />}
    </>
  );
}
