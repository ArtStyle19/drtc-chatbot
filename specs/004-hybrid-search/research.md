# Investigación — spec 004

Formato: **Decisión · Por qué · Alternativas**. Lo marcado «se mide» queda definido por el golden set y se registra en el ADR-0014.

## R1. Búsqueda por palabras: configuración `es_unaccent`

- **Decisión**: `CREATE TEXT SEARCH CONFIGURATION es_unaccent (COPY = spanish)` y mapear `hword, hword_part, word` a `unaccent, spanish_stem`.
- **Por qué**: probado en la base real (PostgreSQL 18, `unaccent` 1.1): "Los vehículos motorizados menores sancionan; ¿cuál es el PLAZO de apelación?" →
  `'apelacion' 'menor' 'motoriz' 'plaz' 'sancion' 'vehicul'`. Al ser una configuración (no una llamada a `unaccent()`), el `tsvector` puede ser una columna
  **generada** (inmutable) y `ts_headline` ignora las tildes pero **devuelve el texto original** ("<<apelación>>").
- **Alternativas**: función envoltorio `immutable_unaccent()` (más SQL propio); normalizar el texto al guardarlo (el fragmento resaltado perdería las tildes).

## R2. Forma de la consulta y puntaje

- **Decisión**: la pregunta se convierte con `plainto_tsquery('es_unaccent', q)` y se cambia `&` por `|` (OR). Probado: "¿Se puede cobrar por el servicio de mototaxi?" →
  `'pued' | 'cobr' | 'servici' | 'mototaxi'` (las palabras vacías desaparecen). Puntaje: `ts_rank_cd` sobre un `tsvector` con pesos (título y etiqueta = A, texto = B).
- **Por qué**: el modo AND por defecto no devuelve nada para preguntas largas; el OR ordena por cuántos términos y con qué cercanía coinciden.
- **Se mide**: pesos A/B, normalización de longitud de `ts_rank_cd`, y un respaldo AND-primero. **Alternativa**: `pg_trgm` (tolerancia a errores de tipeo) solo si el golden set muestra fallos por ortografía.

## R3. Modelo de significado

- **Decisión**: comparar `text-embedding-3-small` (1536 dimensiones) y `text-embedding-3-large` (3072; también reducido con el parámetro `dimensions` a 1024/1536) y conservar el que
  gane en Recall@10 y rango recíproco; en empate, el más barato.
