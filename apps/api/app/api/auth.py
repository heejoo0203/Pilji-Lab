from fastapi import APIRouter, Cookie, Depends, File, Form, UploadFile, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    AccountDeleteRequest,
    AuthResponse,
    FindIdCompleteRequest,
    FindIdCompleteResponse,
    LoginRequest,
    PasswordChangeRequest,
    RecoveryCodeSendRequest,
    RecoveryCodeSendResponse,
    RegisterRequest,
    ResetPasswordByCodeRequest,
    TermsResponse,
    UserOut,
)
from app.services.auth_service import (
    attach_auth_cookies,
    build_user_out,
    change_password,
    clear_auth_cookies,
    delete_account,
    find_id_by_code,
    get_user_from_access_token,
    get_terms_for_user,
    login_user,
    register_user,
    reset_password_by_code,
    send_recovery_code,
    update_profile,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = register_user(db, payload)
    return AuthResponse(user_id=user.id, email=user.email, full_name=user.full_name)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user = login_user(db, payload)
    attach_auth_cookies(response, user.id)
    return AuthResponse(user_id=user.id, email=user.email, full_name=user.full_name)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_auth_cookies(response)
    return response


@router.get("/me", response_model=UserOut)
def me(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> UserOut:
    user = get_user_from_access_token(db, access_token)
    return build_user_out(user)


@router.get("/terms", response_model=TermsResponse)
def terms(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> TermsResponse:
    user = get_user_from_access_token(db, access_token)
    return get_terms_for_user(user)


@router.patch("/profile", response_model=UserOut)
async def edit_profile(
    full_name: str | None = Form(default=None),
    profile_image: UploadFile | None = File(default=None),
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> UserOut:
    user = get_user_from_access_token(db, access_token)
    image_name = profile_image.filename if profile_image else None
    image_bytes = await profile_image.read() if profile_image else None
    updated = update_profile(
        db,
        user=user,
        full_name=full_name,
        profile_image_filename=image_name,
        profile_image_bytes=image_bytes,
    )
    return build_user_out(updated)


@router.post("/password/change")
def update_password(
    payload: PasswordChangeRequest,
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = get_user_from_access_token(db, access_token)
    change_password(db, user=user, payload=payload)
    return {"message": "비밀번호가 변경되었습니다."}


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def withdraw_account(
    payload: AccountDeleteRequest,
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Response:
    user = get_user_from_access_token(db, access_token)
    delete_account(db, user=user, confirmation_text=payload.confirmation_text)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_auth_cookies(response)
    return response


@router.post("/recovery/send-code", response_model=RecoveryCodeSendResponse)
def send_code(payload: RecoveryCodeSendRequest, db: Session = Depends(get_db)) -> RecoveryCodeSendResponse:
    return send_recovery_code(db, payload)


@router.post("/recovery/find-id", response_model=FindIdCompleteResponse)
def find_id(payload: FindIdCompleteRequest, db: Session = Depends(get_db)) -> FindIdCompleteResponse:
    email = find_id_by_code(db, payload)
    return FindIdCompleteResponse(email=email)


@router.post("/recovery/reset-password")
def reset_password(payload: ResetPasswordByCodeRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    reset_password_by_code(db, payload)
    return {"message": "비밀번호가 재설정되었습니다. 새 비밀번호로 로그인해 주세요."}
