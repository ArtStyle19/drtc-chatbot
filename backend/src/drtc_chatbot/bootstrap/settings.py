"""Application settings, read from environment variables prefixed with ``DRTC_``."""

from enum import StrEnum
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
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


def _default_evaluation_dir() -> Path:
    # Same rule as the manifest: source checkout only; containers set DRTC_EVALUATION_DIR.
    return Path(__file__).resolve().parents[4] / "evaluation"


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
    evaluation_dir: Path = Field(default_factory=_default_evaluation_dir)
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:4200"])
    # "database": catalog from PostgreSQL (needs migrations + `drtc-ingest sync`).
    # "manifest": reads corpus/manifest.yaml directly (fast tests, development without a database).
    catalog_backend: Literal["database", "manifest"] = "database"
    # Unset = auto_dev in local/test, manual elsewhere.
    # auto_dev is refused in staging/production (ADR-0011).
    ingestion_approval_policy: Literal["manual", "auto_dev"] | None = None

    # --- meaning search (spec 004). The key lives ONLY in the environment / .env, never in code.
    openai_api_key: SecretStr | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    # Optional shortened vectors (text-embedding-3-* accept it); None = the model's own size.
    openai_embedding_dimensions: int | None = Field(default=None, ge=64)
    # Unset = "openai" with an OpenAI key, else "gemini" with a Gemini key, else "none" (the search
    # then falls back to words). With both keys, say which one: it is a choice of provider.
    # "fake" is a deterministic offline provider for tests and demos; refused in staging/production.
    embedding_provider: Literal["openai", "gemini", "fake", "none"] | None = None
    # Google Gemini embeddings (OpenAI-compatible endpoint). The free tier is rate limited per
    # project; the ceiling is estimated tokens per minute (raise it on a paid tier).
    gemini_api_key: SecretStr | None = None
    gemini_embedding_model: str = "gemini-embedding-2"
    gemini_max_tokens_per_minute: int = Field(default=25_000, ge=1_000)
    # Free tier of gemini-embedding-2: 100 requests a minute; every text of a batch counts as one.
    gemini_max_requests_per_minute: int = Field(default=80, ge=1)
    # Fusion of the words and meaning arms, chosen with the golden set (see search_passages.py).
    search_rrf_k: int = Field(default=5, ge=1)
    search_vector_weight: float = Field(default=6.0, gt=0)
    search_arm_top_n: int = Field(default=50, ge=1, le=200)
    search_vector_timeout_seconds: float = Field(default=3.0, gt=0)

    @model_validator(mode="after")
    def _resolve_embedding_provider(self) -> Self:
        protected = self.environment in {Environment.STAGING, Environment.PRODUCTION}
        if self.embedding_provider == "fake" and protected:
            raise ValueError("DRTC_EMBEDDING_PROVIDER=fake is not allowed in staging or production")
        if self.embedding_provider == "openai" and self.openai_api_key is None:
            raise ValueError("DRTC_EMBEDDING_PROVIDER=openai needs DRTC_OPENAI_API_KEY")
        if self.embedding_provider == "gemini" and self.gemini_api_key is None:
            raise ValueError("DRTC_EMBEDDING_PROVIDER=gemini needs DRTC_GEMINI_API_KEY")
        if self.embedding_provider is None:
            if self.openai_api_key is not None:
                self.embedding_provider = "openai"
            elif self.gemini_api_key is not None:
                self.embedding_provider = "gemini"
            else:
                self.embedding_provider = "none"
        return self

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
