# Modelo de datos — spec 004

El índice es un modelo **derivado y reconstruible** del corpus (ADR-0005): se puede borrar y volver a preparar desde `legal_corpus.api`.
Pertenece al contexto `retrieval`; `legal_corpus` no sabe que existe.

## Tablas (migración `0004`)

### Configuración de búsqueda

Se usa la configuración estándar `spanish` (no hay configuración propia): las tildes de la **consulta** se resuelven ampliándola con la tabla `retrieval_accents` (ver [research R1](research.md)).

### `retrieval_passages` — un pasaje por revisión vigente indexada

| Columna | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `instrument_id` | text | Para filtrar por norma |
| `instrument_version_id` | text | Edición aprobada de la que viene |
| `provision_path` | text | Ruta estructural (`articulo:2/literal:e`) |
| `unit_path` | text | Unidad de lectura (la calcula `legal_corpus`: `reading_unit_path`) |
| `kind` | text | `article`, `numeral`, `literal`, `disposition`, `annex` |
| `label` | text | `2`, `e`, … |
| `title` | text null | |
| `breadcrumb` | text | "Ley 27181 › Título I › Art. 2 › lit. e)" |
| `lead` | text null | Comienzo (≤ 300 caracteres) del texto del padre, si es numeral o literal |
| `body` | text | Texto vigente completo |
| `page_start`, `page_end` | int | |
| `content_hash` | text | SHA-256 de lo que se indexa (`breadcrumb + lead + title + body`); decide si hay que recalcular |
| `search_vector` | tsvector **generado, almacenado** | `setweight(to_tsvector('spanish', title), 'A') ‖ setweight(…(body), 'B') ‖ setweight(…(breadcrumb ‖ ' ' ‖ lead), 'C')` |

Restricciones e índices: `UNIQUE (instrument_version_id, provision_path)`; índice **GIN** sobre `search_vector`; índice por `(instrument_id)`.
Al preparar el índice se **eliminan** los pasajes de la edición que ya no existen (texto sustituido o ingesta nueva); los vectores caen en cascada.

### `retrieval_accents` — vocabulario de tildes del corpus

| Columna | Tipo | Notas |
|---|---|---|
| `plain` | text PK | La palabra tecleada sin tilde (`apelacion`); la `ñ` se conserva |
| `accented` | text PK | La palabra como está escrita en el corpus (`apelación`) |

Se reconstruye completa en cada sincronización a partir de los pasajes.

### `retrieval_embeddings` — varios modelos conviven

| Columna | Tipo | Notas |
|---|---|---|
| `passage_id` | uuid FK → `retrieval_passages` (ON DELETE CASCADE) | |
| `model` | text | Identificador del modelo (de la configuración) |
| `dims` | int | Dimensiones del vector |
| `window` | int | 0 si el pasaje cabe entero; 1..n si se partió |
| `content_hash` | text | Hash de la ventana embebida: si coincide, no se vuelve a pedir |
| `embedding` | `vector` (sin dimensión fija) | `CHECK (vector_dims(embedding) = dims)` |

PK `(passage_id, model, window)`. **Sin índice ANN** ([R4](research.md)): se consulta con `WHERE model = $m ORDER BY embedding <=> $q LIMIT 50`; por pasaje se toma la mejor ventana.

## Entidades de dominio (Python puro)

- `PassageText` — lo que se indexa de una disposición: ubicación, miga de pan, `lead`, título, cuerpo, páginas, huella. Función `chunk(passage) → [ventanas]`.
- `Candidate` — un pasaje recuperado por un brazo: `path`, `unit_path`, `arm` (`lexical` | `vector`), `rank`, `score`.
- `Fused` — un pasaje con su puntaje RRF y los brazos que lo hallaron.
- `SearchHit` (aplicación) — una unidad: mejor pasaje, pasajes coincidentes (≤ 5), cita breve, edición, estado de verificación, `via` (`reference` / `lexical` / `vector`) y, si se pide, `debug` (rango por brazo).
- `EvaluationQuestion`, `Expectation`, `MethodRun`, `MetricsReport` — evaluación (ver abajo).

## Evaluación

### Pregunta (JSONL, `evaluation/datasets/golden-v1.jsonl`)

El esquema actual se amplía (retrocompatible) con, por cita esperada:

```json
{
  "version_id": "tuo-ley-27444@ds-004-2019-jus-ed2021",
  "provision": "TUO Ley 27444, art. 218, num. 218.2",
  "path": "articulo:218/numeral:218.2",
  "pdf_pages": [236],
  "supporting_text": "El término para la interposición de los recursos es de quince (15) días perentorios…",
  "page_role": "normative"
}
```

Reglas verificadas por la suite: la `version_id` y las páginas existen en el manifiesto; el `supporting_text` aparece en la página del PDF (ya existe); **nuevo**: la `path` existe en el corpus ingerido, sus páginas incluyen las citadas y su texto
contiene el `supporting_text` (normalizado). Las preguntas sin respuesta (`answerable: false`) no tienen citas. `golden-v0.jsonl` (10 preguntas) se conserva dentro de `golden-v1.jsonl` ya con `path`.

### Informe de una corrida (`evaluation/reports/AAAA-MM-DD-<etiqueta>.json` y `.md`)

```json
{
  "dataset": "golden-v1", "questions": 52, "answerable": 44, "approved": 0,
  "methods": {
    "lexical": {"unit": {"recall@1": 0.0, "recall@3": 0.0, "recall@5": 0.0, "recall@10": 0.0, "mrr": 0.0},
                "provision": {"recall@10": 0.0, "mrr": 0.0}, "support_in_context@5": 0.0,
                "latency_ms": {"p50": 0, "p95": 0}},
    "exact": {...}, "vector": {...}, "hybrid": {...}
  },
  "by_intent": {...}, "by_review_status": {...},
  "worst": [{"id": "q-017", "rank": null, "expected": ["articulo:…"], "top": ["articulo:…"]}],
  "provider": {"model": "text-embedding-3-small", "tokens": 0, "estimated_cost_usd": 0.0}
}
```

### Línea base (`evaluation/baseline.json`)

Métricas de `exact` y `lexical` aceptadas (al nivel de unidad y de disposición) más la fecha, el commit y la versión del golden set. `evaluation/CHANGELOG.md` registra, por fecha, por qué cambió la línea base y quién lo aprobó.

## Transiciones

`BuildIndex`: `lee pasajes aprobados` → (por cada uno) `huella igual` ⇒ sin cambios · `huella distinta o nuevo` ⇒ upsert y borra sus vectores del modelo vigente · `ya no existe` ⇒ borra. `embed`: solo ventanas sin vector del modelo configurado (o con huella distinta).
