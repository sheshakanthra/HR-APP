import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { apiFetch, tokenStore, API_BASE } from "./api";
import type { MeOut, RBACRole, TokenResponse } from "./types";

interface AuthState {
  me: MeOut | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (min: RBACRole) => boolean;
}

const ROLE_RANK: Record<RBACRole, number> = {
  employee: 0,
  manager: 1,
  hr_admin: 2,
  super_admin: 3,
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<MeOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function bootstrap() {
      if (tokenStore.access) {
        try {
          setMe(await apiFetch<MeOut>("/auth/me"));
        } catch {
          tokenStore.clear();
        }
      }
      setLoading(false);
    }
    bootstrap();
  }, []);

  async function login(email: string, password: string) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: "Login failed" }));
      throw new Error(body.detail ?? "Login failed");
    }
    const data: TokenResponse = await res.json();
    tokenStore.set(data.access_token, data.refresh_token);
    setMe(await apiFetch<MeOut>("/auth/me"));
  }

  function logout() {
    tokenStore.clear();
    setMe(null);
  }

  function hasRole(min: RBACRole) {
    if (!me) return false;
    return ROLE_RANK[me.user.rbac_role] >= ROLE_RANK[min];
  }

  return (
    <AuthContext.Provider value={{ me, loading, login, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
