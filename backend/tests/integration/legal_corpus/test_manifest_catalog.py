from pathlib import Path

import pytest

from drtc_chatbot.contexts.legal_corpus.domain.value_objects import (
    PageRole,
    VerificationStatus,
)
from drtc_chatbot.contexts.legal_corpus.infrastructure.manifest_catalog import (
    CorpusManifestError,
    ManifestInstrumentCatalog,
)
from tests.conftest import CORPUS_MANIFEST


@pytest.mark.spec("001-FR-001")
async def test_the_real_manifest_describes_the_three_initial_instruments() -> None:
    instruments = await ManifestInstrumentCatalog(CORPUS_MANIFEST).list_instruments()

    assert [str(instrument.id) for instrument in instruments] == [
        "ley-27181",
        "ds-017-2009-mtc",
        "tuo-ley-27444",
    ]


@pytest.mark.spec("001-FR-003")
async def test_no_initial_edition_is_verified_yet() -> None:
    instruments = await ManifestInstrumentCatalog(CORPUS_MANIFEST).list_instruments()

    statuses = {instrument.latest_version.verification_status for instrument in instruments}
    assert statuses == {VerificationStatus.UNVERIFIED}


async def test_the_tuo_manual_is_marked_as_explanatory_material() -> None:
    instruments = await ManifestInstrumentCatalog(CORPUS_MANIFEST).list_instruments()
    tuo = next(instrument for instrument in instruments if str(instrument.id) == "tuo-ley-27444")

    assert tuo.latest_version.role_of_page(30) is PageRole.EXPLANATORY
    assert tuo.latest_version.role_of_page(119) is PageRole.NORMATIVE


async def test_a_missing_manifest_is_reported_clearly(tmp_path: Path) -> None:
    with pytest.raises(CorpusManifestError, match="not found"):
        await ManifestInstrumentCatalog(tmp_path / "nope.yaml").list_instruments()


async def test_a_version_pointing_to_an_unknown_source_is_rejected(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        """
schema_version: 1
updated_on: 2026-11-17
sources: []
instruments:
  - id: ley-1
    type: ley
    number: "1"
    title: Ley de prueba
    short_name: Ley 1
    issuing_authority: Congreso
    versions:
      - id: ley-1@v1
        source: src-missing
        edition_label: Edición de prueba
        verification_status: unverified
""",
        encoding="utf-8",
    )

    with pytest.raises(CorpusManifestError, match="unknown source"):
        await ManifestInstrumentCatalog(manifest).list_instruments()
