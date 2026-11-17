"""Value objects of the legal corpus.

Ubiquitous language (ES -> EN) is documented in docs/domain/ubiquitous-language.md.
"""

import re
from dataclasses import dataclass
from enum import StrEnum

from drtc_chatbot.shared_kernel.domain import InvariantViolationError

_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_VERSION_ID = re.compile(r"^[a-z0-9]+(?:[-.@][a-z0-9]+)*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class InstrumentType(StrEnum):
    """Kind of legal instrument (tipo de norma)."""

    LAW = "ley"
    SUPREME_DECREE = "decreto_supremo"
    LEGISLATIVE_DECREE = "decreto_legislativo"
    EMERGENCY_DECREE = "decreto_de_urgencia"
    SINGLE_ORDERED_TEXT = "texto_unico_ordenado"
    REGULATION = "reglamento"
    RESOLUTION = "resolucion"
    REGIONAL_ORDINANCE = "ordenanza_regional"
    OTHER = "otro"


class VerificationStatus(StrEnum):
    """What we know about whether a version's text is the one in force today.

    ``unknown`` is deliberately different from ``verified_current``: an unverified text is
    never presented as current law (Annex B, principle 1 of the reference architecture).
    """

    VERIFIED_CURRENT = "verified_current"
    UNVERIFIED = "unverified"
    PENDING_REVIEW = "pending_review"
    SUPERSEDED = "superseded"
    REPEALED = "repealed"
    UNKNOWN = "unknown"

    @property
    def may_be_presented_as_current(self) -> bool:
        return self is VerificationStatus.VERIFIED_CURRENT

    @property
    def is_known_to_be_out_of_force(self) -> bool:
        return self in {VerificationStatus.SUPERSEDED, VerificationStatus.REPEALED}


class PageRole(StrEnum):
    """What a page range of a source document contains."""

    NORMATIVE = "normative"
    EXPLANATORY = "explanatory"
    FRONT_MATTER = "front_matter"
    INDEX = "index"
    BACK_MATTER = "back_matter"


@dataclass(frozen=True, slots=True)
class InstrumentId:
    """Stable slug of a legal instrument, e.g. ``ley-27181``."""

    value: str

    def __post_init__(self) -> None:
        if not _SLUG.fullmatch(self.value):
            raise InvariantViolationError(f"Invalid instrument id: {self.value!r}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class VersionId:
    """Stable id of an instrument version, e.g. ``ley-27181@2020-05``."""

    value: str

    def __post_init__(self) -> None:
        if not _VERSION_ID.fullmatch(self.value):
            raise InvariantViolationError(f"Invalid version id: {self.value!r}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Sha256Digest:
    """Lowercase hexadecimal SHA-256 digest that identifies an immutable source file."""

    value: str

    def __post_init__(self) -> None:
        if not _SHA256.fullmatch(self.value):
            raise InvariantViolationError("A SHA-256 digest must be 64 lowercase hex characters")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PageRange:
    """Inclusive range of physical PDF pages (1-based)."""

    first: int
    last: int

    def __post_init__(self) -> None:
        if self.first < 1 or self.last < self.first:
            raise InvariantViolationError(f"Invalid page range: {self.first}-{self.last}")

    def contains(self, page: int) -> bool:
        return self.first <= page <= self.last


@dataclass(frozen=True, slots=True)
class PageSection:
    """A page range with the role of its content (e.g. pages 23-68 are explanatory)."""

    role: PageRole
    pages: PageRange
