"""Parser profiles: the tuning each of the three initial norms needs."""

import re

from drtc_chatbot.contexts.ingestion.domain.parsing.engine import (
    ArticleDocumentParser,
    ParserOptions,
)

_TUO_NOISE = re.compile(
    r"^(?:"
    r"TEXTO ÚNICO ORDENADO DE LA LEY N° 27444(?: - LEY DEL PROCEDIMIENTO ADMINISTRATIVO GENERAL)?(?:\s+\d{1,3})?"
    r"|LEY DE L PROCEDIMIENTO ADMINISTRATIVO GENERAL"
    r"|MINISTERIO DE JUSTICIA Y DERECHOS HUMANOS"
    r"|(?:\d{1,3}\s+)?SEGUNDA PARTE"
    r")\s*$"
)
_TUO_START = re.compile(r"^T[ÍI]TULO PRELIMINAR\s*$")
_RENAT_START = re.compile(r"^REGLAMENTO NACIONAL DE ADMINISTRACI[ÓO]N DE TRANSPORTE\s*$")

PROFILES: dict[str, ParserOptions] = {
    "ley-lgttt": ParserOptions(),
    "renat": ParserOptions(start_marker=_RENAT_START),
    "tuo-lpag": ParserOptions(
        is_noise=lambda text: bool(_TUO_NOISE.match(text)),
        roman_articles=True,
        footnotes=True,
        start_marker=_TUO_START,  # pages 71-77 are the approving DS 004-2019-JUS, not the TUO text
        marker_is_content=True,
    ),
}


class UnknownParserProfileError(KeyError):
    """The manifest asks for a parser profile that does not exist."""


def build_parser(profile: str) -> ArticleDocumentParser:
    try:
        return ArticleDocumentParser(PROFILES[profile])
    except KeyError as error:
        raise UnknownParserProfileError(profile) from error
