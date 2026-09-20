import React, { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import { supabase } from "../supabase";

const API_URL = "http://127.0.0.1:8000";

// Global fetch interceptor to automatically attach Bearer token to all backend API calls
if (typeof window !== "undefined") {
  const originalFetch = window.fetch;
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const urlStr = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
    if (urlStr.startsWith(API_URL)) {
      const token = sessionStorage.getItem("bhusync_auth_token");
      if (token) {
        init = init || {};
        const headers = new Headers(init.headers || {});
        if (!headers.has("Authorization")) {
          headers.set("Authorization", `Bearer ${token}`);
        }
        init.headers = headers;
      }
    }
    return originalFetch(input, init);
  };
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: "PLATFORM_ADMIN" | "DEPARTMENT_ADMIN" | "OFFICER" | "VIEWER" | string;
  organization_id?: string;
  organization_name?: string;
  organization_code?: string;
  department?: string;
  is_active: boolean;
  permissions: string[];
}

export interface AuthContextType {
  user: { id: string; email: string } | null;
  profile: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password?: string) => Promise<boolean>;
  logout: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  authFetch: (url: string, options?: RequestInit) => Promise<Response>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<{ id: string; email: string } | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize session on mount
  useEffect(() => {
    const initSession = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // 1. Check stored token in sessionStorage
        const storedToken = sessionStorage.getItem("bhusync_auth_token");

        if (storedToken) {
          try {
            const res = await fetch(`${API_URL}/auth/me`, {
              headers: { Authorization: `Bearer ${storedToken}` },
            });
            if (res.ok) {
              const prof: UserProfile = await res.json();
              setToken(storedToken);
              setUser({ id: prof.id, email: prof.email });
              setProfile(prof);
              setIsLoading(false);
              return;
            }
          } catch {
            // Ignore and fall through to Supabase check
          }
        }

        // 2. Check Supabase Auth session
        const { data } = await supabase.auth.getSession();
        if (data?.session?.access_token) {
          const sbToken = data.session.access_token;
          const res = await fetch(`${API_URL}/auth/me`, {
            headers: { Authorization: `Bearer ${sbToken}` },
          });
          if (res.ok) {
            const prof: UserProfile = await res.json();
            setToken(sbToken);
            setUser({ id: prof.id, email: prof.email });
            setProfile(prof);
            sessionStorage.setItem("bhusync_auth_token", sbToken);
            setIsLoading(false);
            return;
          }
        }

        // Unauthenticated
        sessionStorage.removeItem("bhusync_auth_token");
        setToken(null);
        setUser(null);
        setProfile(null);
      } catch (err: any) {
        console.error("Session verification error:", err);
      } finally {
        setIsLoading(false);
      }
    };

    initSession();

    // Listen to Supabase auth state changes
    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (event === "SIGNED_OUT" || !session) {
          sessionStorage.removeItem("bhusync_auth_token");
          setToken(null);
          setUser(null);
          setProfile(null);
        } else if (event === "SIGNED_IN" && session.access_token) {
          try {
            const res = await fetch(`${API_URL}/auth/me`, {
              headers: { Authorization: `Bearer ${session.access_token}` },
            });
            if (res.ok) {
              const prof: UserProfile = await res.json();
              setToken(session.access_token);
              setUser({ id: prof.id, email: prof.email });
              setProfile(prof);
              sessionStorage.setItem("bhusync_auth_token", session.access_token);
            }
          } catch (e) {
            console.error("Auth state change error:", e);
          }
        }
      }
    );

    return () => {
      authListener?.subscription.unsubscribe();
    };
  }, []);

  const login = async (email: string, password: string = "Test@12345"): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const errMsg = errData.detail || "Authentication failed. Invalid email or password.";
        setError(errMsg);
        setIsLoading(false);
        return false;
      }

      const data = await res.json();
      setToken(data.access_token);
      setUser(data.user);
      setProfile(data.profile);
      sessionStorage.setItem("bhusync_auth_token", data.access_token);
      setIsLoading(false);
      return true;
    } catch (err: any) {
      setError(err.message || "Network error. Unable to reach authentication server.");
      setIsLoading(false);
      return false;
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      if (token) {
        await fetch(`${API_URL}/auth/logout`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        }).catch(() => {});
      }
      await supabase.auth.signOut().catch(() => {});
    } finally {
      sessionStorage.removeItem("bhusync_auth_token");
      setToken(null);
      setUser(null);
      setProfile(null);
      setIsLoading(false);
    }
  };

  const hasPermission = (permission: string): boolean => {
    if (!profile) return false;
    if (profile.role === "PLATFORM_ADMIN") return true;
    return profile.permissions?.includes(permission) ?? false;
  };

  const hasRole = (role: string): boolean => {
    if (!profile) return false;
    if (profile.role === "PLATFORM_ADMIN") return true;
    return profile.role === role;
  };

  const authFetch = async (url: string, options: RequestInit = {}): Promise<Response> => {
    const headers = new Headers(options.headers || {});
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    return fetch(url, { ...options, headers });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        token,
        isLoading,
        error,
        login,
        logout,
        hasPermission,
        hasRole,
        authFetch,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
