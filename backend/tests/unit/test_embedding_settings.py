"""Settings of the meaning search: the key is a secret and a fake provider never reaches production."""

import pytest

from drtc_chatbot.bootstrap.container import build_embedding_provider
from drtc_chatbot.bootstrap.settings import Environment, Settings
from drtc_chatbot.contexts.retrieval.infrastructure.fake_embeddings import FakeEmbeddingProvider
from drtc_chatbot.contexts.retrieval.infrastructure.gemini_embeddings import GeminiEmbeddingProvider
from drtc_chatbot.contexts.retrieval.infrastructure.openai_embeddings import OpenAIEmbeddingProvider

SECRET = "sk-test-NOT-A-REAL-KEY-0123456789"  # noqa: S105 - a fake key, to prove it never leaks
GEMINI = "gemini-test-NOT-A-REAL-KEY-0123456789"  # a fake key, to prove it never leaks


def settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


@pytest.mark.spec("004-FR-014")
def test_the_key_never_shows_in_repr_str_or_a_dump_of_the_settings() -> None:
    configured = settings(openai_api_key=SECRET)

    assert SECRET not in repr(configured)
    assert SECRET not in str(configured)
    assert SECRET not in configured.model_dump_json()
    assert configured.openai_api_key is not None
    assert configured.openai_api_key.get_secret_value() == SECRET  # only on purpose


@pytest.mark.spec("004-FR-013")
def test_without_a_key_the_meaning_search_is_off_and_with_one_it_is_on() -> None:
    assert settings().embedding_provider == "none"
    assert settings(openai_api_key=SECRET).embedding_provider == "openai"


def test_the_provider_can_be_chosen_explicitly() -> None:
    assert settings(openai_api_key=SECRET, embedding_provider="none").embedding_provider == "none"
    assert (
        settings(embedding_provider="fake", environment=Environment.LOCAL).embedding_provider
        == "fake"
    )


@pytest.mark.parametrize("environment", [Environment.STAGING, Environment.PRODUCTION])
def test_the_fake_provider_is_refused_where_real_people_use_the_tool(
    environment: Environment,
) -> None:
    with pytest.raises(ValueError, match="not allowed in staging or production"):
        settings(embedding_provider="fake", environment=environment)


def test_asking_for_openai_without_a_key_is_a_configuration_error_not_a_silent_fallback() -> None:
    with pytest.raises(ValueError, match="needs DRTC_OPENAI_API_KEY"):
        settings(embedding_provider="openai")


def test_sensible_defaults_and_limits() -> None:
    configured = settings()

    assert configured.openai_embedding_model == "text-embedding-3-small"
    assert configured.openai_embedding_dimensions is None
    assert (configured.search_rrf_k, configured.search_arm_top_n) == (5, 50)
    assert configured.search_vector_weight == 6.0
    assert configured.search_vector_timeout_seconds == 3.0
    with pytest.raises(ValueError, match="greater than or equal to 1"):
        settings(search_rrf_k=0)
    with pytest.raises(ValueError, match="greater than 0"):
        settings(search_vector_timeout_seconds=0)
    with pytest.raises(ValueError, match="greater than 0"):
        settings(search_vector_weight=0)


# ---------------------------------------------------------------------------------- gemini
def test_the_gemini_key_never_shows_in_repr_str_or_a_dump_of_the_settings() -> None:
    configured = settings(gemini_api_key=GEMINI)

    assert GEMINI not in repr(configured)
    assert GEMINI not in str(configured)
    assert GEMINI not in configured.model_dump_json()
    assert configured.gemini_api_key is not None
    assert configured.gemini_api_key.get_secret_value() == GEMINI  # only on purpose


def test_a_gemini_key_alone_turns_the_meaning_search_on_with_gemini() -> None:
    assert settings(gemini_api_key=GEMINI).embedding_provider == "gemini"


def test_with_both_keys_the_default_is_openai_and_gemini_must_be_asked_for() -> None:
    both = {"openai_api_key": SECRET, "gemini_api_key": GEMINI}

    assert settings(**both).embedding_provider == "openai"
    assert settings(**both, embedding_provider="gemini").embedding_provider == "gemini"


def test_asking_for_gemini_without_its_key_is_a_configuration_error_not_a_silent_fallback() -> None:
    with pytest.raises(ValueError, match="needs DRTC_GEMINI_API_KEY"):
        settings(embedding_provider="gemini")
    with pytest.raises(ValueError, match="needs DRTC_GEMINI_API_KEY"):
        settings(openai_api_key=SECRET, embedding_provider="gemini")  # the other key does not count


def test_gemini_defaults_and_a_floor_for_the_rate_limit_ceiling() -> None:
    configured = settings()

    assert configured.gemini_embedding_model == "gemini-embedding-2"
    assert configured.gemini_max_tokens_per_minute == 25_000
    assert configured.gemini_max_requests_per_minute == 80  # the free tier allows 100 per minute
    with pytest.raises(ValueError, match="greater than or equal to 1000"):
        settings(gemini_max_tokens_per_minute=10)


def test_the_container_builds_the_provider_the_settings_ask_for() -> None:
    gemini = build_embedding_provider(
        settings(gemini_api_key=GEMINI, gemini_embedding_model="gemini-embedding-001")
    )
    openai = build_embedding_provider(settings(openai_api_key=SECRET))
    fake = build_embedding_provider(settings(embedding_provider="fake"))

    assert isinstance(gemini, GeminiEmbeddingProvider)
    assert gemini.model == "gemini-embedding-001"
    assert type(openai) is OpenAIEmbeddingProvider
    assert isinstance(fake, FakeEmbeddingProvider)
    assert build_embedding_provider(settings()) is None
