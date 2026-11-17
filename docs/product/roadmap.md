# Roadmap

Cada release es usable por sí mismo. Las specs se escriben **justo a tiempo** (un sprint adelante);
lo que está más allá del próximo release es intencionalmente breve.

| Release | Specs | Valor entregado | Estado |
|---|---|---|---|
| **R0 · Walking skeleton** | [001-instrument-catalog](../../specs/001-instrument-catalog/spec.md) | Repo, CI, corte delgado de punta a punta: catálogo de normas con sello de vigencia | ✅ Sprint 0 |
| **R1 · Biblioteca** | [002-corpus-ingestion](../../specs/002-corpus-ingestion/spec.md) · 003-legal-reader | Disposiciones estructuradas con página exacta; árbol de la norma, búsqueda exacta ("art. 5 Ley 27181") y visor *Folio*; despliegue de demo | 📝 002 en borrador |
| **R2 · Consultas citadas** | 004-hybrid-search (+ golden set, evaluación primero) · 005-cited-answers · 006-conversations-feedback | Respuestas citadas y validadas, abstención; piloto interno | ⏳ |
| **R3 · Producción interna** | 007-identity (login DRTC) · 008-document-admin (carga y revisión, ingesta en segundo plano) · 009-observability-hardening | Uso diario por el personal | ⏳ |
| **R4 · Ciudadanía** | 010-public-mode | Acceso público con lenguaje claro y límites de uso | ⏳ |

## En paralelo

- **SPIKE-01 · Vigencia del corpus** (responsable: líder del proyecto). Obtener los textos oficiales
  vigentes de las tres normas (SPIJ, El Peruano, MTC/MINJUSDH), en particular el **TUO aprobado por
  el DS 006-2026-JUS**, y registrarlos como nuevas versiones verificadas. Resultado: actualización de
  `corpus/manifest.yaml` y de [corpus-inventory.md](../domain/corpus-inventory.md).

## Backlog (resumen de cada spec futura)

- **003-legal-reader:** navegar Título → Capítulo → Artículo; abrir un artículo con su texto, sello de
  vigencia y la página del PDF resaltada (pdf.js); búsqueda exacta por referencia; "Copiar cita".
- **004-hybrid-search:** golden set inicial (≥ 50 preguntas) y arnés de métricas (Recall@K, MRR);
  búsqueda textual en español + vectorial + RRF; expansión de contexto; reranker solo si la
  evaluación lo justifica.
- **005-cited-answers:** puertos `QueryAnalyzer`, `AnswerGenerator`, `EmbeddingProvider` con OpenAI;
  respuesta estructurada (conclusión, fundamento, análisis, excepciones, fuentes); `CitationValidator`;
  abstención; SSE de progreso; registro de costo y latencia; minimización de datos personales.
- **006-conversations-feedback:** preguntas de seguimiento, historial por sesión anónima, 👍/👎 con motivo.
- **007-identity:** adaptador que valide la sesión del sistema DRTC (`/api/v1/auth/me`) u OIDC; roles.
- **008-document-admin:** carga de PDF, revisión y aprobación en la interfaz, cola de trabajos.
- **009-observability-hardening:** OpenTelemetry, métricas, respaldos, pruebas de prompt injection.
- **010-public-mode:** límites de uso, lenguaje llano, protección contra abuso, idiomas originarios.
