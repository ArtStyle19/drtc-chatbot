# Infraestructura

Hoy: el entorno local se define en [`../compose.yaml`](../compose.yaml) (PostgreSQL + pgvector,
migraciones, backend y frontend) y las imágenes en `backend/Dockerfile` y `frontend/Dockerfile`.

## Producción (release R1)

Se seguirá el patrón ya probado en el sistema DRTC de Habilitación Vehicular:

- Imágenes publicadas en GHCR por GitHub Actions (`drtc-chatbot-backend`, `drtc-chatbot-frontend`).
- `infra/compose.prod.yaml` con PostgreSQL (respaldos automáticos), backend, frontend y MinIO para
  los documentos fuente, detrás del proxy inverso con TLS de la DRTC.
- Secretos fuera del repositorio (variables de entorno del servidor).
- Health checks: `/health/live` y `/health/ready` del backend.

Archivos previstos en esta carpeta: `compose.prod.yaml`, `nginx/` (si el proxy no es compartido),
`backup/` (scripts de respaldo y restauración probados) y un runbook en `docs/operations/`.
