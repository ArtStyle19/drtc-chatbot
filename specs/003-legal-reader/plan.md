# Implementation Plan: Lector normativo

**Branch**: `003-legal-reader` (apilada sobre `002-corpus-ingestion`) | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

## Summary

El lector es una feature de Angular (`features/reader`) con tres paneles —índice, texto, Folio— sobre
cuatro lecturas nuevas de la API: **índice**, **subárbol** (con citas, notas, advertencias y cajas),
**PDF original** y **búsqueda por referencia**. La búsqueda de referencias nace como contexto `retrieval`
(dominio puro: analizador de referencias + resolvedor), que consulta al corpus solo por su fachada
`legal_corpus.api` (capa anticorrupción). El visor usa pdf.js cargado bajo demanda; el resaltado se dibuja
con las cajas que guardó la ingesta.

## Decisiones de diseño

| Tema | Decisión | Por qué |
|---|---|---|
| Identidad pública de una disposición | **Ruta estructural** (`articulo:2/literal:e`) + edición, no el UUID | Es estable entre ediciones, legible y la que cita el usuario; el UUID sigue sirviendo para el historial |
| Unidad de lectura | El backend decide (`reading_unit_path`): artículo, disposición, anexo o contenedor | El cliente no adivina jerarquías; una sola regla probada |
| Citas | Las genera el backend (`CitationFormatter`, dominio) y viajan en cada disposición | Constitución I.2-3: ninguna cita sale del navegador ni del modelo |
| Advertencias de revisión | Se guardan por revisión (`review_flags`) y la digest las incluye | El reporte de la spec 002 era efímero; el lector debe avisar de un párrafo sustituido sin aplicar |
| PDF | `GET /versions/{id}/source` (solo ediciones aprobadas) con `Range`, `ETag` = SHA-256, verificación de huella cacheada por `(mtime,size)`; puerto `DocumentStorage` | pdf.js pide rangos; en producción el puerto pasa a MinIO sin tocar el caso de uso |
| Resaltado | pdf.js (canvas + capa de texto) y rectángulos sobre la página con `viewport.convertToViewportRectangle` | Las cajas de pdfium están en espacio de usuario del PDF (origen 0,0; sin rotación en los 3 PDF) |
| Referencias entre normas | **No** se enlazan automáticamente | Riesgo jurídico de enlazar mal (ver spec, Assumptions) |
| Búsqueda | Contexto `retrieval`: `ReferenceParser` + `NormIndex` (alias desde el manifiesto) + resolvedor puro; puerto `ProvisionDirectory` | Aísla la lógica; es la base de la búsqueda exacta de la spec 004 (RRF: identificador primero) |
| Rutas web | `/biblioteca/:norma?p=<ruta>&v=<edición>` | Enlace compartible; `p` evita codificar rutas con `/` en el path |

## Technical Context

**Backend**: FastAPI, SQLAlchemy, migración `0003` (`legal_instruments.aliases`, `provision_versions.review_flags`).
**Frontend**: Angular 22, NgRx SignalStore, `pdfjs-dist` 6 (worker, cmaps y fuentes copiados como assets; JS diferido).
**Testing**: pytest (unit, real PDFs, PostgreSQL, e2e), Vitest, Playwright + axe (API simulada **y** API real con medición de alineación del resaltado).
**Constraints**: nada no verificado como vigente; PDFs inmutables; sin rutas de archivo del cliente; WCAG 2.2 AA.

## Constitution Check

| Principio | Cumplimiento |
|---|---|
| I.1 vigencia | El sello y el aviso de edición están en el encabezado del lector; la cita formal dice "no verificada"; prueba SC-006 |
| I.2-3 citas | Generadas por el backend, con ruta, edición y página; el historial sustituido rotulado "no vigente" |
| I.4 PDF inmutable | El servidor verifica el SHA-256 antes de entregar |
| I.6 exacta primero | La búsqueda por referencia es determinista, sin similitud |
| III Clean Architecture | `retrieval` solo importa `legal_corpus.api`; `DocumentStorage` es un puerto; 6 contratos en verde |
| IV Test-first | Casos del analizador de referencias a partir de ejemplos reales; alineación del resaltado medida en el navegador |
| V Cortes verticales | US1 (leer) → US2 (Folio) → US3 (buscar) → US4 (citar) |
| VII UX accesible | axe sin violaciones serias, teclado, móvil |
| VIII Simplicidad | Sin caché ni búsqueda de texto; el índice es una sola petición (< 40 kB) |

## Project Structure

```text
backend/src/drtc_chatbot/contexts/
├── legal_corpus/
│   ├── domain/{citations,reading}.py
│   ├── application/queries/{get_outline,get_subtree,get_source_document}.py · ports (DocumentStorage)
│   ├── infrastructure/{sql_store(+outline,subtree,source),local_document_storage}.py
│   └── presentation/http/{router(+outline,subtree,source),schemas}.py
└── retrieval/
    ├── domain/{text,reference,norms,matching}.py
    ├── application/{ports,lookup_reference}.py
    ├── infrastructure/legal_corpus_directory.py   (usa legal_corpus.api)
    ├── presentation/http/{router,schemas}.py      (GET /api/v1/lookup)
    └── api.py
backend/migrations/versions/…_0003_reader_aliases_and_review_flags.py

frontend/src/app/
├── features/reader/{data-access,feature,ui}/       índice · texto · Folio · cita · notas
├── features/lookup/{data-access,ui}/               ReferenceSearch (en el encabezado)
└── shared/ui/…                                      (ValiditySeal ya existe)
```

**Structure Decision**: dos contextos de backend (corpus + retrieval) y dos features de frontend (reader + lookup).

## Complexity Tracking

Se agrega el contexto `retrieval` (ya previsto en el mapa de contextos) en lugar de poner la búsqueda
dentro de `legal_corpus`: justificado porque la spec 004 construirá encima y porque el límite se verifica
con import-linter desde ahora.
