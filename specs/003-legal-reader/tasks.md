# Tasks: Lector normativo

**Input**: [spec.md](spec.md), [plan.md](plan.md) · `[P]` = paralelizable

## Phase 1: Setup y datos

- [x] T001 Migración `0003`: `legal_instruments.aliases`, `provision_versions.review_flags`; alias en el manifiesto y su esquema
- [x] T002 Ingesta: advertencias por disposición (`flags`), cajas de la continuación, digest incluye flags; re-ingesta

## Phase 2: Backend del corpus (US1, US2, US4)

- [x] T003 [P] Dominio: `CitationFormatter` (breve y formal) y `reading_unit_path`
- [x] T004 Consultas: `GetOutline`, `GetReadingUnit` (cita, historial, notas, advertencias, cajas) + SQL
- [x] T005 `DocumentStorage` + `LocalDocumentStorage` (SHA-256 verificado, sin rutas del cliente) + `GetSourceDocument`
- [x] T006 HTTP: `GET /instruments/{id}/outline`, `/reading-unit`, `GET /versions/{id}/source`; la cita viaja en cada nodo de la unidad de lectura (no hay endpoint de detalle aparte)
- [x] T007 Tests: dominio, casos de uso, SQL, e2e (Range, ETag, 404 de pendientes, huella alterada)

## Phase 3: Búsqueda por referencia (US3)

- [x] T008 `retrieval` dominio: normalizador, `ReferenceParser`, `NormIndex`, resolvedor
- [x] T009 `LookupReference` + `LegalCorpusDirectory` + `GET /lookup`; cableado y contratos de arquitectura
- [x] T010 Tests con referencias reales (equivalentes, ambiguas, inexistentes, no-referencias) y el golden set (SC-003)

## Phase 4: Frontend (US1-US5)

- [x] T011 Dependencias (`pdfjs-dist`), assets del visor, tipos regenerados, rutas `/biblioteca/:norma`
- [x] T012 Índice (`OutlineTree`) y página del lector; enlace desde las tarjetas
- [x] T013 Lectura: subárbol anidado, selección, historial sustituido, notas y advertencias
- [x] T014 Folio con pdf.js: página, zoom, resaltado, errores
- [x] T015 `ReferenceSearch` en el encabezado (teclado y lectores de pantalla)
- [x] T016 "Copiar cita" (breve/formal) con confirmación anunciada
- [x] T017 Responsive (alternador Texto/PDF, índice desplegable) y estados de carga/vacío/error

## Phase 5: Verificación y cierre

- [x] T018 Vitest (stores, utilidades de cajas, componentes); Playwright con API simulada + axe
- [x] T019 Playwright contra la API real: el PDF se renderiza y el resaltado coincide con la capa de texto (SC-002)
- [x] T020 Revisión visual (escritorio y móvil) y de accesibilidad; presupuesto de carga (SC-004: 2,4 % del TUO)
- [x] T021 Documentación: ADR, `frontend.md`, `ingestion.md`, README, roadmap, glosario; `make check` y `make e2e`

## Notas del cierre

- Todas las tareas están hechas salvo la medición **SC-001** (< 15 s con personas), que no puede hacerla el
  equipo de desarrollo: ver *Resultados* en la [spec](spec.md#resultados-sprint-2).
- Cambios de alcance respecto de lo planeado: `GetSubtree` → `GetReadingUnit`; las citas viajan en la
  unidad de lectura; se añadió `ListProvisionIndex` (índice para la búsqueda por referencia); gzip en
  nginx para JSON; regla de nginx para `.mjs`; limpieza de llamadas a nota en títulos del TUO.
