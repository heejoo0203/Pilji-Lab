"use client";

import type { FormEvent, MouseEvent } from "react";
import { useEffect, useState } from "react";

import { useAuth } from "@/app/components/auth-provider";

type AssistMode = "none" | "find-id" | "reset-password";

export function AuthModal() {
  const {
    authOpen,
    authMode,
    closeAuth,
    setAuthMode,
    setAuthMessage,
    authMessage,
    authLoading,
    login,
    register,
    sendRecoveryCode,
    findIdByCode,
    resetPasswordByCode,
  } = useAuth();

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  const [registerName, setRegisterName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerPasswordConfirm, setRegisterPasswordConfirm] = useState("");
  const [registerVerificationId, setRegisterVerificationId] = useState("");
  const [registerVerificationCode, setRegisterVerificationCode] = useState("");
  const [registerAgreements, setRegisterAgreements] = useState(false);

  const [findIdName, setFindIdName] = useState("");
  const [findIdEmail, setFindIdEmail] = useState("");
  const [findIdVerificationId, setFindIdVerificationId] = useState("");
  const [findIdCode, setFindIdCode] = useState("");

  const [resetEmail, setResetEmail] = useState("");
  const [resetVerificationId, setResetVerificationId] = useState("");
  const [resetCode, setResetCode] = useState("");
  const [resetNewPassword, setResetNewPassword] = useState("");
  const [resetConfirmPassword, setResetConfirmPassword] = useState("");

  const [assistMode, setAssistMode] = useState<AssistMode>("none");
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);
  const [showRegisterPasswordConfirm, setShowRegisterPasswordConfirm] = useState(false);
  const [showResetPassword, setShowResetPassword] = useState(false);
  const [showResetPasswordConfirm, setShowResetPasswordConfirm] = useState(false);
  const [backdropPressed, setBackdropPressed] = useState(false);

  useEffect(() => {
    if (!authOpen) return;
    setAssistMode("none");
  }, [authOpen, authMode]);

  useEffect(() => {
    setRegisterVerificationId("");
    setRegisterVerificationCode("");
  }, [registerEmail]);

  if (!authOpen) return null;

  const onOverlayMouseDown = (event: MouseEvent<HTMLDivElement>) => {
    setBackdropPressed(event.target === event.currentTarget);
  };

  const onOverlayMouseUp = (event: MouseEvent<HTMLDivElement>) => {
    const isBackdrop = event.target === event.currentTarget;
    if (backdropPressed && isBackdrop) {
      closeAuth();
    }
    setBackdropPressed(false);
  };

  const onLoginSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      await login(loginEmail, loginPassword);
    } catch (e) {
      setAuthMessage(e instanceof Error ? e.message : "로그인 실패");
    }
  };

  const onRegisterSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!registerVerificationId) {
      setAuthMessage("이메일 인증 코드를 먼저 발송해 주세요.");
      return;
    }
    try {
      await register({
        full_name: registerName,
        email: registerEmail,
        password: registerPassword,
        confirm_password: registerPasswordConfirm,
        agreements: registerAgreements,
        verification_id: registerVerificationId,
        verification_code: registerVerificationCode,
      });
    } catch (e) {
      setAuthMessage(e instanceof Error ? e.message : "회원가입 실패");
    }
  };

  const onSendSignupCode = async () => {
    if (!registerEmail.trim()) {
      setAuthMessage("이메일을 먼저 입력해 주세요.");
      return;
    }
    try {
      const result = await sendRecoveryCode({
        purpose: "signup",
        email: registerEmail.trim(),
      });
      setRegisterVerificationId(result.verification_id);
      if (result.debug_code) {
        setRegisterVerificationCode(result.debug_code);
      }
      setAuthMessage(result.debug_code ? `인증 코드 발송 완료(개발코드: ${result.debug_code})` : result.message);
    } catch (e) {
      setAuthMessage(e instanceof Error ? e.message : "인증 코드 발송 실패");
    }
  };

  const onSendFindIdCode = async () => {
    try {
      const result = await sendRecoveryCode({
        purpose: "find_id",
        email: findIdEmail.trim(),
        full_name: findIdName.trim(),
      });
      setFindIdVerificationId(result.verification_id);
      if (result.debug_code) {
        setFindIdCode(result.debug_code);
      }
      setAuthMessage(result.debug_code ? `인증 코드 발송 완료(개발코드: ${result.debug_code})` : result.message);
    } catch (e) {
      setAuthMessage(e instanceof Error ? e.message : "인증 코드 발송 실패");
    }
  };

  const onFindIdSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!findIdVerificationId) {
      setAuthMessage("인증 코드를 먼저 발송해 주세요.");
      return;
    }
    try {
      const result = await findIdByCode({
        verification_id: findIdVerificationId,
        code: findIdCode.trim(),
      });
      setAuthMessage(`가입된 아이디(이메일): ${result.email}`);
    } catch (e) {
      setAuthMessage(e instanceof Error ? e.message : "아이디 찾기 실패");
    }
  };

  const onSendResetCode = async () => {
    try {
      const result = await sendRecoveryCode({
        purpose: "reset_password",
        email: resetEmail.trim(),
      });
      setResetVerificationId(result.verification_id);
      if (result.debug_code) {
        setResetCode(result.debug_code);
      }
      setAuthMessage(result.debug_code ? `인증 코드 발송 완료(개발코드: ${result.debug_code})` : result.message);
    } catch (e) {
      setAuthMessage(e instanceof Error ? e.message : "인증 코드 발송 실패");
    }
  };

  const onResetSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!resetVerificationId) {
      setAuthMessage("인증 코드를 먼저 발송해 주세요.");
      return;
    }
    try {
      const message = await resetPasswordByCode({
        email: resetEmail.trim(),
        verification_id: resetVerificationId,
        code: resetCode.trim(),
        new_password: resetNewPassword,
        confirm_new_password: resetConfirmPassword,
      });
      setAuthMessage(message);
      setAssistMode("none");
      setAuthMode("login");
      setLoginEmail(resetEmail.trim());
      setResetNewPassword("");
      setResetConfirmPassword("");
      setResetCode("");
      setResetVerificationId("");
    } catch (e) {
      setAuthMessage(e instanceof Error ? e.message : "비밀번호 재설정 실패");
    }
  };

  const modalTitle =
    assistMode === "find-id" ? "아이디 찾기" : assistMode === "reset-password" ? "비밀번호 찾기" : authMode === "login" ? "로그인" : "회원가입";

  return (
    <div className="auth-overlay" onMouseDown={onOverlayMouseDown} onMouseUp={onOverlayMouseUp}>
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
        <div className="auth-modal-head">
          <h3>{modalTitle}</h3>
          <button onClick={closeAuth}>✕</button>
        </div>

        {assistMode === "none" ? (
          <div className="tab-row">
            <button className={`tab-chip ${authMode === "login" ? "on" : ""}`} onClick={() => setAuthMode("login")}>
              로그인
            </button>
            <button className={`tab-chip ${authMode === "register" ? "on" : ""}`} onClick={() => setAuthMode("register")}>
              회원가입
            </button>
          </div>
        ) : (
          <div className="tab-row">
            <button className="tab-chip on" onClick={() => setAssistMode("none")}>
              로그인으로 돌아가기
            </button>
          </div>
        )}

        {assistMode === "find-id" ? (
          <form className="auth-form-grid" onSubmit={(event) => void onFindIdSubmit(event)}>
            <input
              placeholder="닉네임"
              value={findIdName}
              onChange={(event) => setFindIdName(event.target.value)}
            />
            <input
              placeholder="가입 이메일"
              value={findIdEmail}
              onChange={(event) => setFindIdEmail(event.target.value)}
            />
            <div className="verification-row">
              <input
                placeholder="인증 코드 6자리"
                value={findIdCode}
                onChange={(event) => setFindIdCode(event.target.value)}
              />
              <button type="button" className="nav-item" onClick={() => void onSendFindIdCode()}>
                코드 발송
              </button>
            </div>
            <button type="submit" className="btn-primary" disabled={authLoading}>
              {authLoading ? "처리 중..." : "아이디 확인"}
            </button>
          </form>
        ) : null}

        {assistMode === "reset-password" ? (
          <form className="auth-form-grid" onSubmit={(event) => void onResetSubmit(event)}>
            <input
              placeholder="가입 이메일"
              value={resetEmail}
              onChange={(event) => setResetEmail(event.target.value)}
            />
            <div className="verification-row">
              <input
                placeholder="인증 코드 6자리"
                value={resetCode}
                onChange={(event) => setResetCode(event.target.value)}
              />
              <button type="button" className="nav-item" onClick={() => void onSendResetCode()}>
                코드 발송
              </button>
            </div>
            <div className="password-field">
              <input
                placeholder="새 비밀번호"
                type={showResetPassword ? "text" : "password"}
                value={resetNewPassword}
                onChange={(event) => setResetNewPassword(event.target.value)}
              />
              <button type="button" className="password-toggle" onClick={() => setShowResetPassword((prev) => !prev)}>
                {showResetPassword ? "숨김" : "보기"}
              </button>
            </div>
            <div className="password-field">
              <input
                placeholder="새 비밀번호 확인"
                type={showResetPasswordConfirm ? "text" : "password"}
                value={resetConfirmPassword}
                onChange={(event) => setResetConfirmPassword(event.target.value)}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowResetPasswordConfirm((prev) => !prev)}
              >
                {showResetPasswordConfirm ? "숨김" : "보기"}
              </button>
            </div>
            <button type="submit" className="btn-primary" disabled={authLoading}>
              {authLoading ? "처리 중..." : "비밀번호 재설정"}
            </button>
          </form>
        ) : null}

        {assistMode === "none" && authMode === "login" ? (
          <form className="auth-form-grid" onSubmit={(event) => void onLoginSubmit(event)}>
            <input placeholder="이메일" value={loginEmail} onChange={(event) => setLoginEmail(event.target.value)} />
            <div className="password-field">
              <input
                placeholder="비밀번호"
                type={showLoginPassword ? "text" : "password"}
                value={loginPassword}
                onChange={(event) => setLoginPassword(event.target.value)}
              />
              <button type="button" className="password-toggle" onClick={() => setShowLoginPassword((prev) => !prev)}>
                {showLoginPassword ? "숨김" : "보기"}
              </button>
            </div>
            <button type="submit" className="btn-primary" disabled={authLoading}>
              {authLoading ? "처리 중..." : "로그인"}
            </button>
            <div className="auth-help-row">
              <button type="button" className="btn-link" onClick={() => setAssistMode("find-id")}>
                아이디 찾기
              </button>
              <button type="button" className="btn-link" onClick={() => setAssistMode("reset-password")}>
                비밀번호 찾기
              </button>
            </div>
          </form>
        ) : null}

        {assistMode === "none" && authMode === "register" ? (
          <form className="auth-form-grid" onSubmit={(event) => void onRegisterSubmit(event)}>
            <input
              placeholder="닉네임 (2~20자, 한글/영문/숫자)"
              value={registerName}
              onChange={(event) => setRegisterName(event.target.value)}
            />
            <input
              placeholder="이메일"
              value={registerEmail}
              onChange={(event) => setRegisterEmail(event.target.value)}
            />
            <div className="verification-row">
              <input
                placeholder="인증 코드 6자리"
                value={registerVerificationCode}
                onChange={(event) => setRegisterVerificationCode(event.target.value)}
              />
              <button type="button" className="nav-item" onClick={() => void onSendSignupCode()}>
                코드 발송
              </button>
            </div>
            <div className="password-field">
              <input
                placeholder="비밀번호 (8~16자, 영문/숫자/특수문자)"
                type={showRegisterPassword ? "text" : "password"}
                value={registerPassword}
                onChange={(event) => setRegisterPassword(event.target.value)}
              />
              <button type="button" className="password-toggle" onClick={() => setShowRegisterPassword((prev) => !prev)}>
                {showRegisterPassword ? "숨김" : "보기"}
              </button>
            </div>
            <div className="password-field">
              <input
                placeholder="비밀번호 확인"
                type={showRegisterPasswordConfirm ? "text" : "password"}
                value={registerPasswordConfirm}
                onChange={(event) => setRegisterPasswordConfirm(event.target.value)}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowRegisterPasswordConfirm((prev) => !prev)}
              >
                {showRegisterPasswordConfirm ? "숨김" : "보기"}
              </button>
            </div>
            <label className="agree-label">
              <input
                type="checkbox"
                checked={registerAgreements}
                onChange={(event) => setRegisterAgreements(event.target.checked)}
              />
              [필수] 서비스 이용약관 및 개인정보 처리방침 동의
            </label>
            <button type="submit" className="btn-primary" disabled={authLoading}>
              {authLoading ? "처리 중..." : "회원가입"}
            </button>
          </form>
        ) : null}

        <p className="auth-message">{authMessage}</p>
      </div>
    </div>
  );
}
