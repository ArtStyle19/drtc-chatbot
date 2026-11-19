# Investigación — spec 004

Formato: **Decisión · Por qué · Alternativas**. Lo marcado «se mide» queda definido por el golden set y se registra en el ADR-0014.

## R1. Búsqueda por palabras: configuración `spanish` y tildes en la consulta

- **Decisión (corregida con datos)**: documentos con la configuración estándar `spanish` (columna `tsvector` **generada**) y, en la consulta, cada palabra
  tecleada sin tilde se amplía con su forma acentuada: la que tiene el corpus (tabla `retrieval_accents`, reconstruida en cada sincronización) y, de respaldo, la regla «consonante + ion → ión».
- **Por qué**: lo planeado inicialmente (`es_unaccent` = `unaccent` + `spanish_stem`) **rompía el singular/plural de las palabras en «-ción»**: el lematizador solo reconoce «-ción» con tilde, pero «-ciones» sin ella,
  así que `apelación` → `apelacion` y `apelaciones` → `apel` nunca coinciden. Medido sobre el vocabulario real: **366 de 6.403 palabras distintas** (202 en «-ción», 36 en «-ía», verbos como «sustituirá») se lematizan
  distinto si se teclean sin tilde con la configuración estándar. Con la ampliación de la consulta, `resolucion`, `resoluciones` y `resolución` coinciden entre sí.
- **Alternativas**: `es_unaccent` (rompe -ción); doble `tsvector` (estándar + sin tilde) con consulta doble (no cubre singular tecleado sin tilde frente a un plural); reglas de acentuación solo por expresión regular (no cubre verbos ni «-ía»).
- **Fuera de alcance**: la `ñ` no se pliega a `n` (`año` ≠ `ano`); el PDF de la Ley dice «danos y perjuicios» (error del propio documento) y por eso «daños» no lo encuentra.

## R2. Forma de la consulta y puntaje

- **Decisión (medida con el golden set)**: la pregunta, ampliada con las tildes (R1), se convierte con `plainto_tsquery('spanish', q)` y se cambia `&` por `|` (OR): "¿Se puede cobrar por el servicio de mototaxi?" →
  `'pued' | 'cobr' | 'servici' | 'mototaxi'` (las palabras vacías desaparecen). Puntaje: `ts_rank_cd` sobre un `tsvector` con pesos **A = título 0,4 · B = texto 0,4 · C = miga de pan y encabezado del padre 0,2 · D = 0,1** y
  **normalización 2 (dividir por la longitud del pasaje)**.
- **Por qué**: el modo AND por defecto no devuelve nada para preguntas largas; el OR ordena por cuántos términos coinciden y con qué cercanía. Resultado de la cuadrícula (ver [informe de ajuste](../../evaluation/reports/2026-11-19-lexical-tuning.md)):
  la normalización por longitud casi **duplica el MRR** (0,226 → 0,397) porque un anexo de 35.000 caracteres dejaba de ganar solo por acumular coincidencias; el título debe pesar **igual** que el texto (no más); y el contexto (peso C) sí ayuda (quitarlo baja el MRR de 0,445 a 0,340).
  Final: acierto@10 por unidad 55 % → **67 %**, MRR 0,226 → **0,445**, p95 40 ms.
- **Pendiente de medir**: respaldo AND-primero y `pg_trgm` solo si el golden set muestra fallos por ortografía (los fallos observados son de **vocabulario**, no de ortografía: eso lo cubre el significado).

## R3. Modelo de significado

- **Decisión**: comparar `text-embedding-3-small` (1536 dimensiones) y `text-embedding-3-large` (3072; también reducido con el parámetro `dimensions` a 1024/1536) y conservar el que
  gane en Recall@10 y rango recíproco; en empate, el más barato.
- **Por qué**: precios publicados: [small 0,02 USD](https://developers.openai.com/api/docs/models/text-embedding-3-small) y [large 0,13 USD](https://developers.openai.com/api/docs/models/text-embedding-3-large) por millón de tokens. Con ~175 mil tokens el
  costo es ≈ 0,004 y ≈ 0,023 USD: la comparación completa cuesta centavos (SC-010).
- **Verificar al usar la clave**: los identificadores vigentes (`models.retrieve`) y la versión del SDK (3.55.1 en PyPI al 2026-11-18, Python ≥ 3.10).
- **Alternativas**: modelo local (dependencias de ~1-2 GB; contradice ADR-0006); `ada-002` (superado).

### R3 bis — segundo proveedor: Gemini (2026-11-19)

Con la clave de OpenAI rechazada (HTTP 401) y sin API de embeddings en DeepSeek (su documentación oficial no la lista), se añadió **Gemini** detrás del mismo puerto para medir sin esperar. Se compara con el golden set igual que cualquier modelo (los vectores de cada modelo conviven en `retrieval_embeddings`).

- **Modelos**: `gemini-embedding-2` (GA, texto e imagen, hasta 8.192 tokens por texto, normaliza solo si se acortan) y `gemini-embedding-001` (solo texto, 2.048 tokens, `task_type` solo por la API nativa). Sus espacios no son comparables.
- **Endpoint compatible con OpenAI** (`/v1beta/openai/embeddings`): el adaptador de Gemini es una subclase del de OpenAI. No admite `task_type`; `gemini-embedding-2` pide en su lugar un **prefijo de texto**: consulta `task: search result | query: …`, documento `title: none | text: …`. Por eso el puerto distingue `EmbeddingPurpose.QUERY` y `DOCUMENT`.
- **Dimensiones**: 3072 (la de fábrica) para no tener que normalizar; la distancia coseno no depende de la norma.
- **Plan gratuito**: límites por proyecto no publicados en la documentación (se ven en AI Studio). **Medido con la API real**: `gemini-embedding-2` permite **100 solicitudes de embedding por minuto y cada texto de un lote cuenta como una** (la primera corrida se detuvo en 300 de 2.896 con 429). Por eso: lotes de 16, un tope de textos por minuto (`DRTC_GEMINI_MAX_REQUESTS_PER_MINUTE`, 80) y otro de tokens (`DRTC_GEMINI_MAX_TOKENS_PER_MINUTE`), y ante un 429 espera una ventana completa y reintenta el mismo lote; una corrida cortada se reanuda. **Datos**: en el plan gratuito Google puede usar y revisar lo que se envíe (ver [seguridad y privacidad](../../docs/architecture/security-privacy.md)).
- **Sin verificar al escribir esto**: que el endpoint compatible acepte listas de textos y devuelva `usage` (la documentación no lo dice): se comprueba con una sonda mínima antes de la corrida completa; si falla, plan B = API nativa `batchEmbedContents`.

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
