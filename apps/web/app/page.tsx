"use client";

import { useState } from "react";
import type { CSSProperties } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

type AuthMode = "login" | "register";

type AuthUser = {
  user_id: string;
  email: string;
  full_name?: string | null;
};

export default function Home() {
  const [healthResult, setHealthResult] = useState("아직 확인 전");
  const [healthLoading, setHealthLoading] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [authLoading, setAuthLoading] = useState(false);
  const [authMessage, setAuthMessage] = useState("로그인 상태를 확인해 주세요.");
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerName, setRegisterName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerPasswordConfirm, setRegisterPasswordConfirm] = useState("");
  const [registerAgreements, setRegisterAgreements] = useState(false);

  const checkApiHealth = async () => {
    setHealthLoading(true);
    try {
      const response = await fetch(`${API_BASE}/health`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = (await response.json()) as { status?: string };
      setHealthResult(`API 연결 성공: ${data.status ?? "unknown"}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "unknown error";
      setHealthResult(`API 연결 실패: ${message}`);
    } finally {
      setHealthLoading(false);
    }
  };

  const fetchMe = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/me`, {
        method: "GET",
        credentials: "include",
      });
      if (!response.ok) {
        setCurrentUser(null);
        setAuthMessage("현재 로그인되어 있지 않습니다.");
        return;
      }
      const data = (await response.json()) as {
        id: string;
        email: string;
        full_name?: string | null;
      };
      setCurrentUser({
        user_id: data.id,
        email: data.email,
        full_name: data.full_name,
      });
      setAuthMessage("로그인 상태입니다.");
    } catch {
      setAuthMessage("로그인 상태 확인에 실패했습니다.");
    }
  };

  const submitLogin = async () => {
    if (!loginEmail || !loginPassword) {
      setAuthMessage("이메일과 비밀번호를 입력해 주세요.");
      return;
    }
    setAuthLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          email: loginEmail,
          password: loginPassword,
        }),
      });
      const data = (await response.json()) as AuthUser | Record<string, unknown>;
      if (!response.ok) {
        throw new Error(extractErrorMessage(data, "로그인에 실패했습니다."));
      }
      setCurrentUser(data as AuthUser);
      setAuthMessage("로그인 성공");
    } catch (error) {
      const message = error instanceof Error ? error.message : "로그인 실패";
      setAuthMessage(message);
      setCurrentUser(null);
    } finally {
      setAuthLoading(false);
    }
  };

  const submitRegister = async () => {
    if (!registerName || !registerEmail || !registerPassword || !registerPasswordConfirm) {
      setAuthMessage("닉네임, 이메일, 비밀번호, 비밀번호 확인을 모두 입력해 주세요.");
      return;
    }
    if (!/^[A-Za-z0-9가-힣]{2,20}$/.test(registerName)) {
      setAuthMessage("닉네임은 2~20자의 한글/영문/숫자만 사용할 수 있습니다.");
      return;
    }
    if (!/^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,16}$/.test(registerPassword)) {
      setAuthMessage("비밀번호는 8~16자, 영문/숫자/특수문자를 모두 포함해야 합니다.");
      return;
    }
    if (registerPassword !== registerPasswordConfirm) {
      setAuthMessage("비밀번호 확인이 일치하지 않습니다.");
      return;
    }
    if (!registerAgreements) {
      setAuthMessage("필수 약관 동의가 필요합니다.");
      return;
    }
    setAuthLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          email: registerEmail,
          password: registerPassword,
          confirm_password: registerPasswordConfirm,
          full_name: registerName,
          agreements: registerAgreements,
        }),
      });
      const data = (await response.json()) as AuthUser | Record<string, unknown>;
      if (!response.ok) {
        throw new Error(extractErrorMessage(data, "회원가입에 실패했습니다."));
      }
      setAuthMessage("회원가입 성공. 로그인 탭에서 로그인해 주세요.");
      setAuthMode("login");
      setLoginEmail((data as AuthUser).email);
      setRegisterName("");
      setRegisterEmail("");
      setRegisterPassword("");
      setRegisterPasswordConfirm("");
      setRegisterAgreements(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : "회원가입 실패";
      setAuthMessage(message);
    } finally {
      setAuthLoading(false);
    }
  };

  const logout = async () => {
    setAuthLoading(true);
    try {
      await fetch(`${API_BASE}/api/v1/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
      setCurrentUser(null);
      setAuthMessage("로그아웃되었습니다.");
    } finally {
      setAuthLoading(false);
    }
  };

  return (
    <main style={{ maxWidth: 980, margin: "64px auto", padding: "0 20px" }}>
      <section
        style={{
          background: "#fffdfa",
          borderRadius: 20,
          padding: 30,
          border: "1px solid #ece4d8",
          boxShadow: "0 10px 30px rgba(15,23,42,0.08)",
        }}
      >
        <h1 style={{ marginTop: 0, marginBottom: 8 }}>autoLV</h1>
        <p style={{ marginTop: 0, color: "#475569", marginBottom: 20 }}>
          개별공시지가 서비스 인증 MVP 화면입니다. 밝은 톤 기준으로 사용성이 단순한 구조를 우선 적용했습니다.
        </p>

        <div style={{ display: "grid", gap: 20, gridTemplateColumns: "1fr 1fr" }}>
          <article
            style={{
              border: "1px solid #e7dfd3",
              borderRadius: 14,
              padding: 18,
              background: "#fff",
            }}
          >
            <h2 style={{ margin: "0 0 12px 0", fontSize: 20 }}>API 상태 확인</h2>
            <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
              <button
                onClick={checkApiHealth}
                disabled={healthLoading}
                style={{
                  border: "none",
                  borderRadius: 10,
                  padding: "10px 14px",
                  cursor: "pointer",
                  background: "#2563eb",
                  color: "white",
                  fontWeight: 700,
                }}
              >
                {healthLoading ? "확인 중..." : "API 헬스체크"}
              </button>
              <button
                onClick={fetchMe}
                style={{
                  border: "1px solid #cbd5e1",
                  borderRadius: 10,
                  padding: "10px 14px",
                  cursor: "pointer",
                  background: "#f8fafc",
                  color: "#1e293b",
                  fontWeight: 600,
                }}
              >
                로그인 상태 확인
              </button>
            </div>
            <p style={{ marginBottom: 6 }}>
              <code style={{ background: "#f1f5f9", padding: "4px 8px", borderRadius: 8 }}>
                {API_BASE}/health
              </code>
            </p>
            <p style={{ margin: 0, fontWeight: 600 }}>{healthResult}</p>
          </article>

          <article
            style={{
              border: "1px solid #e7dfd3",
              borderRadius: 14,
              padding: 18,
              background: "#fff",
            }}
          >
            <h2 style={{ margin: "0 0 12px 0", fontSize: 20 }}>계정</h2>
            <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
              <button
                onClick={() => setAuthMode("login")}
                style={{
                  border: "none",
                  borderRadius: 8,
                  padding: "8px 12px",
                  background: authMode === "login" ? "#0f172a" : "#e2e8f0",
                  color: authMode === "login" ? "#fff" : "#334155",
                  cursor: "pointer",
                }}
              >
                로그인
              </button>
              <button
                onClick={() => setAuthMode("register")}
                style={{
                  border: "none",
                  borderRadius: 8,
                  padding: "8px 12px",
                  background: authMode === "register" ? "#0f172a" : "#e2e8f0",
                  color: authMode === "register" ? "#fff" : "#334155",
                  cursor: "pointer",
                }}
              >
                회원가입
              </button>
            </div>

            {authMode === "login" ? (
              <div style={{ display: "grid", gap: 10 }}>
                <input
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  placeholder="이메일"
                  type="email"
                  style={inputStyle}
                />
                <input
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="비밀번호"
                  type="password"
                  style={inputStyle}
                />
                <button onClick={submitLogin} disabled={authLoading} style={primaryButtonStyle}>
                  {authLoading ? "처리 중..." : "로그인"}
                </button>
                <div style={{ display: "flex", gap: 10 }}>
                  <button
                    type="button"
                    onClick={() => setAuthMessage("아이디 찾기 기능은 준비 중입니다.")}
                    style={ghostButtonStyle}
                  >
                    아이디 찾기
                  </button>
                  <button
                    type="button"
                    onClick={() => setAuthMessage("비밀번호 찾기 기능은 준비 중입니다.")}
                    style={ghostButtonStyle}
                  >
                    비밀번호 찾기
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ display: "grid", gap: 10 }}>
                <input
                  value={registerName}
                  onChange={(e) => setRegisterName(e.target.value)}
                  placeholder="닉네임 (2~20자, 한글/영문/숫자)"
                  type="text"
                  style={inputStyle}
                />
                <input
                  value={registerEmail}
                  onChange={(e) => setRegisterEmail(e.target.value)}
                  placeholder="이메일"
                  type="email"
                  style={inputStyle}
                />
                <input
                  value={registerPassword}
                  onChange={(e) => setRegisterPassword(e.target.value)}
                  placeholder="비밀번호 (8~16자, 영문/숫자/특수문자)"
                  type="password"
                  style={inputStyle}
                />
                <input
                  value={registerPasswordConfirm}
                  onChange={(e) => setRegisterPasswordConfirm(e.target.value)}
                  placeholder="비밀번호 확인"
                  type="password"
                  style={inputStyle}
                />
                <label style={{ display: "flex", gap: 8, alignItems: "center", color: "#334155", fontSize: 14 }}>
                  <input
                    type="checkbox"
                    checked={registerAgreements}
                    onChange={(e) => setRegisterAgreements(e.target.checked)}
                  />
                  [필수] 서비스 이용약관 및 개인정보 처리방침에 동의합니다.
                </label>
                <button onClick={submitRegister} disabled={authLoading} style={primaryButtonStyle}>
                  {authLoading ? "처리 중..." : "회원가입"}
                </button>
              </div>
            )}

            <p style={{ marginTop: 12, marginBottom: 6, color: "#1e293b", fontWeight: 600 }}>{authMessage}</p>
            {currentUser ? (
              <div style={{ background: "#f8fafc", borderRadius: 10, padding: 10 }}>
                <p style={{ margin: 0 }}>로그인 사용자: {currentUser.full_name || currentUser.email}</p>
                <button onClick={logout} style={{ ...secondaryButtonStyle, marginTop: 10 }}>
                  로그아웃
                </button>
              </div>
            ) : null}
          </article>
        </div>
      </section>
    </main>
  );
}

const inputStyle: CSSProperties = {
  border: "1px solid #d6d3d1",
  borderRadius: 8,
  padding: "10px 12px",
  fontSize: 14,
  outline: "none",
};

const primaryButtonStyle: CSSProperties = {
  border: "none",
  borderRadius: 10,
  padding: "10px 14px",
  cursor: "pointer",
  background: "#2563eb",
  color: "white",
  fontWeight: 700,
};

const secondaryButtonStyle: CSSProperties = {
  border: "1px solid #cbd5e1",
  borderRadius: 8,
  padding: "8px 12px",
  cursor: "pointer",
  background: "white",
  color: "#1e293b",
  fontWeight: 600,
};

const ghostButtonStyle: CSSProperties = {
  border: "none",
  borderRadius: 8,
  padding: "0",
  cursor: "pointer",
  background: "transparent",
  color: "#1d4ed8",
  fontWeight: 600,
  textDecoration: "underline",
  textUnderlineOffset: "2px",
  textAlign: "left",
};

function extractErrorMessage(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== "object") return fallback;

  const detail = (payload as { detail?: unknown }).detail;
  if (!detail) return fallback;

  if (typeof detail === "string") return detail;

  if (typeof detail === "object" && detail !== null) {
    const message = (detail as { message?: unknown }).message;
    if (typeof message === "string" && message.trim()) return message;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: unknown };
    if (first && typeof first.msg === "string" && first.msg.trim()) return first.msg;
  }

  return fallback;
}
