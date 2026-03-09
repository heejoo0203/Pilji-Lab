"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/app/components/auth-provider";
import type { UserTerms } from "@/app/lib/types";

export default function MyPage() {
  const {
    user,
    openAuth,
    authLoading,
    authMessage,
    updateProfile,
    changePassword,
    deleteAccount,
    loadTerms,
    expectedWithdrawalText,
  } = useAuth();

  const isLoggedIn = Boolean(user);
  const [fullName, setFullName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [profileImage, setProfileImage] = useState<File | null>(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");

  const [withdrawText, setWithdrawText] = useState("");
  const [terms, setTerms] = useState<UserTerms | null>(null);
  const [termsLoading, setTermsLoading] = useState(false);
  const [localMessage, setLocalMessage] = useState("");

  useEffect(() => {
    if (!isLoggedIn) return;
    setFullName(user?.full_name ?? "");
    setPhoneNumber(user?.phone_number ?? "");
  }, [isLoggedIn, user?.full_name, user?.phone_number]);

  useEffect(() => {
    if (!isLoggedIn) return;
    let ignore = false;
    const run = async () => {
      setTermsLoading(true);
      try {
        const payload = await loadTerms();
        if (ignore) return;
        setTerms(payload);
      } catch (error) {
        if (ignore) return;
        setLocalMessage(error instanceof Error ? error.message : "약관을 불러오지 못했습니다.");
      } finally {
        if (!ignore) setTermsLoading(false);
      }
    };
    void run();
    return () => {
      ignore = true;
    };
  }, [isLoggedIn, loadTerms]);

  const mergedMessage = useMemo(() => localMessage || authMessage, [localMessage, authMessage]);

  if (!isLoggedIn) {
    return (
      <div className="mypage-shell">
        <section className="mypage-hero hero-grid">
          <div>
            <span className="eyebrow">Account Center</span>
            <h1 className="hero-title">계정, 보안, 약관 동의 내역을 한 곳에서 관리합니다.</h1>
            <p className="hero-copy">필지랩 마이페이지는 회원 정보 수정부터 앱 다운로드, 계정 삭제까지 운영형 서비스 기준으로 구성돼 있습니다.</p>
          </div>
        </section>
        <section className="panel">
          <h2>마이페이지는 로그인 후 사용할 수 있습니다.</h2>
          <p className="hint">로그인 후 계정 설정, 비밀번호 변경, 서비스 약관 확인, 앱 다운로드를 이용할 수 있습니다.</p>
          <button className="btn-primary" onClick={() => openAuth("login")}>
            로그인하고 마이페이지 열기
          </button>
        </section>
      </div>
    );
  }

  return (
    <div className="mypage-shell">
      <section className="mypage-hero hero-grid">
        <div>
          <span className="eyebrow">Account Center</span>
          <h1 className="hero-title">필지랩 계정과 서비스 설정을 한 화면에서 다룹니다.</h1>
          <p className="hero-copy">프로필, 비밀번호, 약관 동의 내역, 모바일 앱 배포본, 회원 탈퇴까지 계정 운영 흐름을 정리했습니다.</p>
          {mergedMessage ? <p className="hint">{mergedMessage}</p> : null}
        </div>
        <div className="hero-stat-grid">
          <div className="hero-stat-card">
            <div className="hero-stat-label">이름</div>
            <div className="hero-stat-value small">{user?.full_name || "-"}</div>
          </div>
          <div className="hero-stat-card">
            <div className="hero-stat-label">이메일</div>
            <div className="hero-stat-value small">{user?.email || "-"}</div>
          </div>
          <div className="hero-stat-card">
            <div className="hero-stat-label">연락처</div>
            <div className="hero-stat-value small">{user?.phone_number || "-"}</div>
          </div>
          <div className="hero-stat-card">
            <div className="hero-stat-label">역할</div>
            <div className="hero-stat-value small">{user?.role || "user"}</div>
          </div>
        </div>
      </section>

      <section className="panel mypage-grid">
        <article className="mypage-card">
          <h3>회원 정보 수정</h3>
          <label className="field-label" htmlFor="mypage-name">
            이름
          </label>
          <input
            id="mypage-name"
            className="auth-input"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            placeholder="이름"
          />

          <label className="field-label" htmlFor="mypage-phone">
            연락처
          </label>
          <input
            id="mypage-phone"
            className="auth-input"
            value={phoneNumber}
            onChange={(event) => setPhoneNumber(event.target.value)}
            placeholder="연락처 (숫자 또는 하이픈)"
          />

          <label className="field-label" htmlFor="mypage-image">
            프로필 이미지
          </label>
          <input
            id="mypage-image"
            className="auth-input"
            type="file"
            accept=".png,.jpg,.jpeg,.webp"
            onChange={(event) => setProfileImage(event.target.files?.[0] ?? null)}
          />

          <button
            type="button"
            className="btn-primary"
            disabled={authLoading}
            onClick={async () => {
              setLocalMessage("");
              await updateProfile({ full_name: fullName, phone_number: phoneNumber, profile_image: profileImage });
              setProfileImage(null);
            }}
          >
            {authLoading ? "저장 중..." : "저장"}
          </button>
        </article>

        <article className="mypage-card">
          <h3>비밀번호 변경</h3>
          <label className="field-label" htmlFor="mypage-current-password">
            기존 비밀번호
          </label>
          <input
            id="mypage-current-password"
            className="auth-input"
            type="password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
            placeholder="기존 비밀번호"
          />

          <label className="field-label" htmlFor="mypage-new-password">
            새 비밀번호
          </label>
          <input
            id="mypage-new-password"
            className="auth-input"
            type="password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            placeholder="새 비밀번호"
          />

          <label className="field-label" htmlFor="mypage-confirm-password">
            새 비밀번호 확인
          </label>
          <input
            id="mypage-confirm-password"
            className="auth-input"
            type="password"
            value={confirmNewPassword}
            onChange={(event) => setConfirmNewPassword(event.target.value)}
            placeholder="새 비밀번호 확인"
          />

          <button
            type="button"
            className="btn-primary"
            disabled={authLoading}
            onClick={async () => {
              setLocalMessage("");
              await changePassword({
                current_password: currentPassword,
                new_password: newPassword,
                confirm_new_password: confirmNewPassword,
              });
              setCurrentPassword("");
              setNewPassword("");
              setConfirmNewPassword("");
            }}
          >
            {authLoading ? "변경 중..." : "비밀번호 변경"}
          </button>
        </article>

        <article className="mypage-card">
          <h3>서비스 약관</h3>
          {termsLoading ? <p className="hint">약관을 불러오는 중입니다...</p> : null}
          {!termsLoading && terms ? (
            <>
              <p className="hint">
                동의 버전: <strong>{terms.version}</strong>
                <br />
                동의 일시: {terms.accepted_at ? new Date(terms.accepted_at).toLocaleString("ko-KR") : "-"}
              </p>
              <pre className="terms-content-box">{terms.content}</pre>
            </>
          ) : null}
          {!termsLoading && !terms ? <p className="hint">약관 정보를 불러오지 못했습니다.</p> : null}
        </article>

        <article className="mypage-card">
          <h3>앱 다운로드</h3>
          <p className="hint">
            안드로이드 기기에서 필지랩 앱을 설치해 모바일 환경에서 바로 사용할 수 있습니다.
          </p>
          <a
            className="btn-primary full"
            href="/downloads/autoLV-android-release-v2.1.2.apk"
            download
            target="_blank"
            rel="noopener noreferrer"
          >
            필지랩 안드로이드 APK 다운로드
          </a>
        </article>

        <article className="mypage-card danger-zone">
          <h3>회원 탈퇴</h3>
          <p className="danger-guide">
            아래 문구를 정확히 입력해야 탈퇴할 수 있습니다.
            <br />
            <strong>{expectedWithdrawalText}</strong>
          </p>
          <input
            className="auth-input"
            value={withdrawText}
            onChange={(event) => setWithdrawText(event.target.value)}
            placeholder="확인 문구 입력"
          />
          <button
            type="button"
            className="btn-primary danger-fill"
            disabled={authLoading}
            onClick={async () => {
              setLocalMessage("");
              await deleteAccount(withdrawText);
            }}
          >
            {authLoading ? "탈퇴 처리 중..." : "회원 탈퇴"}
          </button>
        </article>
      </section>
    </div>
  );
}
