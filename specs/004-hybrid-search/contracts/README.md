# Contratos (spec 004)

El contrato HTTP vigente es `backend/openapi.json` (generado; CI verifica que no se desvíe; los tipos del frontend salen de él con `make openapi`). Este documento fija lo que se va a construir.

## `GET /api/v1/search`

Búsqueda por contenido. **Siempre responde 200** salvo que la consulta sea inválida (422): una falla del método de significado no es un error, es una degradación.

| Parámetro | Tipo | Por defecto | Notas |
|---|---|---|---|
| `q` | string, 1-300 caracteres (sin contar espacios de los extremos) | — | El texto buscado. Vacío o más largo → 422 |
| `limit` | entero 1-30 | 10 | Número de **unidades de lectura** a devolver |
| `instrument` | string, opcional | — | Filtra por norma (`ley-27181`) **antes** de aplicar el límite |
| `mode` | `hybrid` \| `lexical` \| `vector` | `hybrid` | `lexical` y `vector` sirven para evaluar; `vector` sin clave responde con `degraded` y sin resultados de significado |
| `debug` | booleano | `false` | Solo se atiende si el entorno es `local` o `test`; en otros se ignora (sin campo `debug`) |

Respuesta (esquema orientativo; el definitivo es el OpenAPI generado):

```json
{
  "query": "plazo para apelar una resolución",
  "mode": "hybrid",
  "degraded": [],
  "total": 14,
  "facets": [{"instrument_id": "tuo-ley-27444", "short_name": "TUO de la Ley 27444 (LPAG)", "count": 9}],
  "results": [
    {
      "instrument_id": "tuo-ley-27444",
      "instrument_short_name": "TUO de la Ley 27444 (LPAG)",
      "version_id": "tuo-ley-27444@ds-004-2019-jus-ed2021",
      "edition_label": "Segunda Edición Oficial MINJUSDH (julio de 2021)",
      "verification_status": "unverified",
      "may_be_presented_as_current": false,
      "unit_path": "articulo:218",
      "path": "articulo:218/numeral:218.2",
      "kind": "numeral",
      "label": "218.2",
      "title": null,
      "citation": "TUO de la Ley N.° 27444, art. 218, num. 218.2",
      "page_start": 236,
      "page_end": 236,
      "snippet": [{"text": "El término para la interposición de los ", "match": false},
                  {"text": "recursos", "match": true}],
      "matched": [{"path": "articulo:218/numeral:218.2", "citation": "…", "page_start": 236, "snippet": []}],
      "via": ["lexical", "vector"],
      "debug": {"reference_rank": null, "lexical_rank": 1, "vector_rank": 3, "score": 0.0325}
    }
  ]
}
```

Reglas:

- `degraded`: lista de códigos; hoy solo `vector_unavailable` (sin clave, error del proveedor o más de 3 s). La interfaz muestra el aviso a partir de él.
- `via`: `reference` (referencia exacta, siempre al principio), `lexical`, `vector`. Una unidad hallada por referencia y por contenido aparece **una vez**, con ambos.
- `snippet`: segmentos `{text, match}`; nunca HTML. `matched` lista hasta 5 pasajes de la unidad que coincidieron (el principal incluido) con su cita.
- `citation`, `page_*`, `edition_label` y `verification_status` los redacta el servidor con los mismos datos que la spec 003; `may_be_presented_as_current` es verdadero **solo** para `verified_current`.
- `facets`: conteo por norma sobre los candidatos fusionados **antes** del límite (sirve para el filtro de la interfaz).
- El texto de `q` **no** se registra ni se guarda; el registro lleva modo, número de resultados, latencia, degradación y largo.
- Solo se devuelven textos vigentes de ediciones aprobadas.

Errores (RFC 9457): `422 validation_error` para `q` vacío o demasiado largo, o parámetros fuera de rango.

## `GET /api/v1/lookup` (spec 003) — cambio de redacción

Para `status = unrecognized`, el mensaje deja de decir "solo busco por referencia" y pasa a invitar a buscar por contenido ("No reconozco una referencia; puede buscar por su contenido"). El estado y el resto del contrato no cambian.

## CLI `drtc-retrieval` (mensajes en español)

| Comando | Qué hace |
|---|---|
| `index [--version ID]` | Prepara o actualiza el índice de palabras desde las ediciones aprobadas. Idempotente: imprime cuántos pasajes agregó, cambió, borró y dejó igual |
| `embed --dry-run` | Cuenta las ventanas sin vector del modelo configurado y **estima** tokens y costo; no llama a nadie |
| `embed --yes [--limit N]` | Pide los vectores faltantes por lotes; al final imprime el uso real y el costo; sin `--yes` solo estima (nunca gasta sin confirmación) |
| `search "texto" [--mode …] [--limit N] [--debug]` | Corre la misma búsqueda que la API y muestra la lista en la terminal |
| `eval [--dataset golden-v1] [--modes exact,lexical,vector,hybrid] [--k 1,3,5,10] [--out RUTA] [--check-baseline]` | Calcula las métricas y escribe el informe (`.json` y `.md`); con `--check-baseline` sale con error si exacta o palabras empeoran más que la tolerancia. `vector` e `hybrid` piden clave y, antes de enviar nada, muestran la estimación y esperan confirmación |

Código de salida distinto de cero ante: clave ausente cuando el modo la necesita, modelo no disponible, empeoramiento respecto de la línea base.

## Configuración (variables `DRTC_*`)

| Variable | Notas |
|---|---|
| `DRTC_OPENAI_API_KEY` | `SecretStr`; solo en `.env`; ausente ⇒ búsqueda por palabras con aviso |
| `DRTC_OPENAI_EMBEDDING_MODEL` | Identificador del modelo de vectores |
| `DRTC_OPENAI_EMBEDDING_DIMENSIONS` | Opcional: reduce las dimensiones (solo modelos que lo admiten) |
| `DRTC_SEARCH_RRF_K`, `DRTC_SEARCH_ARM_TOP_N`, `DRTC_SEARCH_VECTOR_TIMEOUT_SECONDS` | Parámetros de la búsqueda (valores iniciales en [research](research.md)); se fijan con el golden set |

## Ruta web

`/buscar?q=<texto>&norma=<id>`: la página lee `q` (obligatorio para mostrar resultados) y `norma` (opcional); es la dirección que se comparte.
