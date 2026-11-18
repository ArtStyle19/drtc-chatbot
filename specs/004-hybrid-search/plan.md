# Implementation Plan: Búsqueda por contenido (híbrida), con la evaluación primero

**Branch**: `004-hybrid-search` (apilada sobre `003-legal-reader`) | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

**Artefactos**: [research.md](research.md) · [data-model.md](data-model.md) · [contracts/](contracts/README.md) · [quickstart.md](quickstart.md)

## Summary

Se amplía el contexto `retrieval` (que ya resuelve referencias exactas) con una **búsqueda por contenido de tres brazos**:
referencia exacta (prioridad), palabras (PostgreSQL, español sin tildes) y significado (embeddings de OpenAI en pgvector),
fusionados con RRF y agrupados por unidad de lectura. **La evaluación se construye antes**: golden set de ≥ 50 preguntas con
ruta estructural, métricas (Recall@K, MRR), línea base de la búsqueda exacta y una compuerta de CI determinista
(exacta + palabras) contra `evaluation/baseline.json`. El índice es un dato derivado (`retrieval_passages`,
`retrieval_embeddings`) que se reconstruye desde `legal_corpus.api`. La interfaz es la página `/buscar?q=`, a la que lleva
el buscador del encabezado cuando el texto no es una referencia. No se generan respuestas (spec 005).

## Decisiones de diseño

| Tema | Decisión | Por qué |
|---|---|---|
| Orden del trabajo | Evaluación → exacta (línea base) → palabras → significado → combinada → API → interfaz | Constitución IV: ninguna variante se integra sin medirla; la línea base existe antes de la búsqueda |
| Brazo exacto | Reutiliza `LookupReference` (spec 003); su `ignored_text` es el texto restante que busca por contenido | Constitución I.6: una disposición identificada va antes que la similitud; sin código duplicado |
| Palabras | Configuración de búsqueda `es_unaccent` (copia de `spanish` + diccionario `unaccent`), `tsvector` **generado** con pesos (título/etiqueta A, texto B), consulta = OR de raíces, `ts_rank_cd` | Verificado en la base real: sin tildes, plurales y formas verbales; `ts_headline` conserva el texto original ([research R1-R2](research.md)) |
| Significado | Puerto `EmbeddingProvider`; adaptador OpenAI (SDK `openai` 3.x) y adaptador falso determinista; modelo y dimensiones desde configuración; se comparan `text-embedding-3-small` y `-large` | ADR-0006; la clave es del líder del proyecto, solo en `.env` (`SecretStr`) |
| Vectores | Tabla aparte `retrieval_embeddings` (pasaje, modelo, ventana), columna `vector` sin dimensión fija, **sin índice ANN** | Varios modelos conviven para evaluarlos; ~2.600 filas se recorren en milisegundos; HNSW exigiría reducir dimensiones sin beneficio (VIII) |
| Fusión | RRF (k = 60) sobre los 50 primeros de cada brazo, a nivel de **pasaje**; luego agrupa por unidad de lectura (puntaje = el del mejor pasaje) | Pasajes que ambos brazos prefieren suben; la unidad es lo que el lector abre. Variantes (k, suma en vez de máximo) se miden |
| Fragmentación | Un pasaje = el texto **vigente** de una disposición (artículo, numeral, literal, disposición, anexo); el texto a indexar lleva la miga de pan y el comienzo del texto del padre; los textos > 3.500 caracteres se parten en ventanas para el vector | Un literal sin su encabezado ("entiéndase por:") no significa nada; el límite del modelo es de ~8 mil tokens ([R6](research.md)) |
| Costo y confirmación | `embed --dry-run` estima tokens (caracteres ÷ 3, cota superior) y costo; `--yes` ejecuta; el uso real (`usage` de la API) se anota | Sin dependencia `tiktoken` (descarga archivos al ejecutar); la cifra real queda registrada |
| Degradación | Si no hay clave, hay error o pasa el tiempo límite (3 s), responde con palabras y `degraded: ["vector_unavailable"]` | FR-013; la herramienta no puede depender de un tercero |
| Privacidad | Solo se registra modo, número de resultados, latencia, degradación y **largo** de la consulta; nunca su texto | Constitución VI |
| Compuerta de CI | Brazos deterministas (exacta + palabras) contra `evaluation/baseline.json` con tolerancia 0,02; el significado y la combinada se miden a mano (necesitan clave) y su informe se versiona en `evaluation/reports/` | CI sin red ni claves; las cifras del significado quedan documentadas en el ADR |
| Diagnóstico | `debug=true` solo se atiende si el entorno es `local` o `test`; en otros se ignora | FR-017 |
| Resaltado | El servidor devuelve el fragmento como segmentos `[{text, match}]` (a partir de `ts_headline` con marcas internas); el cliente nunca usa `innerHTML` | Evita XSS y HTML generado por el servidor |
| Ruta web | `/buscar?q=<texto>&norma=<id>` | Compartible; el filtro por norma se pide al servidor para que respete el límite |