- **Por qué**: precios publicados: [small 0,02 USD](https://developers.openai.com/api/docs/models/text-embedding-3-small) y [large 0,13 USD](https://developers.openai.com/api/docs/models/text-embedding-3-large) por millón de tokens. Con ~175 mil tokens el
  costo es ≈ 0,004 y ≈ 0,023 USD: la comparación completa cuesta centavos (SC-010).
- **Verificar al usar la clave**: los identificadores vigentes (`models.retrieve`) y la versión del SDK (3.55.1 en PyPI al 2026-11-18, Python ≥ 3.10).
- **Alternativas**: modelo local (dependencias de ~1-2 GB; contradice ADR-0006); `ada-002` (superado).

## R4. Sin índice aproximado (ANN)

- **Decisión**: no crear HNSW/IVFFlat. Búsqueda exacta por `ORDER BY embedding <=> $1 LIMIT N` filtrando por modelo.
- **Por qué**: 2.572 vectores × 1536 floats se recorren en milisegundos; HNSW de `vector` admite hasta 2000 dimensiones (obligaría a reducir `large`) y complica la reconstrucción.
  Se reevalúa con una spec si el corpus crece por órdenes de magnitud. **Columna `vector` sin dimensión fija** (permite varios modelos); un `CHECK` de coherencia con la columna `dims`.

## R5. Estimar tokens sin `tiktoken`

- **Decisión**: `tokens_estimados = ceil(caracteres / 3)` (cota superior para español con el tokenizador de estos modelos, ~3,5-4 caracteres por token); el costo estimado usa esa cifra; el **uso real** (`usage.total_tokens`) de cada respuesta se suma y se imprime al final.
- **Por qué**: `tiktoken` descarga sus archivos de vocabulario al ejecutarse (red en una herramienta que debe funcionar sin ella) y solo daría una cifra algo más ajustada de una estimación que luego se reemplaza por la real.

## R6. Qué es un pasaje y cómo se parte

- **Decisión**: un pasaje por cada revisión **vigente** con texto de tipo artículo, numeral, literal, disposición y anexo (contenedores y notas no). Texto a indexar para el vector:
  `"<norma> › <título/capítulo> › <artículo> › <etiqueta>\n<comienzo del texto del padre (≤ 300 caracteres) si es numeral/literal>\n<texto propio>"`. Para palabras se indexa el título, la etiqueta
  y el texto propio (la miga de pan va en un campo aparte, con peso C).
- **Textos largos**: si el texto indexado supera 3.500 caracteres (≈ 1.200 tokens) se parte por párrafos/oraciones en ventanas con 10 % de solapamiento; cada ventana tiene su vector y el pasaje toma la mejor. El límite del modelo es de 8.191 tokens por entrada; el anexo del RENAT llega a 35 mil caracteres.
- **Se mide**: con y sin el comienzo del padre; tamaño de ventana.
- **Alternativas**: un pasaje por artículo (los numerales dejarían de poder citarse con precisión); partir por tamaño fijo (rompe la estructura jurídica, decisión 2 del [RAG](../../docs/architecture/rag-pipeline.md)).

## R7. Fusión

- **Decisión**: RRF con `k = 60` sobre los 50 primeros de cada brazo (a nivel de pasaje) → agrupar por unidad de lectura con el puntaje del mejor pasaje → devolver hasta `limit` unidades.
  El brazo exacto no entra en la fusión: va primero (I.6) y se quita de la lista del resto para que no se repita.
- **Se mide**: `k` ∈ {20, 60}, pesos por brazo, máximo vs suma al agrupar, N por brazo.
- **Alternativa**: combinar puntajes crudos (escalas incomparables entre `ts_rank_cd` y distancia coseno); aprendizaje de ordenamiento (sin datos suficientes).

## R8. Criterio de acierto en la evaluación

- **Decisión**: dos niveles. *Disposición*: la ruta recuperada es la esperada o está **debajo** de ella (esperado = artículo, recuperado = su numeral). *Unidad*: la unidad de lectura
  recuperada es la de la esperada (esperado = literal e, recuperado = su artículo cuenta). Se informan ambos; los umbrales de SC-003 usan el de unidad.
- **Por qué**: una persona que cita "art. 2, lit. e)" queda bien servida si el lector abre el artículo 2; pero la métrica estricta evita ocultar imprecisión.
- **Métricas**: Recall@K (K = 1, 3, 5, 10), MRR, y *soporte en contexto@K*: el texto de respaldo esperado aparece (normalizado) en el contexto expandido de los K primeros — es lo que le importará a la spec 005.
  Preguntas sin respuesta: se informa la distribución del mejor puntaje (el umbral de abstención se calibra en la 005).

## R9. Compuerta determinista

- **Decisión**: una prueba (marcada `docker`) ingesta las tres normas, prepara el índice sin vectores, corre exacta y palabras sobre el golden set y compara con `evaluation/baseline.json`
  (tolerancia 0,02 por métrica). El significado y la combinada necesitan la clave: se corren a mano y su informe se guarda en `evaluation/reports/`.
- **Por qué**: la suite no puede llamar a OpenAI (cuesta, es lenta y no es determinista). Cambiar la línea base exige una entrada en `evaluation/CHANGELOG.md`.

## R10. Resaltado seguro

- **Decisión**: `ts_headline(... StartSel=<marca>, StopSel=</marca>)` con caracteres de control (U+0001/U+0002) como marcas; el adaptador los convierte en segmentos `[{text, match}]`. Al construir el índice se verifica que el texto no contenga esos caracteres
  (se eliminan si aparecen). El cliente pinta los segmentos con `<mark>` sin `innerHTML`.

## R11. Privacidad y registros

- **Decisión**: se registra `search` con `mode`, `results`, `latency_ms`, `degraded`, `query_chars`; nunca el texto. La consulta se limita a 1-300 caracteres antes de salir hacia cualquier servicio.
  La interfaz avisa que el texto se envía a un servicio externo y que no incluya datos personales.

## R12. Cliente de OpenAI

- **Decisión**: `AsyncOpenAI` del SDK `openai` 3.x: `embeddings.create(model, input=[...], dimensions?)`, lotes de hasta 100 entradas, tiempo límite de 20 s para el índice y de **3 s para consultas**, 2 reintentos con espera creciente (los del SDK), errores traducidos a un error de dominio
  `EmbeddingUnavailableError` (que la búsqueda convierte en degradación). Configuración: `DRTC_OPENAI_API_KEY` (`SecretStr`), `DRTC_OPENAI_EMBEDDING_MODEL`, `DRTC_OPENAI_EMBEDDING_DIMENSIONS`.

## R13. Sin resolver a propósito (se decide con datos)

Reordenador (reranker), sinónimos propios, `pg_trgm`, caché de vectores de consulta: no se construyen; el informe de evaluación dirá si alguno se justifica y entonces será otra spec.
