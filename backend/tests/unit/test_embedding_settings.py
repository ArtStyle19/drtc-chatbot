"""Settings of the meaning search: the key is a secret and a fake provider never reaches production."""

import pytest

from drtc_chatbot.bootstrap.settings import Environment, Settings

SECRET = "sk-test-NOT-A-REAL-KEY-0123456789"  # noqa: S105 - a fake key, to prove it never leaks


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
    assert (configured.search_rrf_k, configured.search_arm_top_n) == (60, 50)
    assert configured.search_vector_timeout_seconds == 3.0
    with pytest.raises(ValueError, match="greater than or equal to 1"):
        settings(search_rrf_k=0)
    with pytest.raises(ValueError, match="greater than 0"):
        settings(search_vector_timeout_seconds=0)