## Technical Context

**Backend**: FastAPI, SQLAlchemy 2.1 async + psycopg 3, Alembic (migración `0004`), `pgvector` (ya es dependencia), `openai` 3.x
(nueva; versión estable verificada en PyPI: 3.55.1, Python ≥ 3.10).
**Frontend**: Angular 22, NgRx SignalStore; reutiliza `ValiditySeal`, `entryLabel`, `toUserMessage` y el patrón de `ReaderStore` (contador de peticiones).
**Testing**: pytest (unidad con proveedor falso; PostgreSQL real con `full_corpus` para índice, búsqueda y evaluación), Vitest, Playwright + axe
(API simulada **y** real). La suite nunca llama a OpenAI.
**Constraints**: sin infraestructura nueva (Redis, colas, reranker, OCR, índice ANN); nada no verificado como vigente; sin texto de consultas en registros;
clave solo en `.env`.
**Scale**: 2.572 pasajes vigentes (~692 mil caracteres, ~175 mil tokens); un pasaje llega a 35 mil caracteres (anexo).

## Constitution Check

| Principio | Cumplimiento |
|---|---|
| I.1 vigencia | Cada resultado lleva `verification_status` y `may_be_presented_as_current`; el sello se muestra; prueba SC-009 |
| I.2-3 citas | La cita breve viene del servidor (la misma de la spec 003); el enlace abre el lector en la ruta exacta y edición |
| I.5 aprobación | Solo ediciones **aprobadas** se indexan (el índice se alimenta de `legal_corpus.api`, que ya filtra) |
| I.6 exacta primero | El brazo exacto va primero y marcado; la fusión solo ordena lo demás |
| I.7 abstención | No aplica (no hay respuestas); la pantalla dice que son coincidencias, no una respuesta |
| I.8 material explicativo | El Manual del TUO no está en el corpus ingerido; no se indexa historial ni notas |
| I.9 documentos como datos | Los pasajes se tratan solo como texto; las marcas internas del resaltado son caracteres que no aparecen en los textos (se verifican al construir el índice) |
| I.10 calidad medida | Golden set + métricas + línea base + compuerta |
| III Clean Architecture | `retrieval` solo importa `legal_corpus.api`; dominio puro (sin openai, sqlalchemy, httpx); 6 contratos de import-linter |
| IV Test-first | La evaluación y la línea base preceden a la búsqueda; pruebas con `@pytest.mark.spec("004-FR-xxx")` |
| V Cortes verticales | US1 (medir) → US2 (palabras + exacta + pantalla) → US3 (significado) → US4 (degradar) → US5 (diagnóstico) |
| VI Privacidad | Sin texto de consultas en registros; aviso en la interfaz; clave en `.env`; solo corpus público y la consulta salen del servidor |
| VII UX accesible | axe sin violaciones serias, teclado, móvil, estados de carga/vacío/error/degradado |
| VIII Simplicidad | Sin ANN, sin reranker, sin `tiktoken`, sin caché; una tabla de pasajes y una de vectores |

