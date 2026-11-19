"""Limits of a search text."""

import pytest

from drtc_chatbot.contexts.retrieval.domain.query import MAX_QUERY_CHARS, validate_query
from drtc_chatbot.shared_kernel.domain import InvariantViolationError


@pytest.mark.spec("004-FR-014")
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("plazo para apelar", "plazo para apelar"),
        ("  mucho   espacio \n aquí ", "mucho espacio aquí"),
        ("a", "a"),
    ],
)
def test_the_text_is_trimmed_and_its_whitespace_collapsed(raw: str, expected: str) -> None:
    assert validate_query(raw) == expected


@pytest.mark.spec("004-FR-014")
@pytest.mark.parametrize("raw", ["", "   ", "\n\t "])
def test_an_empty_text_is_refused(raw: str) -> None:
    with pytest.raises(InvariantViolationError, match="empty"):
        validate_query(raw)


@pytest.mark.spec("004-FR-014")
def test_the_limit_is_measured_on_the_cleaned_text() -> None:
    assert len(validate_query("x" * MAX_QUERY_CHARS)) == MAX_QUERY_CHARS
    assert (
        validate_query(" " + "x" * MAX_QUERY_CHARS + "  ") == "x" * MAX_QUERY_CHARS
    )  # spaces do not count
    with pytest.raises(InvariantViolationError, match="longer than 300"):
        validate_query("x" * (MAX_QUERY_CHARS + 1))
