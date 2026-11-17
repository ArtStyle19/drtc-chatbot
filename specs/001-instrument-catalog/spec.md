# Feature Specification: Catálogo de normas con sello de vigencia (walking skeleton)

**Feature Branch**: `001-instrument-catalog`

**Created**: 2026-11-17

**Status**: Implemented (Sprint 0)

**Input**: "Iniciar el proyecto: estructura, documentación y un primer corte de punta a punta que
muestre las normas del corpus y su estado de vigencia."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver las normas disponibles y su estado de vigencia (Priority: P1)

Como personal de la DRTC Puno, quiero ver qué normas contiene el asistente y en qué estado de
verificación está cada edición, para saber en qué medida puedo confiar en ellas.

**Why this priority**: es el primer valor visible y obliga a construir todas las capas
(interfaz → API → caso de uso → adaptador) con las reglas de vigencia desde el día uno.

**Independent Test**: abrir la Biblioteca y comprobar las tres normas con su sello "No verificado".

**Acceptance Scenarios**:

1. **Given** el corpus registra tres normas, **When** abro la Biblioteca, **Then** veo tres tarjetas
   con la referencia formal ("Ley N.° 27181"), el título, la entidad emisora, la fecha de publicación,
   la edición, la fecha de actualización (si se conoce) y el número de páginas.
2. **Given** una edición no verificada frente a la fuente oficial, **When** la veo, **Then** su sello
   dice "No verificado" y nada la describe como vigente.
3. **Given** una edición con advertencias (p. ej. "posiblemente sustituido"), **When** veo su
   tarjeta, **Then** puedo desplegar y leer cada advertencia.
4. **Given** la API no responde, **When** abro la Biblioteca, **Then** veo un mensaje comprensible y
   un botón "Reintentar".

---

### User Story 2 - Integridad de los documentos fuente (Priority: P2)

Como equipo, queremos verificar automáticamente que los PDF originales no cambian, para que toda cita
futura apunte a un documento conocido.

**Why this priority**: es la base de la trazabilidad jurídica (principio I.4 de la constitución).

**Independent Test**: modificar un byte de un PDF (en una copia) o agregar un PDF sin registrar hace
fallar la suite.

**Acceptance Scenarios**:

1. **Given** el manifiesto registra el SHA-256 de cada PDF, **When** corre la suite, **Then** cada
   archivo coincide con su huella.
2. **Given** un PDF en `corpus/sources/` que no está en el manifiesto, **When** corre la suite,
   **Then** la prueba falla.

---

### User Story 3 - Esqueleto técnico verificable (Priority: P3)

Como equipo, queremos health checks, errores estandarizados, contratos de arquitectura y CI, para
construir las siguientes specs sobre bases sólidas.

**Independent Test**: `make check` y `make e2e` en verde.

**Acceptance Scenarios**:

1. **Given** el backend sin base de datos, **When** consulto `/health/ready`, **Then** responde 503
   indicando qué falta; con base de datos, 200.
2. **Given** una ruta inexistente, **When** la llamo, **Then** recibo `application/problem+json` con
   `code` y `request_id`.
3. **Given** una importación que viola la arquitectura, **When** corre `make arch`, **Then** falla.

### Edge Cases

- Manifiesto ausente o mal formado → error claro al cargar el catálogo.
- Una versión que apunta a un documento fuente inexistente → el manifiesto se rechaza.
- Corpus vacío → la Biblioteca muestra un estado vacío explicativo.
- `X-Request-ID` entrante inválido → se reemplaza por uno generado.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE listar todas las normas del corpus con referencia, título, nombre corto,
  entidad emisora, fecha de publicación y su edición de referencia (la más reciente).
- **FR-002**: La API DEBE exponer el listado en `GET /api/v1/instruments` según el contrato
  `backend/openapi.json`.
- **FR-003**: Ninguna edición no verificada DEBE presentarse como vigente
  (`may_be_presented_as_current` es verdadero solo con `verified_current`); la interfaz DEBE mostrar
  el sello de vigencia con palabras.
- **FR-004**: Cada PDF de `corpus/sources/` DEBE coincidir con el SHA-256 del manifiesto y todo PDF
  DEBE estar registrado.
- **FR-005**: Los errores de la API DEBEN seguir RFC 9457 con `code` estable y `request_id`.
- **FR-006**: El backend DEBE ofrecer `/health/live` y `/health/ready` (base de datos + manifiesto).
- **FR-007**: La interfaz DEBE mostrar un aviso global de corpus de prueba no verificado (texto fijo en
  este sprint; derivado de los datos en la spec 003).
- **FR-008**: Las advertencias de cada edición DEBEN ser visibles para el usuario.

### Key Entities

- **LegalInstrument (norma):** id, tipo, número, título, nombre corto, entidad emisora, fecha de
  publicación, versiones.
- **InstrumentVersion (edición):** id, etiqueta, fecha de consolidación, nota, estado de verificación,
  documento fuente, secciones de páginas (normativa, explicativa, índice…), advertencias.
- **SourceDocument (PDF):** id, archivo, nombre original, SHA-256, páginas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una persona del personal identifica el estado de verificación de cada norma en menos de
  10 segundos, sin ayuda.
- **SC-002**: La Biblioteca no tiene violaciones serias o críticas de accesibilidad (axe, WCAG 2.2 AA).
- **SC-003**: El 100 % de los PDF del corpus se verifican en cada ejecución de la suite.
- **SC-004**: `make check` termina en verde en un entorno limpio siguiendo solo el README.

## Assumptions

- Sin autenticación en esta etapa (ADR-0007).
- El catálogo se lee de `corpus/manifest.yaml`; PostgreSQL se usará desde la spec 002.
- Las tres ediciones iniciales están desactualizadas y se marcan `unverified` (inventario del corpus).
