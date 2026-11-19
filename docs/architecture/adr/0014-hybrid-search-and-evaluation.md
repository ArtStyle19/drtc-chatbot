# 0014. Búsqueda por contenido híbrida, con la evaluación primero

- Estado: **propuesta** (pasa a aceptada cuando se registren las cifras del significado, ver «Resultados»)
- Fecha: 2026-11-19
- Decisores: líder del proyecto (spec 004)

## Contexto y problema

Hasta la spec 003 solo se encontraba una disposición por su **referencia** («art. 5 Ley 27181»). El personal
necesita encontrarla por lo que dice («¿se puede cobrar por el servicio de mototaxi?»), y ese es el cimiento
del bot que responde con citas (spec 005). La constitución obliga desde esta spec a que **ningún cambio de
recuperación se funda si empeora las métricas del golden set** (IV), a que una referencia identificada
gane a la similitud (I.6) y a que lo que la gente busca no se guarde ni se registre (VI). Había que decidir
cómo medir, cómo combinar los métodos y qué hacer cuando falla el proveedor de significado.

## Opciones consideradas

**Orden de construcción**: (1) construir la búsqueda y medirla después; (2) **la evaluación primero**: golden
set, métricas y una línea base antes de que exista cualquier búsqueda, y cada brazo se mide al nacer.

**Palabras**: `unaccent` + `spanish_stem` (planeada) frente a la configuración estándar `spanish` con la
consulta ampliada por las tildes del corpus. Se midió: la primera rompe el singular/plural de «-ción»
(366 de 6.403 palabras distintas se lematizan distinto).

**Significado**: modelo local (dependencias de 1-2 GB, contradice ADR-0006) frente a un proveedor externo
detrás de un puerto; índice aproximado (HNSW) frente a recorrido exacto.

**Combinación**: sumar puntajes crudos (escalas incomparables) frente a *Reciprocal Rank Fusion*.

## Decisión

1. **Evaluación primero.** Golden set `golden-v1` (61 preguntas, 9 sin respuesta, todas `draft` hasta que las
   apruebe el revisor jurídico), métricas por **disposición** (la ruta es la esperada o está debajo) y por
   **unidad de lectura**, y una **compuerta determinista en CI sin red**: los brazos exacto y de palabras contra
   `evaluation/baseline.json` (tolerancia 0,02). Cambiar la línea base exige `--reason` y una entrada en
   `evaluation/CHANGELOG.md`. Significado y combinada cuestan dinero: se miden a mano con estimación previa y
   confirmación, y su informe se guarda en `evaluation/reports/`.
2. **Tres brazos, la referencia primero.** Exacto (`LookupReference`, siempre primero y marcado) → palabras
   (PostgreSQL FTS `spanish`, consulta con OR y ampliada con las tildes del corpus, `ts_rank_cd` con
   normalización por longitud y pesos 0,1/0,2/0,4/0,4, resaltado como segmentos y nunca HTML) y significado
   (embeddings en pgvector, **coseno exacto, sin índice aproximado**: 2.896 ventanas se recorren en milisegundos)
   → fusionados con **RRF (k = 60, 50 candidatos por brazo)** y agrupados por unidad de lectura.
3. **Degradar, no fallar.** Sin proveedor, con error, con cuota agotada, con demora (3 s) o con vectores sin
   calcular, la búsqueda responde `200` con palabras y `degraded` dice por qué.
4. **El índice es derivado y reconstruible** (`retrieval_passages` con `tsvector` generado,
   `retrieval_embeddings` con varios modelos a la vez, `retrieval_accents`); `BuildIndex` es idempotente por
   huella de contenido y el significado se calcula aparte (`embed`).
5. **Proveedores de significado detrás del puerto `EmbeddingProvider`**: OpenAI y Gemini (el mismo adaptador
   apuntado a otra dirección, con el **propósito** del texto —consulta o documento— porque `gemini-embedding-2`
   exige un prefijo distinto). Una persona confirma antes de que salga texto (`--yes`), con la estimación y el
   aviso de datos del proveedor.
6. **Privacidad de lo que se busca**: el texto no se registra (solo su tamaño), las respuestas 422 no lo
   devuelven, la aplicación registra cada petición sin la cadena de consulta y `uvicorn` y `nginx` no la
   escriben; escribir en el encabezado solo consulta `/lookup`, nunca `/search`. Un caché en memoria de
   vectores de consulta existe **solo** en la línea de comandos.
7. **Sin reordenador, sin índice aproximado, sin sinónimos propios** hasta que los números muestren una
   brecha que lo justifique (principio VIII).

## Hallazgos que cambiaron el diseño

- `unaccent` + `spanish_stem` rompía «-ción»: configuración `spanish` + ampliación de la consulta.
- La normalización por longitud casi **duplicó el MRR** de palabras (0,226 → 0,445).
- El analizador del corpus leía referencias cruzadas como numerales (RENAT 108.1.8 fantasma, art. 20.1 con
  todo el texto sustituido); se corrigió con pruebas contra el PDF.
- La comprobación de privacidad con el stack real encontró **tres fugas** del texto de la búsqueda (422,
  registro de acceso de `uvicorn` y de `nginx`); se cerraron.
- Gemini, medido con la API real: el endpoint compatible omite `index` en el primer elemento; el plan gratuito
  permite **100 solicitudes de embedding por minuto y 1.000 por día, una por texto**, y se cortó por el tope
  diario. El adaptador lo reconoce y se detiene en vez de esperar.

## Consecuencias

- (+) Cada mejora o regresión de la búsqueda se ve en cifras; la compuerta corre en CI sin red ni costo.
- (+) Cambiar de proveedor o de modelo no toca el dominio: los vectores de cada modelo conviven.
- (+) Sin clave o sin cuota la herramienta sigue útil, con palabras.
- (−) El golden set lo redactó el asistente a partir de los mismos textos: puede favorecer el vocabulario de
  la norma; se mitiga con preguntas coloquiales y sin respuesta, y exige la aprobación del revisor.
- (−) El corpus sigue **sin verificar** (SPIKE-01): los resultados muestran «No verificado» y las expectativas
  del golden set están ligadas a una `version_id`.
- (−) El plan gratuito de Google puede usar y revisar lo que se envíe: solo texto de normas y preguntas de
  prueba; para usuarios reales hace falta un proyecto de pago o un modelo local y revisión con Asesoría Jurídica.

## Resultados de la medición

> **Pendiente**: vectorizar el corpus completo con el modelo elegido y correr
> `drtc-retrieval eval --modes lexical,vector,hybrid`. Hasta entonces solo hay cifras de palabras.

| Método (nivel unidad, 52 preguntas con respuesta) | acierto@10 | MRR | p95 |
|---|---|---|---|
| Exacto | 12 % | 0,118 | 29 ms |
| Palabras | 67 % | 0,445 | 47 ms |
| Significado | pendiente | pendiente | pendiente |
| Combinada | pendiente | pendiente | pendiente |

Modelo elegido, costo real (SC-010 < US$ 0,50), ablaciones (k de RRF, candidatos por brazo) y la decisión
sobre el reordenador: **pendientes**.
