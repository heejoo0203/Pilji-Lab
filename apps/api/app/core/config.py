from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "autoLV API"
    cors_origins: str = Field(
        default="http://127.0.0.1:3000,http://localhost:3000",
        alias="CORS_ORIGINS",
    )
    database_url: str = Field(default="sqlite:///./autolv.db", alias="DATABASE_URL")

    jwt_secret_key: str = Field(default="change-me-access-key", alias="JWT_SECRET_KEY")
    jwt_refresh_secret_key: str = Field(
        default="change-me-refresh-key",
        alias="JWT_REFRESH_SECRET_KEY",
    )
    access_token_exp_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXP_MINUTES")
    refresh_token_exp_days: int = Field(default=14, alias="REFRESH_TOKEN_EXP_DAYS")

    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    cookie_samesite: str = Field(default="lax", alias="COOKIE_SAMESITE")
    vworld_api_base_url: str = Field(default="https://api.vworld.kr", alias="VWORLD_API_BASE_URL")
    vworld_api_key: str = Field(default="", alias="VWORLD_API_KEY")
    vworld_api_domain: str = Field(default="localhost", alias="VWORLD_API_DOMAIN")
    vworld_timeout_seconds: int = Field(default=15, alias="VWORLD_TIMEOUT_SECONDS")


settings = Settings()
