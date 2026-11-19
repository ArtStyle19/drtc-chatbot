"""HTTP response models of the content search (the public API contract, in Spanish)."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from drtc_chatbot.contexts.retrieval.application.dto import (
    MatchedPassage,
    SearchFacet,
    SearchMode,
    SearchResponse,
    SearchResult,
)
from drtc_chatbot.contexts.retrieval.application.ports import Segment

Via = Literal["reference", "lexical", "vector"]
Degraded = Literal["vector_unavailable", "vector_not_indexed"]


class SegmentOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    match: bool = Field(description="Verdadero si son palabras que coincidieron con la búsqueda.")

    @classmethod
    def from_segment(cls, segment: Segment) -> SegmentOut:
        return cls(text=segment.text, match=segment.match)


class MatchedPassageOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: str
    citation: str
    page_start: int
    page_end: int
    snippet: list[SegmentOut]

    @classmethod
    def from_passage(cls, passage: MatchedPassage) -> MatchedPassageOut:
        return cls(
            path=passage.path,
            citation=passage.citation,
            page_start=passage.page_start,
            page_end=passage.page_end,
            snippet=[SegmentOut.from_segment(s) for s in passage.snippet],
        )


class SearchResultOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    instrument_id: str
    instrument_short_name: str
    version_id: str = Field(description="Edición aprobada de la que viene el resultado.")
    edition_label: str
    verification_status: str = Field(
        description="Estado de verificación de la edición; solo 'verified_current' es vigente verificado."
    )
    may_be_presented_as_current: bool = Field(
        description="Verdadero solo si la edición fue verificada como vigente."
    )
    unit_path: str = Field(
        description="Unidad de lectura (artículo, disposición o anexo) que se abre."
    )
    path: str = Field(description="Mejor pasaje dentro de la unidad: lo que el lector resalta.")
    kind: str
    label: str
    title: str | None
    citation: str = Field(description="Cita breve generada por el servidor.")
    page_start: int
    page_end: int
    snippet: list[SegmentOut] = Field(description="Fragmento; nunca HTML.")
    matched: list[MatchedPassageOut] = Field(
        description="Pasajes de la unidad que coincidieron (hasta 5), el principal primero."
    )
    via: list[Via] = Field(
        description="Cómo se halló: reference (referencia exacta, siempre al principio), lexical, vector."
    )
    score: float
    debug: dict[str, Any] | None = Field(
        default=None, description="Solo con debug=true en entornos de desarrollo y prueba."
    )

    @classmethod
    def from_result(cls, result: SearchResult, *, include_debug: bool) -> SearchResultOut:
        return cls(
            instrument_id=result.instrument_id,
            instrument_short_name=result.instrument_short_name,
            version_id=result.version_id,
            edition_label=result.edition_label,
            verification_status=result.verification_status,
            may_be_presented_as_current=result.verification_status == "verified_current",
            unit_path=result.unit_path,
            path=result.path,
            kind=result.kind,
            label=result.label,
            title=result.title,
            citation=result.citation,
            page_start=result.page_start,
            page_end=result.page_end,
            snippet=[SegmentOut.from_segment(s) for s in result.snippet],
            matched=[MatchedPassageOut.from_passage(m) for m in result.matched],
            via=[v for v in result.via if v in {"reference", "lexical", "vector"}],
            score=result.score,
            debug=dict(result.debug) if include_debug and result.debug else None,
        )


class SearchFacetOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    instrument_id: str
    short_name: str
    count: int

    @classmethod
    def from_facet(cls, facet: SearchFacet) -> SearchFacetOut:
        return cls(
            instrument_id=facet.instrument_id,
            short_name=facet.instrument_short_name,
            count=facet.count,
        )


class SearchOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    query: str
    mode: SearchMode
    degraded: list[Degraded] = Field(
        description="Por qué se respondió con menos de lo pedido (p. ej. sin búsqueda por significado)."
    )
    total: int = Field(description="Unidades de lectura encontradas (antes del límite).")
    reference: str | None = Field(
        description="Lo que se entendió como referencia, p. ej. 'art. 5'."
    )
    facets: list[SearchFacetOut] = Field(description="Conteo por norma, para el filtro.")
    results: list[SearchResultOut]

    @classmethod
    def from_response(cls, response: SearchResponse, *, include_debug: bool) -> SearchOut:
        return cls(
            query=response.query,
            mode=response.mode,
            degraded=list(response.degraded),
            total=response.total,
            reference=response.reference,
            facets=[SearchFacetOut.from_facet(f) for f in response.facets],
            results=[
                SearchResultOut.from_result(r, include_debug=include_debug)
                for r in response.results
            ],
        )
