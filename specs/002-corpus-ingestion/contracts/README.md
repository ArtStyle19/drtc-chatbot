# Contrato de la API (spec 002)

El contrato vigente es `backend/openapi.json` (generado; CI verifica que no se desvíe). Rutas nuevas:

| Ruta | Descripción |
|---|---|
| `GET /api/v1/instruments/{instrument_id}/provisions` | Disposiciones **vigentes** de la edición aprobada más reciente (o `version_id`). Filtros: `kind`, `parent`, `limit` (1-500), `offset`. 404 si no hay edición aprobada |
| `GET /api/v1/provisions/{provision_id}` | Una disposición con todas sus revisiones (de la más antigua a la vigente), sus eventos legales y notas editoriales |
| `GET /api/v1/instruments` *(ampliada)* | La edición incluye `approval_status`, `approval_mode`, `provision_count` |

Reglas del contrato: nunca se devuelven ediciones pendientes de aprobación; toda respuesta con texto
incluye `verification_status` y `may_be_presented_as_current` (falso salvo `verified_current`) y el
`approval_mode`; los errores son RFC 9457.
