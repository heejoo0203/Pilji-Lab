"use client";

import { useEffect, useMemo, useState } from "react";

import type { AuthUser } from "@/app/lib/types";

export type ProfileActionMode = "profile" | "password" | "withdraw";

type Props = {
  open: boolean;
  mode: ProfileActionMode;
  user: AuthUser | null;
  authLoading: boolean;
  message: string;
  expectedWithdrawalText: string;
  onClose: () => void;
  onUpdateProfile: (payload: { full_name?: string; profile_image?: File | null }) => Promise<void>;
  onChangePassword: (payload: {
    current_password: string;
    new_password: string;
    confirm_new_password: string;
  }) => Promise<void>;
  onDeleteAccount: (confirmationText: string) => Promise<void>;
};

export function ProfileActionModal(props: Props) {
  const [fullName, setFullName] = useState("");
  const [profileImage, setProfileImage] = useState<File | null>(null);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [withdrawText, setWithdrawText] = useState("");

  useEffect(() => {
    if (!props.open) return;
    setFullName((props.user?.full_name ?? "").trim());
    setProfileImage(null);
    setCurrentPassword("");
    setNewPassword("");
    setConfirmNewPassword("");
    setWithdrawText("");
  }, [props.open, props.mode, props.user?.full_name]);

  const title = useMemo(() => {
    if (props.mode === "profile") return "회원 정보 수정";
    if (props.mode === "password") return "비밀번호 변경";
    return "회원 탈퇴";
  }, [props.mode]);

  if (!props.open) return null;

  const renderBody = () => {
    if (props.mode === "profile") {
      return (
        <div className="profile-modal-grid">
          <label className="field-label" htmlFor="profile-name">
            닉네임
          </label>
          <input
            id="profile-name"
            className="auth-input"
            placeholder="닉네임 (2~20자, 한글/영문/숫자)"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />

          <label className="field-label" htmlFor="profile-image">
            프로필 사진
          </label>
          <input
            id="profile-image"
            className="auth-input"
            type="file"
            accept=".png,.jpg,.jpeg,.webp"
            onChange={(e) => setProfileImage(e.target.files?.[0] ?? null)}
          />

          <button
            type="button"
            className="btn-primary"
            disabled={props.authLoading}
            onClick={async () => {
              await props.onUpdateProfile({
                full_name: fullName,
                profile_image: profileImage,
              });
              props.onClose();
            }}
          >
            {props.authLoading ? "저장 중..." : "저장"}
          </button>
        </div>
      );
    }

    if (props.mode === "password") {
      return (
        <div className="profile-modal-grid">
          <label className="field-label" htmlFor="current-password">
            기존 비밀번호
          </label>
          <input
            id="current-password"
            className="auth-input"
            type="password"
            placeholder="기존 비밀번호"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />

          <label className="field-label" htmlFor="new-password">
            새 비밀번호
          </label>
          <input
            id="new-password"
            className="auth-input"
            type="password"
            placeholder="새 비밀번호"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />

          <label className="field-label" htmlFor="confirm-new-password">
            새 비밀번호 확인
          </label>
          <input
            id="confirm-new-password"
            className="auth-input"
            type="password"
            placeholder="새 비밀번호 확인"
            value={confirmNewPassword}
            onChange={(e) => setConfirmNewPassword(e.target.value)}
          />

          <button
            type="button"
            className="btn-primary"
            disabled={props.authLoading}
            onClick={async () => {
              await props.onChangePassword({
                current_password: currentPassword,
                new_password: newPassword,
                confirm_new_password: confirmNewPassword,
              });
              props.onClose();
            }}
          >
            {props.authLoading ? "변경 중..." : "비밀번호 변경"}
          </button>
        </div>
      );
    }

    return (
      <div className="profile-modal-grid">
        <p className="danger-guide">
          아래 문구를 정확히 입력해야 탈퇴할 수 있습니다.
          <br />
          <strong>{props.expectedWithdrawalText}</strong>
        </p>
        <input
          className="auth-input"
          placeholder="확인 문구 입력"
          value={withdrawText}
          onChange={(e) => setWithdrawText(e.target.value)}
        />
        <button
          type="button"
          className="btn-primary danger-fill"
          disabled={props.authLoading}
          onClick={async () => {
            await props.onDeleteAccount(withdrawText);
            props.onClose();
          }}
        >
          {props.authLoading ? "탈퇴 처리 중..." : "회원 탈퇴"}
        </button>
      </div>
    );
  };

  return (
    <div className="auth-overlay" onClick={props.onClose}>
      <div className="auth-modal profile-modal" onClick={(e) => e.stopPropagation()}>
        <div className="auth-modal-head">
          <h3>{title}</h3>
          <button type="button" onClick={props.onClose}>
            ✕
          </button>
        </div>
        {renderBody()}
        <p className="auth-message">{props.message}</p>
      </div>
    </div>
  );
}

