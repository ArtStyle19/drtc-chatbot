# Especificaciones

Cada funcionalidad tiene una carpeta `NNN-slug/` creada con Spec Kit (`/speckit-specify`). El proceso
está en [docs/process/way-of-working.md](../docs/process/way-of-working.md) y las reglas que toda spec
debe respetar en la [constitución](../.specify/memory/constitution.md).

| Spec | Release | Estado | Artefactos |
|---|---|---|---|
| [001-instrument-catalog](001-instrument-catalog/spec.md) | R0 | ✅ Implementada (Sprint 0) | spec · plan · tasks |
| [002-corpus-ingestion](002-corpus-ingestion/spec.md) | R1 | ✅ Implementada (Sprint 1) · revisión SC-001 pendiente | spec · plan · data-model · contracts · quickstart · tasks |
| [003-legal-reader](003-legal-reader/spec.md) | R1 | ✅ Implementada (Sprint 2) · prueba SC-001 con personas pendiente | spec · plan · contracts · tasks |
| [004-hybrid-search](004-hybrid-search/spec.md) | R2 | 🚧 Implementada salvo la medición con la clave real de OpenAI (T036-T038) · prueba SC-011 con personas pendiente | spec · plan · research · data-model · contracts · quickstart · tasks |
| 005-cited-answers | R2 | ⏳ Backlog | — |
| 006-conversations-feedback | R2 | ⏳ Backlog | — |
| 007-identity | R3 | ⏳ Backlog | — |
| 008-document-admin | R3 | ⏳ Backlog | — |
| 009-observability-hardening | R3 | ⏳ Backlog | — |
| 010-public-mode | R4 | ⏳ Backlog | — |

Resumen de cada spec futura: [roadmap](../docs/product/roadmap.md#backlog-resumen-de-cada-spec-futura).

## Convenciones

- Contenido en español; nombres de carpeta en inglés (`NNN-slug`), que coinciden con la rama.
- Requisitos `FR-NNN` y criterios `SC-NNN` numerados dentro de cada spec; los tests los citan como
  `@pytest.mark.spec("002-FR-003")`.
- Estados: 📝 borrador · 🔎 clarificada (Ready) · 🚧 en curso · ✅ implementada.
