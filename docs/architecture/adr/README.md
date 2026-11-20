# Registro de decisiones de arquitectura (ADR)

Formato [MADR](https://adr.github.io/madr/). Un ADR aceptado no se edita: si la decisión cambia, se
crea uno nuevo que lo sustituye y se actualiza el estado del anterior.

| N.° | Decisión | Estado |
|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Registrar las decisiones de arquitectura con ADR | Aceptada |
| [0002](0002-modular-monolith-clean-architecture.md) | Monolito modular con bounded contexts y Clean Architecture | Aceptada |
| [0003](0003-monorepo.md) | Monorepo con backend, frontend, specs, docs, corpus y evaluación | Aceptada |
| [0004](0004-spec-driven-development-scrum-lite.md) | Spec-Driven Development (Spec Kit) + Scrum-lite | Aceptada |
| [0005](0005-postgresql-pgvector-single-datastore.md) | PostgreSQL 18 + pgvector + FTS como único almacén | Aceptada |
| [0006](0006-openai-behind-ports-validated-citations.md) | OpenAI detrás de puertos; citas validadas por el backend | Aceptada |
| [0007](0007-no-authentication-in-mvp.md) | Sin autenticación en el MVP; puerto de identidad | Aceptada |
| [0008](0008-angular-frontend-architecture.md) | Frontend Angular 22 con features autocontenidas | Aceptada |
| [0009](0009-corpus-validity-and-versioning.md) | Modelo de vigencia y versiones del corpus | Aceptada |
| [0010](0010-deviations-from-reference-architecture.md) | Diferencias con la arquitectura de referencia | Aceptada |
| [0011](0011-ingestion-approval-policy.md) | Política de aprobación de la ingesta (auto en desarrollo) | Aceptada |
| [0012](0012-pypdfium2-for-pdf-extraction.md) | pypdfium2 para la extracción de texto de los PDF | Aceptada |
| [0013](0013-reader-pdfjs-folio-and-reference-lookup.md) | Lector: visor pdf.js (Folio), la URL como estado y búsqueda por referencia determinista | Aceptada |
| [0014](0014-hybrid-search-and-evaluation.md) | Búsqueda por contenido híbrida (referencia + palabras + significado + RRF), con la evaluación primero | Aceptada |

## Plantilla

```markdown
# NNNN. Título en forma de decisión

- Estado: propuesta | aceptada | sustituida por NNNN
- Fecha: AAAA-MM-DD
- Decisores: …

## Contexto y problema
## Opciones consideradas
## Decisión
## Consecuencias (positivas / negativas)
```
