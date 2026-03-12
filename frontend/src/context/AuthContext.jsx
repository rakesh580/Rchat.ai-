import { createContext, useContext, useState, useEffect, useRef } from "react";
import { api } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // Token kept in memory only (never localStorage) to prevent XSS theft
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const initialLoad = useRef(true);

  // On mount, try to restore session via httpOnly cookie
  useEffect(() => {
    if (initialLoad.current) {
      initialLoad.current = false;
      api("/users/me")
        .then((data) => {
          setUser(data);
          setLoading(false);
        })
        .catch(() => {
          setToken(null);
          setUser(null);
          setLoading(false);
        });
      return;
    }

    if (token) {
      api("/users/me", { token })
        .then((data) => {
          setUser(data);
          setLoading(false);
        })
        .catch(() => {
          setToken(null);
          setUser(null);
          setLoading(false);
        });
    } else {
      setUser(null);
      setLoading(false);
    }
  }, [token]);

  const login = (newToken) => setToken(newToken);
  const logout = async () => {
    try { await api("/auth/logout", { method: "POST", token }); } catch { /* ignore */ }
    setToken(null);
    setUser(null);
  };
  const refreshUser = async () => {
    try {
      const data = await api("/users/me", { token });
      setUser(data);
    } catch { /* ignore */ }
  };
  const isAuthenticated = !!user;

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAuthenticated, loading, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
