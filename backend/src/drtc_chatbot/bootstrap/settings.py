"""Application settings, read from environment variables prefixed with ``DRTC_``."""

from enum import StrEnum
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


def _default_manifest_path() -> Path:
    # backend/src/drtc_chatbot/bootstrap/settings.py -> repository root (source checkout only;
    # containers set DRTC_CORPUS_MANIFEST_PATH explicitly).
    return Path(__file__).resolve().parents[4] / "corpus" / "manifest.yaml"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DRTC_",
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "DRTC Puno - Asistente normativo"
    environment: Environment = Environment.LOCAL
    log_level: str = "INFO"
    log_json: bool = False
    database_url: str = "postgresql+psycopg://drtc:drtc@localhost:5433/drtc_chatbot"
    database_echo: bool = False
    corpus_manifest_path: Path = Field(default_factory=_default_manifest_path)
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:4200"])
    # "database": catalog from PostgreSQL (needs migrations + `drtc-ingest sync`).
    # "manifest": reads corpus/manifest.yaml directly (fast tests, development without a database).
    catalog_backend: Literal["database", "manifest"] = "database"
    # Unset = auto_dev in local/test, manual elsewhere.
    # auto_dev is refused in staging/production (ADR-0011).
    ingestion_approval_policy: Literal["manual", "auto_dev"] | None = None

    @model_validator(mode="after")
    def _resolve_approval_policy(self) -> Self:
        protected = self.environment in {Environment.STAGING, Environment.PRODUCTION}
        if self.ingestion_approval_policy == "auto_dev" and protected:
            raise ValueError(
                "DRTC_INGESTION_APPROVAL_POLICY=auto_dev is not allowed in staging or production"
            )
        if self.ingestion_approval_policy is None:
            self.ingestion_approval_policy = "manual" if protected else "auto_dev"
        return self
