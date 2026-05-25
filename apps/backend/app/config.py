"""Application settings loaded from environment variables.

All configuration is centralised here so the rest of the codebase never reads
``os.environ`` directly. Secrets are injected through the environment / Docker
secrets and never hard-coded.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
    # ``NoDecode`` disables pydantic-settings' source-level JSON parsing so the
    # validator below can accept a plain comma-separated env value.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    # --- WireGuard hub -----------------------------------------------------
    # The single VPS hub all site gateways tunnel into. Used to auto-fill
    # generated gateway configs so operators get a ready-to-use file. The
    # public key and endpoint are not secrets (the private key never leaves
    # the hub). Tunnel IPs for site gateways are allocated from the hub subnet.
    wg_hub_public_key: str = Field(default="")
    wg_hub_endpoint: str = Field(default="")  # host:port, e.g. vps.example.com:51820
    wg_hub_tunnel_subnet: str = Field(default="10.10.0.0/24")

    # --- wg-easy -----------------------------------------------------------
    # wg-easy is the WireGuard hub and the source of truth for peers/clients.
    # The backend talks to its HTTP API to list/create client configs; the UI
    # links operators to the wg-easy panel for full tunnel management.
    wgeasy_api_url: str = Field(default="")  # internal URL, e.g. http://wg-easy:51821
    wgeasy_password: str = Field(default="")  # password for the wg-easy session API
    wgeasy_public_url: str = Field(default="")  # public panel URL for the menu link

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
