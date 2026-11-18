# Feature Specification: Ingesta del corpus en disposiciones estructuradas

**Feature Branch**: `002-corpus-ingestion`

**Created**: 2026-11-17

**Status**: Clarified (Sprint 1, 2026-11-18) — decisiones en la sección *Clarifications*

**Input**: "Convertir los PDF del corpus en disposiciones estructuradas (artículo, numeral, literal),
con su página exacta y su estado de vigencia, revisables por una persona antes de usarse."

## Clarifications

Sesión 2026-11-18 (responsable de producto / revisor jurídico):

- **Alcance del sprint:** esta spec completa para las tres normas; la interfaz del lector es la spec 003.
- **Aprobación (FR-005):** en desarrollo se aprueba automáticamente (política `auto_dev`), con
  aprobación manual disponible desde el primer día (`approve`). La política `auto_dev` se rechaza en
  `staging` y `production`; cada aprobación registra su modo (`human` / `auto_dev`). Aprobar no es
  verificar: la vigencia sigue `unverified`. Ver ADR-0011.
- **Manual del TUO (FR-006):** se excluye por completo; solo se ingieren las páginas normativas 71-284.
- **Notas "(*)" y concordancias (FR-007):** se conservan como notas editoriales; aún no se muestran.
- **Granularidad (FR-008):** hasta literal (a, b, c) y numeral; el artículo es el padre.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ley 27181 estructurada y revisable (Priority: P1)

Como revisor jurídico, quiero que la Ley 27181 se convierta en disposiciones con su página exacta y
que los textos sustituidos queden marcados, para revisar y aprobar el resultado antes de que se use en
consultas.

**Why this priority**: es la norma más corta (36 páginas) pero contiene el caso más difícil
(textos originales y modificados intercalados); resolverla valida el modelo de datos.

**Independent Test**: ejecutar la ingesta de la Ley 27181 y revisar el reporte: cada artículo con su
página; el art. 2 con su texto sustituido marcado y su texto vigente según el DU 019-2020.

**Acceptance Scenarios**:

1. **Given** el PDF de la Ley 27181 registrado en el manifiesto, **When** ejecuto la ingesta,
   **Then** obtengo cada artículo, numeral y literal con su ruta estructural y sus páginas.
2. **Given** el art. 2 aparece en su redacción original y en la modificada por el DU 019-2020,
   **When** termina la ingesta, **Then** la original queda como `superseded` y existe un evento
   normativo que lo explica; nunca ambas como texto de la versión.
3. **Given** que ejecuto la ingesta dos veces con el mismo PDF, **Then** el resultado es idéntico y no
   se duplican datos (idempotencia por SHA-256).
4. **Given** un reporte de revisión generado, **When** el revisor lo aprueba, **Then** la versión queda
   disponible para la búsqueda; mientras no se apruebe, no lo está.

---

### User Story 2 - RENAT con anexos (Priority: P2)

Como especialista de SDT/DCT, quiero el RENAT estructurado (secciones, títulos, artículos,
disposiciones complementarias y anexos), para ubicar requisitos y condiciones por su número.

**Independent Test**: los 138 artículos, las disposiciones complementarias y los anexos 1 y 2 aparecen
con sus páginas.

**Acceptance Scenarios**:

1. **Given** el PDF del RENAT, **When** ejecuto la ingesta, **Then** obtengo 138 artículos, las
   disposiciones complementarias finales, transitorias y derogatorias, y los anexos como unidades
   propias.

---

### User Story 3 - TUO de la Ley 27444 sin confundir el Manual con la norma (Priority: P3)

Como abogada de la OAJ, quiero que el texto del TUO se distinga del Manual explicativo, para que
nunca se cite el Manual como si fuera ley.

**Acceptance Scenarios**:

1. **Given** el PDF del TUO, **When** ejecuto la ingesta, **Then** solo las páginas normativas
   (71-284) generan disposiciones normativas; el Manual (23-68) queda como material explicativo.

---

### User Story 4 - Registrar una edición oficial nueva sin perder la anterior (Priority: P3)

Como revisor jurídico, quiero cargar el texto vigente oficial (SPIKE-01) como nueva versión y marcar
la anterior como sustituida, para mantener la trazabilidad.

### Edge Cases

- Notas "(*)" que no modifican el texto (p. ej. prórrogas COVID-19 al inicio de la Ley 27181).
- Artículos cuyo número cambia entre ediciones (TUO 2019 vs. TUO 2026).
- Encabezados y pies de página repetidos que no deben entrar al texto.
- Disposiciones que cruzan páginas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La ingesta DEBE identificar títulos, capítulos, artículos, numerales y literales, con
  ruta estructural estable.
- **FR-002**: Cada disposición DEBE registrar página física inicial y final, y las coordenadas de su
  texto para resaltarlo en el visor (spec 003).
- **FR-003**: Los textos sustituidos DEBEN quedar `superseded` con su `LegalEvent`; nunca dos textos
  de una misma disposición como vigentes.
- **FR-004**: La ingesta DEBE ser idempotente por SHA-256 y no modificar nunca el PDF original.
- **FR-005**: Una versión DEBE estar aprobada antes de quedar disponible para consultas. La política
  de aprobación es configurable (`manual` | `auto_dev`); `auto_dev` solo se permite en `local` y
  `test`. Cada aprobación registra modo, responsable y fecha, y la aprobación no cambia el estado de
  verificación.
- **FR-006**: El material explicativo (Manual del TUO, páginas 23-68) NO se ingiere: solo los rangos
  de páginas con rol `normative` del manifiesto generan disposiciones.
- **FR-007**: Las notas "(*)", las notas al pie del TUO y los bloques CONCORDANCIAS DEBEN conservarse
  como notas editoriales vinculadas a su disposición (todavía no se muestran al usuario).
- **FR-008**: La granularidad mínima de una disposición es el literal (a, b, c); el numeral (2.1) y el
  artículo son sus ancestros.
- **FR-010**: La API DEBE exponer solo disposiciones de versiones aprobadas, con su estado de
  verificación y el modo de aprobación (`GET /api/v1/instruments/{id}/provisions`,
  `GET /api/v1/provisions/{id}`).
- **FR-009**: La ingesta DEBE producir un reporte de revisión legible (por norma: conteos, rangos de
  páginas, textos sustituidos detectados, anomalías).

### Key Entities

- **SourceDocument**, **IngestionJob** (recibido → extraído → analizado → en revisión → aprobado →
  publicado / fallido), **Provision**, **ProvisionVersion**, **LegalEvent**, **AmendmentNote**,
  **ReviewReport**.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En una muestra de 20 disposiciones por norma revisada por una persona, el 100 % tiene la
  página correcta y el texto completo.
- **SC-002**: 0 disposiciones con dos textos vigentes simultáneos.
- **SC-003**: Reejecutar la ingesta produce exactamente el mismo resultado.
- **SC-004**: La ingesta completa de las tres normas tarda menos de 2 minutos en un equipo de desarrollo.
- **SC-005**: Las 10 preguntas del golden set se localizan: su texto de respaldo está dentro de la
  disposición analizada y en la página citada.

## Assumptions

- Los tres PDF tienen capa de texto: PyMuPDF basta; OCR fuera de alcance.
- La ingesta se ejecuta por CLI (Typer); la interfaz de administración llega en la spec 008.
- Los resultados se guardan en PostgreSQL; `corpus/manifest.yaml` es la semilla (`drtc-ingest sync`) y
  sigue registrando los documentos fuente.
- Extracción con pypdfium2 (licencia permisiva; ver ADR-0012).
