import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=16)
    confirm_password: str = Field(min_length=8, max_length=16)
    full_name: str = Field(min_length=2, max_length=20)
    agreements: bool

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        pattern = re.compile(r"^[A-Za-z0-9가-힣]{2,20}$")
        if not pattern.match(value):
            raise ValueError("닉네임은 2~20자의 한글/영문/숫자만 사용할 수 있습니다.")
        return value

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        # bcrypt backend constraints are based on byte-length.
        if len(value.encode("utf-8")) > 72:
            raise ValueError("비밀번호는 UTF-8 기준 72바이트를 넘을 수 없습니다.")
        if not re.search(r"[A-Za-z]", value):
            raise ValueError("비밀번호는 영문을 1자 이상 포함해야 합니다.")
        if not re.search(r"[0-9]", value):
            raise ValueError("비밀번호는 숫자를 1자 이상 포함해야 합니다.")
        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError("비밀번호는 특수문자를 1자 이상 포함해야 합니다.")
        return value

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("비밀번호 확인 값은 UTF-8 기준 72바이트를 넘을 수 없습니다.")
        return value

    @model_validator(mode="after")
    def validate_register_fields(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("비밀번호와 비밀번호 확인이 일치하지 않습니다.")
        if self.agreements is not True:
            raise ValueError("필수 약관 동의가 필요합니다.")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=16)

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("비밀번호는 UTF-8 기준 72바이트를 넘을 수 없습니다.")
        return value


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str | None
    role: str
    auth_provider: str


class AuthResponse(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str | None = None
