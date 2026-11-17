# Contexto `legal_corpus` — Corpus normativo (dominio principal)

**Responsabilidad:** saber qué normas existen, qué versiones (ediciones) tenemos de cada una, de qué
PDF salió cada versión y **cuál es su estado de vigencia verificado**. Es la fuente de verdad jurídica:
el índice de búsqueda (`retrieval`) se deriva de aquí y puede reconstruirse.

| Término (ES) | Código (EN) | Nota |
|---|---|---|
| Norma / instrumento jurídico | `LegalInstrument` | Raíz del agregado |
| Versión / edición | `InstrumentVersion` | Inmutable; se reemplaza vía la raíz |
| Documento fuente (PDF) | `SourceDocumentRef` | Identificado por SHA-256 |
| Estado de verificación | `VerificationStatus` | Solo `verified_current` se presenta como vigente |
| Rango de páginas y su rol | `PageSection` / `PageRole` | Distingue texto normativo de material explicativo |

**Expone (`api.py`):** `ListLegalInstruments`, `LegalInstrumentSummary`, `EditionSummary`.

**Hoy (spec 001):** el catálogo se lee de `corpus/manifest.yaml` (`ManifestInstrumentCatalog`).
**Spec 002:** disposiciones (`Provision`, `ProvisionVersion`), eventos normativos y repositorio PostgreSQL.
