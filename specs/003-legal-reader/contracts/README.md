# Contrato de la API (spec 003)

El contrato vigente es `backend/openapi.json` (generado; CI verifica que no se desvíe) y los tipos del
frontend se generan de él (`make openapi`). Rutas nuevas:

| Ruta | Descripción |
|---|---|
| `GET /api/v1/instruments/{instrument_id}/outline` | Índice plano y ordenado de la edición aprobada (o `version_id`): secciones, títulos, capítulos, artículos, disposiciones y anexos, con `path`, `parent_path`, `unit_path` y página; más el contexto de la edición (sello, aprobación, advertencias, `source_url`). Hasta 65 kB sin comprimir (TUO); gzip en nginx |
| `GET /api/v1/instruments/{instrument_id}/reading-unit?path=&version_id=` | La unidad de lectura que contiene `path` (artículo, disposición, anexo o contenedor): nodos vigentes con texto, páginas, cajas (`page,x0,y0,x1,y1` en puntos del PDF, origen abajo-izquierda), evento legal, **cita breve y formal**, historial de textos sustituidos (cada uno con su cita "no vigente"), notas y advertencias. Un contenedor incluye `children` |
| `GET /api/v1/versions/{version_id}/source` | PDF original de una edición **aprobada**. `Range`/`206`, `ETag` = SHA-256 (`304`), `Cache-Control: private`; verifica el SHA-256 antes de servir; `416` si el rango no es válido; `404` si la edición no existe o no está aprobada |
| `GET /api/v1/lookup?q=` | Resuelve una referencia ("art. 2 lit. e Ley 27181"). `status`: `resolved` · `ambiguous` (varias coincidencias: elige la persona) · `not_found` · `unrecognized`. `q` de 1 a 200 caracteres (`422` si no) |
| `GET /api/v1/instruments` *(ampliada)* | Cada norma incluye `aliases` (nombres y siglas con que el personal la nombra) |

Reglas del contrato: solo ediciones aprobadas; toda respuesta con texto lleva `verification_status` y
`may_be_presented_as_current` (falso salvo `verified_current`); **las citas las redacta el servidor**; los
errores son RFC 9457 (`application/problem+json`) y los fallos de integridad del PDF no revelan rutas ni
detalles internos (`500` con mensaje genérico y detalle solo en el registro).
