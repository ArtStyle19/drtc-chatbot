"""Application settings, read from environment variables prefixed with ``DRTC_``."""

from enum import StrEnum
from pathlib import Path

from pydantic import Field
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
