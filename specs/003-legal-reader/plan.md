# Implementation Plan: Lector normativo

**Branch**: `003-legal-reader` (apilada sobre `002-corpus-ingestion`) | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md) | **Estado**: ✅ implementado (Sprint 2) · decisión de visor: [ADR-0013](../../docs/architecture/adr/0013-reader-pdfjs-folio-and-reference-lookup.md)

## Summary

El lector es una feature de Angular (`features/reader`) con tres paneles —índice, texto, Folio— sobre
cuatro lecturas nuevas de la API: **índice**, **unidad de lectura** (`reading-unit`: con citas, historial, notas, advertencias y cajas),
**PDF original** y **búsqueda por referencia**. La búsqueda de referencias nace como contexto `retrieval`
(dominio puro: analizador de referencias + resolvedor), que consulta al corpus solo por su fachada
`legal_corpus.api` (capa anticorrupción). El visor usa pdf.js cargado bajo demanda; el resaltado se dibuja
con las cajas que guardó la ingesta.

## Decisiones de diseño

| Tema | Decisión | Por qué |
|---|---|---|
| Identidad pública de una disposición | **Ruta estructural** (`articulo:2/literal:e`) + edición, no el UUID | Es estable entre ediciones, legible y la que cita el usuario; el UUID sigue sirviendo para el historial |
| Unidad de lectura | El backend decide (`reading_unit_path`): artículo, disposición, anexo o contenedor (que además devuelve sus hijos) | El cliente no adivina jerarquías; una sola regla probada |
| Citas | Las genera el backend (`format_citation`/`short_citation`, dominio) y viajan en cada nodo de la unidad de lectura, también en cada texto sustituido | Constitución I.2-3: ninguna cita sale del navegador ni del modelo |
| Advertencias de revisión | Se guardan por revisión (`review_flags`) y la digest las incluye | El reporte de la spec 002 era efímero; el lector debe avisar de un párrafo sustituido sin aplicar |
| PDF | `GET /versions/{id}/source` (solo ediciones aprobadas) con `Range`, `ETag` = SHA-256 (con `304`), verificación de huella cacheada por `(mtime,size)`; puerto `DocumentStorage`. En el cliente, pdf.js con `disableStream` + `disableAutoFetch` | pdf.js pide rangos; en producción el puerto pasa a MinIO sin tocar el caso de uso |
| Resaltado | pdf.js (solo el canvas) y rectángulos HTML sobre la página con `viewport.convertToViewportPoint` (en pdfjs-dist 6 no existe `convertToViewportRectangle`) | Las cajas de pdfium están en puntos del PDF con origen abajo-izquierda (sin rotación en los 3 PDF); no se usa la capa de texto de pdf.js |
| Referencias entre normas | **No** se enlazan automáticamente | Riesgo jurídico de enlazar mal (ver spec, Assumptions) |
| Búsqueda | Contexto `retrieval`: `ReferenceParser` + `NormIndex` (alias desde el manifiesto) + resolvedor puro; puerto `ProvisionDirectory` | Aísla la lógica; es la base de la búsqueda exacta de la spec 004 (RRF: identificador primero) |
| Rutas web | `/biblioteca/:norma?p=<ruta>&v=<edición>` (sin `title` estático: lo fija la página con la disposición leída) | Enlace compartible; `p` evita codificar rutas con `/` en el path |
| Estado de la vista | La URL; `ReaderStore` (SignalStore) con contadores de petición para descartar respuestas superadas | Atrás/Adelante y enlaces funcionan; una respuesta lenta no pisa a una nueva |
| Pantallas pequeñas | Un panel a la vez (Texto/PDF) y el índice como panel desplegable; en ≥ 1024 px, tres columnas | Un solo componente y CSS; sin duplicar contenido |

## Technical Context

**Backend**: FastAPI, SQLAlchemy, migración `0003` (`legal_instruments.aliases`, `provision_versions.review_flags`).
**Frontend**: Angular 22, NgRx SignalStore, `pdfjs-dist` 6 (worker, fuentes y wasm copiados como assets en `/pdfjs/`; JS diferido en un chunk aparte).
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
| VIII Simplicidad | Sin caché ni búsqueda de texto; el índice es una sola petición (hasta 65 kB sin comprimir en el TUO; ~12 kB con gzip, que se activó en nginx para JSON) |

## Project Structure

```text
backend/src/drtc_chatbot/contexts/
├── legal_corpus/
│   ├── domain/{citations,reading}.py
│   ├── application/queries/{get_outline,get_reading_unit,get_source_document,list_provision_index}.py · ports (ReadingStore, DocumentStorage)
│   ├── infrastructure/{sql_reading,local_document_storage}.py
│   └── presentation/http/{router(+outline,reading-unit,source),schemas}.py
└── retrieval/
    ├── domain/{text,ordinals,reference,norms,matching}.py
    ├── application/{ports,dto,lookup_reference}.py
    ├── infrastructure/legal_corpus_directory.py   (usa legal_corpus.api)
    ├── presentation/http/{router,schemas,dependencies}.py      (GET /api/v1/lookup)
    └── api.py
backend/migrations/versions/…_0003_reader_aliases_and_review_flags.py

frontend/src/app/
├── core/http/api-url.ts                              resolveApiUrl (pdf.js no pasa por HttpClient)
├── features/reader/
│   ├── data-access/{reader-api,reader.store,outline-tree,reading-tree,outline-labels,provision-labels}.ts
│   ├── data-access/pdf/{pdf-port,pdfjs-loader}.ts    PdfLoader (puerto) + adaptador pdf.js
│   ├── ui/{outline-tree,container-view,edition-header,provision-node,cite-button,folio}/
│   └── feature/reader-page.*                          página: URL → store, foco, scroll, título
├── features/lookup/{data-access,feature}/             LookupStore + ReferenceSearch (combobox en el encabezado)
└── shared/{ui/validity-seal, util/instrument-labels}  (el sello ya existía)
```

**Structure Decision**: dos contextos de backend (corpus + retrieval) y dos features de frontend (reader + lookup).

## Complexity Tracking

Se agrega el contexto `retrieval` (ya previsto en el mapa de contextos) en lugar de poner la búsqueda
dentro de `legal_corpus`: justificado porque la spec 004 construirá encima y porque el límite se verifica
con import-linter desde ahora.

## Hallazgos de la implementación

Defectos que solo aparecieron al verificar con los PDF reales y con la compilación de producción; las
causas y reglas están en [ADR-0013](../../docs/architecture/adr/0013-reader-pdfjs-folio-and-reference-lookup.md):

- pdf.js descargaba el 100 % del TUO aunque `disableAutoFetch` estaba activo → hace falta además `disableStream`.
- nginx servía el worker `.mjs` como `application/octet-stream` → el visor habría fallado en Docker.
- Dos títulos del TUO arrastraban el número de la llamada a nota (`…N° 1272)115`) → se limpian en el analizador.
- La clase `outline` chocaba con Tailwind; los `<span>` contiguos perdían el espacio al copiar.
- El anexo 2 del RENAT quedaba con 182 caracteres (la tabla se tragaba al anexo) → modo de texto plano + advertencia (spec 002).
