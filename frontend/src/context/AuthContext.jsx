import { createContext, useContext, useState, useEffect, useRef, useCallback } from "react";
import { api } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const initialLoad = useRef(true);

  // On mount, try to restore session via httpOnly cookie
  // If successful, request a fresh token from the server
  useEffect(() => {
    if (initialLoad.current) {
      initialLoad.current = false;
      api("/auth/refresh", { method: "POST" })
        .then((data) => {
          if (data.access_token) {
            setToken(data.access_token);
            setUser(data.user);
          }
          setLoading(false);
        })
        .catch(() => {
          // Fallback: try /users/me with cookie
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
    } else if (!user) {
      setLoading(false);
    }
  }, [token]);

  const login = (newToken, userData = null) => {
    if (userData) {
      setToken(newToken);
      setUser(userData);
      setLoading(false);
    } else {
      setLoading(true);
      setToken(newToken);
    }
  };

  const logout = useCallback(async () => {
    try {
      await api("/auth/logout", { method: "POST", token });
    } catch {
      // ignore
    } finally {
      setToken(null);
      setUser(null);
    }
  }, [token]);

  const refreshUser = useCallback(async () => {
    try {
      const data = await api("/users/me", { token });
      setUser(data);
    } catch {
      // ignore
    }
  }, [token]);

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
