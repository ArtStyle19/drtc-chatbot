# Tasks: Ingesta del corpus en disposiciones estructuradas

**Input**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md) · `[P]` = paralelizable

## Phase 1: Setup

- [x] T001 Spike de extracción (pypdfium2 vs pdfplumber) y ADR-0012
- [x] T002 Aclarar la spec y resolver los `[NEEDS CLARIFICATION]` (sesión 2026-11-18)
- [x] T003 Dependencias `pypdfium2`, `typer`; target `make test-db` (PostgreSQL en red de host)

## Phase 2: Foundational

- [x] T004 Migración `0002` (instrumentos, versiones, disposiciones, revisiones, notas, jobs) con índice único parcial de texto vigente
- [x] T005 Dominio de `legal_corpus`: `ProvisionRevision`, `validate_revision_set`, `Approval`, `ApprovalPolicy`
- [x] T006 `Settings`: política de aprobación con validación (`auto_dev` prohibida en staging/producción)

## Phase 3: User Story 1 — Ley 27181 estructurada y revisable (P1) 🎯

- [x] T007 Modelo y motor del analizador (`ingestion/domain/parsing`): artículos, numerales, ítems, literales, rutas estables
- [x] T008 Sustituciones e incorporaciones por bloques citados; eventos legales desde las notas; reporte de anomalías (párrafos sustituidos)
- [x] T009 `PdfiumTextExtractor` (líneas, cajas y tamaño de letra)
- [x] T010 `legal_corpus`: `SyncCorpusManifest`, `PublishProvisions`, `ApproveInstrumentVersion`, `SqlLegalCorpusStore`
- [x] T011 `RunIngestion`, `IngestionJob`, `ReviewReport`, `CorpusGateway` (solo vía `legal_corpus.api`)
- [x] T012 CLI `drtc-ingest` (`sync`, `run`, `report`, `approve`, `sample`)
- [x] T013 API: `GET /instruments/{id}/provisions`, `GET /provisions/{id}`; OpenAPI y tipos del frontend regenerados
- [x] T014 Tests: unitarias, PostgreSQL, e2e (API y CLI), invariantes

## Phase 4: User Story 2 — RENAT (P2)

- [x] T015 Perfil `renat`: decreto aprobatorio como preámbulo, encabezados sin `.-`, numerales de 3 niveles, anexos como unidades
- [x] T016 138 artículos sin saltos (+ `12-A`); NOTA SPIJ; párrafos sustituidos marcados

## Phase 5: User Story 3 — TUO Ley 27444 (P3)

- [x] T017 Perfil `tuo-lpag`: páginas normativas 71-284 (Manual excluido), arranque en "TÍTULO PRELIMINAR", artículos romanos, ítems `1.` `2.`
- [x] T018 Notas al pie por tamaño de letra (incluye notas con el texto anterior de varias páginas)

## Phase 6: User Story 4 — nueva edición sin perder la anterior (P3)

- [x] T019 Un `content_digest` distinto reemplaza las revisiones de esa edición y vuelve a `pending`; las ediciones son filas independientes (`ordinal`); `sync` rechaza un PDF cuyo hash cambió
- [ ] T020 Carga real de la edición oficial vigente (**SPIKE-01**, la hace el responsable del proyecto)

## Phase 7: Polish & criterios

- [x] T021 Aceptación del golden set (SC-005): 10/10 preguntas localizadas en las páginas citadas
- [x] T022 `compose`: servicio `ingest` entre `migrate` y `backend`; documentación, ADR-0011, constitución 1.1.0
- [ ] T023 **SC-001**: revisión manual de 20 disposiciones por norma (`drtc-ingest sample … -n 20`) contra el PDF — **pendiente del revisor jurídico**
- [ ] T024 Resolver con el revisor los casos marcados (ver `docs/domain/corpus-inventory.md`, § Resultado de la ingesta)
