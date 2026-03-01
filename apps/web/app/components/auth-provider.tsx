"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

import type { AuthMode, AuthUser } from "@/app/lib/types";

const DEFAULT_API_BASE = "http://127.0.0.1:8000";

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  authLoading: boolean;
  authOpen: boolean;
  authMode: AuthMode;
  authMessage: string;
  openAuth: (mode: AuthMode) => void;
  closeAuth: () => void;
  setAuthMode: (mode: AuthMode) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: {
    full_name: string;
    email: string;
    password: string;
    confirm_password: string;
    agreements: boolean;
  }) => Promise<void>;
  logout: () => Promise<void>;
  setAuthMessage: (message: string) => void;
  refreshMe: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [authLoading, setAuthLoading] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [authMessage, setAuthMessage] = useState("로그인 후 파일 조회 기능을 사용할 수 있습니다.");

  useEffect(() => {
    void refreshMe();
  }, []);

  const refreshMe = async () => {
    try {
      const res = await authFetch("/api/v1/auth/me", { method: "GET" });
      if (!res.ok) {
        setUser(null);
      } else {
        const data = (await res.json()) as AuthUser;
        setUser(data);
      }
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const openAuth = (mode: AuthMode) => {
    setAuthMode(mode);
    setAuthOpen(true);
  };

  const closeAuth = () => setAuthOpen(false);

  const login = async (email: string, password: string) => {
    if (!email || !password) throw new Error("이메일과 비밀번호를 입력해 주세요.");
    setAuthLoading(true);
    try {
      const res = await authFetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const payload = (await res.json()) as AuthUser | { detail?: unknown };
      if (!res.ok) throw new Error(extractError(payload, "로그인에 실패했습니다."));
      setUser(payload as AuthUser);
      setAuthMessage("로그인되었습니다.");
      setAuthOpen(false);
    } finally {
      setAuthLoading(false);
    }
  };

  const register = async (payload: {
    full_name: string;
    email: string;
    password: string;
    confirm_password: string;
    agreements: boolean;
  }) => {
    setAuthLoading(true);
    try {
      const res = await authFetch("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = (await res.json()) as { detail?: unknown };
      if (!res.ok) throw new Error(extractError(body, "회원가입에 실패했습니다."));
      setAuthMessage("회원가입이 완료되었습니다. 로그인해 주세요.");
      setAuthMode("login");
    } finally {
      setAuthLoading(false);
    }
  };

  const logout = async () => {
    setAuthLoading(true);
    let remoteSuccess = false;
    try {
      const res = await authFetch("/api/v1/auth/logout", { method: "POST" });
      remoteSuccess = res.ok;
    } catch {
      remoteSuccess = false;
    } finally {
      setUser(null);
      setAuthMode("login");
      setAuthOpen(false);
      setAuthMessage(remoteSuccess ? "로그아웃되었습니다." : "서버 연결 문제로 로컬 로그아웃 처리되었습니다.");
      setAuthLoading(false);
    }
  };

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      authLoading,
      authOpen,
      authMode,
      authMessage,
      openAuth,
      closeAuth,
      setAuthMode,
      login,
      register,
      logout,
      setAuthMessage,
      refreshMe,
    }),
    [user, loading, authLoading, authOpen, authMode, authMessage]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth는 AuthProvider 내부에서 사용해야 합니다.");
  return ctx;
}

function extractError(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== "object") return fallback;
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: unknown };
    if (first && typeof first.msg === "string") return first.msg;
  }
  if (detail && typeof detail === "object") {
    const message = (detail as { message?: unknown }).message;
    if (typeof message === "string") return message;
  }
  return fallback;
}

function normalizeBase(base: string): string {
  return base.replace(/\/+$/, "");
}

function resolveApiBases(): string[] {
  const envBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  const bases: string[] = [];

  if (envBase) bases.push(normalizeBase(envBase));

  if (typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "https:" : "http:";
    const hostBase = `${protocol}//${window.location.hostname}:8000`;
    bases.push(normalizeBase(hostBase));
    bases.push("http://localhost:8000");
  }

  bases.push(DEFAULT_API_BASE);
  return Array.from(new Set(bases));
}

async function authFetch(path: string, init: RequestInit): Promise<Response> {
  const bases = resolveApiBases();
  let lastError: unknown = null;

  for (const base of bases) {
    try {
      return await fetch(`${base}${path}`, {
        ...init,
        credentials: "include",
      });
    } catch (error) {
      lastError = error;
    }
  }

  if (lastError instanceof Error) throw lastError;
  throw new Error("API 연결 실패");
}
