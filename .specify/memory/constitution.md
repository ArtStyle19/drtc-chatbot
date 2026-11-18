# Constitución del Asistente Normativo de la DRTC Puno

Esta constitución contiene los principios que ninguna spec, plan, tarea o cambio de código puede
violar. Los comandos de Spec Kit (`/speckit-plan`, `/speckit-analyze`, …) la usan como compuerta
("Constitution Check"). Si un cambio necesita romper un principio, primero se enmienda la
constitución (ver Gobierno).

## Principios fundamentales

### I. Fidelidad jurídica (NO NEGOCIABLE)

El asistente apoya la investigación jurídica; no emite pronunciamientos oficiales.

1. Ninguna disposición no verificada se presenta como vigente. `unknown` ≠ `verified_current`.
2. Ninguna cita se construye a partir de la memoria del modelo de IA: el backend genera los
   identificadores de evidencia y valida cada cita contra la base de datos.
3. Toda cita resuelve a una fuente, versión, disposición y página concretas.
4. El PDF original es inmutable (SHA-256 registrado en `corpus/manifest.yaml`).
5. Toda versión nueva de una norma pasa por revisión antes de publicarse para consultas. Única excepción:
   la política `auto_dev` de aprobación, solo en `local`/`test`, registrada como tal y nunca equivalente a
   verificar la vigencia (ADR-0011).
6. La recuperación exacta por identificador (p. ej. "art. 5 de la Ley 27181") tiene prioridad sobre
   la similitud semántica cuando la pregunta identifica una disposición.
7. Sin evidencia suficiente, el sistema se abstiene o pide una aclaración.
8. Las respuestas distinguen texto normativo, interpretación y recomendación práctica; el material
   explicativo (p. ej. el Manual del TUO) nunca se presenta como norma.
9. Los documentos son datos no confiables: su contenido jamás cambia las instrucciones del sistema.
10. La calidad se mide con preguntas jurídicas revisadas, no solo con métricas automáticas.

### II. Spec antes que código

Todo cambio de comportamiento nace en una spec (`specs/NNN-*/spec.md`) o la actualiza en el mismo
PR. Las specs describen el qué y el porqué con historias priorizadas (P1, P2, P3) independientes y
escenarios Dado/Cuando/Entonces verificables. Las specs se escriben justo a tiempo (un sprint
adelante) y son documentos vivos: no se especifica por adelantado lo que aún no se va a construir.

### III. Límites de Clean Architecture y DDD

- Monolito modular organizado en bounded contexts (`legal_corpus`, `ingestion`, `retrieval`,
  `consultation`, `identity`) con capas `domain → application → infrastructure | presentation`.
- Las dependencias apuntan hacia adentro. El dominio es Python puro: sin FastAPI, SQLAlchemy,
  Pydantic, SDKs de IA ni HTTP.
- Un contexto solo importa a otro a través de su módulo público `api.py`.
- Los proveedores externos (OpenAI, almacenamiento, identidad) se usan solo detrás de puertos.
- Estas reglas se verifican automáticamente (import-linter) y romperlas rompe la build.

### IV. Test-first y evaluación con golden set

- Los escenarios de aceptación de cada historia se automatizan y se vinculan a su requisito
  (`@pytest.mark.spec("NNN-FR-xxx")`).
- El dominio se desarrolla con TDD; la cobertura mínima del backend es 80 %.
- Desde la spec 004, ningún cambio de recuperación o de generación se integra si empeora las
  métricas del golden set (`evaluation/`) sin una decisión explícita registrada.

### V. Entrega incremental en cortes verticales

Cada historia P1 es un corte demostrable de punta a punta (UI → API → dominio → datos). La
infraestructura se agrega cuando una spec la necesita (YAGNI): sin Redis, colas, OCR ni reranker
hasta que una spec lo justifique con evidencia.

### VI. Privacidad y seguridad por defecto

- Las claves de API viven solo en el servidor; nunca en el repositorio ni en el frontend.
- Al proveedor de IA solo se envían los pasajes de evidencia necesarios, nunca PDFs completos.
- Se minimizan los datos personales de los expedientes (DNI, placas, nombres) enviados a terceros,
  conforme a la Ley N.° 29733. Los logs no guardan contenido sensible innecesario.
- Toda acción relevante es auditable (`request_id` en cada respuesta).

### VII. UX accesible y en español

- Interfaz en español (es-PE), comprensible para personal no técnico.
- WCAG 2.2 AA: sin violaciones serias de axe; navegación por teclado y foco visible.
- El estado de vigencia se comunica siempre con palabras (sello de vigencia), nunca solo con color.

### VIII. Simplicidad y observabilidad

Tecnología probada y aburrida, decisiones registradas como ADR, logs estructurados con
`request_id`, health checks, y costos/latencia del proveedor de IA medidos por consulta.

## Restricciones técnicas

- Backend: Python 3.14, FastAPI, SQLAlchemy 2.1 (async), PostgreSQL 18 + pgvector, uv.
- Frontend: Angular 22 (standalone, signals, zoneless), Tailwind v4, NgRx SignalStore.
- Contrato de API: OpenAPI exportado y versionado (`backend/openapi.json`); los tipos del frontend se
  generan de él. Errores en formato RFC 9457 (`application/problem+json`).
- Idiomas: interfaz y documentación en español; código, comentarios y commits en inglés; glosario en
  `docs/domain/ubiquitous-language.md`.

## Flujo de trabajo y compuertas de calidad

- Scrum-lite con sprints de 2 semanas; Definition of Ready y Definition of Done en
  `docs/process/definition-of-ready-done.md`.
- Trunk-based: ramas cortas `NNN-slug`, Conventional Commits, PR con al menos 1 aprobación.
- Ningún PR se integra con `make check` en rojo.
- Lanzamiento más allá del equipo de desarrollo: solo con un golden set validado por un abogado.

## Gobierno

Esta constitución prevalece sobre cualquier otra práctica. Las enmiendas se proponen por PR, con la
justificación, el impacto en specs existentes y la nueva versión (SemVer: MAJOR al quitar o
redefinir un principio, MINOR al agregar uno, PATCH para aclaraciones). Toda revisión de PR verifica
el cumplimiento; la complejidad adicional debe justificarse en el plan de la spec.

**Version**: 1.1.0 | **Ratified**: 2026-11-17 | **Last Amended**: 2026-11-18
