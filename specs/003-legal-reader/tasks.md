# Tasks: Lector normativo

**Input**: [spec.md](spec.md), [plan.md](plan.md) · `[P]` = paralelizable

## Phase 1: Setup y datos

- [ ] T001 Migración `0003`: `legal_instruments.aliases`, `provision_versions.review_flags`; alias en el manifiesto y su esquema
- [ ] T002 Ingesta: advertencias por disposición (`flags`), cajas de la continuación, digest incluye flags; re-ingesta

## Phase 2: Backend del corpus (US1, US2, US4)

- [ ] T003 [P] Dominio: `CitationFormatter` (breve y formal) y `reading_unit_path`
- [ ] T004 Consultas: `GetOutline`, `GetSubtree` (cita, notas, advertencias, cajas) + SQL
- [ ] T005 `DocumentStorage` + `LocalDocumentStorage` (SHA-256 verificado, sin rutas del cliente) + `GetSourceDocument`
- [ ] T006 HTTP: `GET /instruments/{id}/outline`, `/subtree`, `GET /versions/{id}/source`; cita en el detalle
- [ ] T007 Tests: dominio, casos de uso, SQL, e2e (Range, ETag, 404 de pendientes, huella alterada)

## Phase 3: Búsqueda por referencia (US3)

- [ ] T008 `retrieval` dominio: normalizador, `ReferenceParser`, `NormIndex`, resolvedor
- [ ] T009 `LookupReference` + `LegalCorpusDirectory` + `GET /lookup`; cableado y contratos de arquitectura
- [ ] T010 Tests con referencias reales (equivalentes, ambiguas, inexistentes, no-referencias) y el golden set (SC-003)

## Phase 4: Frontend (US1-US5)

- [ ] T011 Dependencias (`pdfjs-dist`), assets del visor, tipos regenerados, rutas `/biblioteca/:norma`
- [ ] T012 Índice (`OutlineTree`) y página del lector; enlace desde las tarjetas
- [ ] T013 Lectura: subárbol anidado, selección, historial sustituido, notas y advertencias
- [ ] T014 Folio con pdf.js: página, zoom, resaltado, errores
- [ ] T015 `ReferenceSearch` en el encabezado (teclado y lectores de pantalla)
- [ ] T016 "Copiar cita" (breve/formal) con confirmación anunciada
- [ ] T017 Responsive (pestañas Texto/Fuente, índice desplegable) y estados de carga/vacío/error

## Phase 5: Verificación y cierre

- [ ] T018 Vitest (stores, utilidades de cajas, componentes); Playwright con API simulada + axe
- [ ] T019 Playwright contra la API real: el PDF se renderiza y el resaltado coincide con la capa de texto (SC-002)
- [ ] T020 Revisión visual (escritorio y móvil) y de accesibilidad; presupuesto de carga (SC-004)
- [ ] T021 Documentación: ADR, `frontend.md`, `ingestion.md`, README, roadmap, glosario; `make check` y `make e2e`
