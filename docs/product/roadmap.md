# Roadmap

Cada release es usable por sí mismo. Las specs se escriben **justo a tiempo** (un sprint adelante);
lo que está más allá del próximo release es intencionalmente breve.

| Release | Specs | Valor entregado | Estado |
|---|---|---|---|
| **R0 · Walking skeleton** | [001-instrument-catalog](../../specs/001-instrument-catalog/spec.md) | Repo, CI, corte delgado de punta a punta: catálogo de normas con sello de vigencia | ✅ Sprint 0 |
| **R1 · Biblioteca** | [002-corpus-ingestion](../../specs/002-corpus-ingestion/spec.md) · 003-legal-reader | Disposiciones estructuradas con página exacta; árbol de la norma, búsqueda exacta ("art. 5 Ley 27181") y visor *Folio*; despliegue de demo | ✅ 002 (Sprint 1) y 003 (Sprint 2) implementadas; falta la prueba SC-001 con personas y el despliegue de demo |
| **R2 · Consultas citadas** | 004-hybrid-search (+ golden set, evaluación primero) · 005-cited-answers · 006-conversations-feedback | Respuestas citadas y validadas, abstención; piloto interno | 🚧 004 implementada (búsqueda por palabras + significado, evaluación y compuerta); falta medir el significado con la clave real, 005 y 006 |
| **R3 · Producción interna** | 007-identity (login DRTC) · 008-document-admin (carga y revisión, ingesta en segundo plano) · 009-observability-hardening | Uso diario por el personal | ⏳ |
| **R4 · Ciudadanía** | 010-public-mode | Acceso público con lenguaje claro y límites de uso | ⏳ |

## En paralelo

- **SPIKE-01 · Vigencia del corpus** (responsable: líder del proyecto). Obtener los textos oficiales
  vigentes de las tres normas (SPIJ, El Peruano, MTC/MINJUSDH), en particular el **TUO aprobado por
  el DS 006-2026-JUS**, y registrarlos como nuevas versiones verificadas. Resultado: actualización de
  `corpus/manifest.yaml` y de [corpus-inventory.md](../domain/corpus-inventory.md).

## Backlog (resumen de cada spec futura)

- ~~**003-legal-reader**~~ ✅ (Sprint 2): navegar Título → Capítulo → Artículo; abrir un artículo con su
  texto, sello de vigencia y la página del PDF resaltada (pdf.js); búsqueda exacta por referencia;
  "Copiar cita". Pendiente de la spec: selector de edición cuando haya más de una.
- ~~**004-hybrid-search**~~ 🚧 (Sprint 3): golden set de 61 preguntas y arnés de métricas con compuerta de línea base;
  búsqueda por palabras en español + por significado + RRF, con degradación a palabras; `GET /api/v1/search`;
  página «Buscar en el texto». Pendiente: medir el significado con la clave real y elegir el modelo; la expansión
  de contexto pasó a la spec 005 (la define el paquete de evidencias); reranker solo si la evaluación lo justifica.
- **005-cited-answers:** puertos `QueryAnalyzer`, `AnswerGenerator`, `EmbeddingProvider` con OpenAI;
  respuesta estructurada (conclusión, fundamento, análisis, excepciones, fuentes); `CitationValidator`;
  abstención; SSE de progreso; registro de costo y latencia; minimización de datos personales.
- **006-conversations-feedback:** preguntas de seguimiento, historial por sesión anónima, 👍/👎 con motivo.
- **007-identity:** adaptador que valide la sesión del sistema DRTC (`/api/v1/auth/me`) u OIDC; roles.
- **008-document-admin:** carga de PDF, revisión y aprobación en la interfaz, cola de trabajos.
- **009-observability-hardening:** OpenTelemetry, métricas, respaldos, pruebas de prompt injection.
- **010-public-mode:** límites de uso, lenguaje llano, protección contra abuso, idiomas originarios.
