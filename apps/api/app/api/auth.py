from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserOut
from app.services.auth_service import (
    attach_auth_cookies,
    clear_auth_cookies,
    get_user_from_access_token,
    login_user,
    register_user,
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
def logout(response: Response) -> Response:
    clear_auth_cookies(response)
    return response


@router.get("/me", response_model=UserOut)
def me(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> UserOut:
    user = get_user_from_access_token(db, access_token)
    return UserOut.model_validate(user)

