"""Application settings loaded from environment variables.

All configuration is centralised here so the rest of the codebase never reads
``os.environ`` directly. Secrets are injected through the environment / Docker
secrets and never hard-coded.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- General -----------------------------------------------------------
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    project_name: str = Field(default="Control Plane")
    api_v1_prefix: str = Field(default="/api/v1")

    # --- Security ----------------------------------------------------------
    secret_key: str = Field(default="change-me-in-production")
    access_token_expire_minutes: int = Field(default=60 * 12)
    jwt_algorithm: str = Field(default="HS256")

    # First superadmin, created on startup if no users exist.
    first_superadmin_email: str = Field(default="admin@example.com")
    first_superadmin_password: str = Field(default="changeme123")

    # --- Database ----------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://control:control@db:5432/control_plane"
    )

    # --- Redis / Celery ----------------------------------------------------
    redis_url: str = Field(default="redis://redis:6379/0")

    # --- CORS --------------------------------------------------------------
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Config rendering --------------------------------------------------
    # Directory where the rendered Traefik dynamic configuration is written.
    traefik_dynamic_dir: str = Field(default="/data/traefik/dynamic")
    # Default web entrypoints used when rendering routers.
    traefik_web_entrypoint: str = Field(default="web")
    traefik_websecure_entrypoint: str = Field(default="websecure")
    traefik_cert_resolver: str = Field(default="letsencrypt")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
