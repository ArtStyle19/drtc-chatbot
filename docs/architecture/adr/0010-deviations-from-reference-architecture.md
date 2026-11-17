# 0010. Diferencias con la arquitectura de referencia

- Estado: aceptada
- Fecha: 2026-11-17

## Contexto

La [arquitectura de referencia](../reference/arquitectura_rag_consultoria_legal_peru.md) sigue siendo
la base (monolito modular, PostgreSQL + pgvector + FTS, búsqueda híbrida, validación de citas,
principios innegociables del Anexo B). Algunas decisiones cambiaron.

## Decisiones

| Tema | Referencia | Este proyecto | Motivo |
|---|---|---|---|
| Frontend | Next.js + TypeScript | Angular 22 | Pedido del equipo; mismo stack que el sistema DRTC (ADR-0008) |
| Proveedor de IA | Por definir con benchmark | OpenAI primero, detrás de puertos | Decisión del equipo (ADR-0006) |
| Autenticación | OIDC/Keycloak, RBAC, MFA | Sin login en el MVP; puerto de identidad | Etapa de pruebas (ADR-0007) |
| Tareas asíncronas | Celery + Redis | Ingesta por CLI hasta la spec 008 | YAGNI: tres documentos |
| Almacenamiento | S3 compatible | Archivos locales detrás de un puerto; MinIO en producción | YAGNI en desarrollo; MinIO ya existe en la DRTC |
| Extracción PDF | PyMuPDF + Docling; OCR | PyMuPDF primero; Docling/OCR solo si hace falta | Los tres PDF tienen capa de texto |
| Reranker | Cross-Encoder | Solo si la evaluación lo justifica | Medir antes de agregar |
| Observabilidad | OTel + Prometheus + Grafana | Logs estructurados + `request_id` ahora; OTel en la spec 009 | Incremental |
| Base de datos | PostgreSQL 17+ | PostgreSQL 18 | Versión estable actual |
| TUO Ley 27444 | Verificar DS 006-2026-JUS | Confirmado por fuentes secundarias; pendiente verificación oficial | SPIKE-01 |

## Consecuencias

Se mantiene el destino de la referencia, llegando por incrementos medibles. Cada componente
postergado tiene una spec que decidirá su incorporación con evidencia.