**Re-evaluación tras el diseño**: sin violaciones. La única adición de dependencia es el SDK `openai`, ya prevista en el ADR-0006.

## Project Structure

```text
backend/src/drtc_chatbot/contexts/
├── legal_corpus/
│   ├── application/queries/list_indexable_passages.py   (nuevo) pasajes vigentes completos de ediciones aprobadas
│   ├── infrastructure/sql_reading.py                    (+ get_indexable_passages)
│   └── api.py                                           (+ ListIndexablePassages, IndexablePassage)
└── retrieval/
    ├── domain/
    │   ├── chunking.py      texto a indexar, ventanas, miga de pan, huella (content_hash)
    │   ├── fusion.py        RRF
    │   ├── metrics.py       Recall@K, MRR, regla de acierto (disposición / unidad)
    │   ├── expansion.py     contexto de un resultado (artículo + hermanos dentro de un presupuesto)
    │   └── query.py         separación referencia / texto restante; límites de la consulta
    ├── application/
    │   ├── ports.py         + PassageSource, PassageIndex, EmbeddingProvider, Clock-like timers
    │   ├── build_index.py   idempotente; recalcula solo lo que cambió
    │   ├── search_passages.py   exacta → palabras ‖ significado → RRF → agrupar → degradar
    │   └── run_evaluation.py    corre un método sobre el golden set y calcula métricas
    ├── infrastructure/
    │   ├── legal_corpus_passages.py   PassageSource sobre legal_corpus.api
    │   ├── sql_passage_index.py       tablas, FTS, vectores, resaltado
    │   ├── openai_embeddings.py       lotes, tiempos, reintentos, uso real
    │   └── fake_embeddings.py         determinista (pruebas y CI)
    └── presentation/
        ├── http/{search_router,search_schemas}.py   GET /api/v1/search
        └── cli/app.py                                drtc-retrieval index | embed | search | eval
backend/src/drtc_chatbot/entrypoints/cli/retrieval.py   (script de consola)
backend/migrations/versions/…_0004_retrieval_index.py

evaluation/
├── datasets/{golden-questions.schema.json, golden-v1.jsonl}   (+ path por cita; ~50 preguntas)
├── baseline.json                                              métricas aceptadas (exacta + palabras)
├── CHANGELOG.md                                               decisiones sobre la línea base
└── reports/                                                   informes de corridas manuales (significado, combinada)

frontend/src/app/features/search/
├── data-access/{search-api,search.store}.ts
├── feature/search-page.*
└── ui/{result-card,snippet}/
frontend/src/app/features/lookup/feature/reference-search.*   (+ opción «Buscar … en el texto»)
```

**Structure Decision**: se amplía `retrieval` (ya previsto en el mapa de contextos) y se añade una feature `search` al frontend; la evaluación vive en
`evaluation/` con su código en `retrieval` (dominio de métricas + caso de uso), invocada por la CLI.

## Complexity Tracking

| Adición | Por qué es necesaria | Alternativa más simple descartada |
|---|---|---|
| Dos tablas derivadas (`retrieval_passages`, `retrieval_embeddings`) | El contexto `retrieval` no puede leer las tablas de `legal_corpus` (contrato de contextos) y se necesitan varios modelos de vectores para compararlos | Columna `tsvector` en `provision_versions`: rompería la propiedad del contexto |
| SDK `openai` | Ya decidido en ADR-0006; maneja reintentos y tiempos | Cliente HTTP propio: más código que mantener |
| CLI `drtc-retrieval` | Preparar el índice, calcular vectores con confirmación de costo y evaluar no pertenecen a la API HTTP | Endpoints de administración: sin login (ADR-0007) sería un riesgo |
