import { useEffect, useState } from "react";
import { FaSun, FaMoon } from "react-icons/fa";

export default function Navbar() {
  const [theme, setTheme] = useState("dark");

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme") || "dark";
    setTheme(savedTheme);
    document.body.className = savedTheme + "-theme";
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    document.body.className = newTheme + "-theme";
    localStorage.setItem("theme", newTheme);
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-custom px-4 py-3 shadow-sm">
      <a className="navbar-brand fw-bold fs-3" href="/">
        Rchat<span className="text-primary">.ai</span>
      </a>

      <button onClick={toggleTheme} className="btn btn-outline-secondary ms-auto">
        {theme === "dark" ? (
          <FaSun size={20} color="#ffd43b" />
        ) : (
          <FaMoon size={20} />
        )}
      </button>
    </nav>
  );
}