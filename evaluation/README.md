# Evaluación (golden set)

La calidad de la búsqueda y del asistente se mide con preguntas jurídicas revisadas, no con impresiones
(constitución, principios I.10 y IV): **ningún cambio de recuperación se integra si empeora las métricas
sin una decisión registrada**.

```text
evaluation/
├── datasets/
│   ├── golden-questions.schema.json   esquema v1 de cada pregunta (se valida en las pruebas)
│   └── golden-v1.jsonl                61 preguntas BORRADOR (52 con respuesta, 9 sin respuesta)
├── baseline.json                      métricas aceptadas de los métodos deterministas (compuerta de CI)
├── CHANGELOG.md                       por qué y cuándo cambió la línea base
└── reports/                           informes de corridas (.json y .md), p. ej. los que usan claves
```

## Formato de una pregunta (v1)

Una por línea (JSONL). Campos principales:

- `question` (máx. 300 caracteres), `intent` (`exact_provision`, `concept`, `requirements`, `exceptions`,
  `comparison`, `practical_case`, `out_of_scope`, `historical`), `audience` (`staff` | `citizen`).
- `answerable`: si el corpus permite responderla; si es `false`, se espera que no haya respaldo (la
  búsqueda no debe inventarlo) y `expected.citations` va vacío.
- `tags` (opcional): `explicit_reference` (la pregunta trae una referencia: «numeral 24.1 del artículo 24
  del TUO»), `colloquial` (lenguaje del personal, sin el vocabulario de la norma), `cross_norm` (la respuesta
  está en más de una norma).
- `expected.citations[]`, una por disposición que respalda la respuesta:
  - `version_id` y `provision` (cita legible, con la forma que entiende la búsqueda por referencia:
    `Ley 27181, art. 24, num. 24.1`);
  - **`path`**: la ruta estructural en esa edición (`articulo:24/numeral:24.1`). Solo puede ser `null` si lo
    citado no es una disposición del corpus (p. ej. el considerando de un decreto aprobatorio); entonces
    `notes` empieza con «path null» y explica por qué. Esa cita no cuenta para las métricas;
  - `pdf_pages` y `supporting_text`: el texto literal de respaldo y las páginas donde aparece.
- `review_status`: `draft` → `reviewed` → `approved` (solo `approved` cuenta para el criterio de
  lanzamiento) y `reviewed_by`.

**Las expectativas están ligadas a una versión** (`version_id`). Cuando SPIKE-01 cargue los textos
vigentes (p. ej. el TUO del DS 006-2026-JUS, que puede renumerar artículos), cada pregunta debe
revisarse y apuntar a la versión nueva.

### Qué verifica la suite automáticamente

- Que cada pregunta cumpla el esquema y que el conjunto sea suficientemente variado (≥ 50 preguntas, ≥ 12 con
  respuesta por norma, ≥ 8 sin respuesta, ≥ 4 que cruzan normas, todas las intenciones).
- Que la versión y las páginas existan y que el `supporting_text` aparezca en esas páginas **del PDF**.
- Que cada `path` exista en el corpus ingerido, que sus páginas coincidan con las citadas y que su texto (o el de
  sus descendientes) contenga el `supporting_text`.
- Que la búsqueda por referencia resuelva cada `provision` a su `path` exacto.

### Cómo agregar una pregunta real del personal

1. Escríbala **como la diría una persona**, sin copiar la redacción de la norma (si copia el texto, la
   medición favorece a la búsqueda por palabras y no dice nada del lenguaje real).
2. Busque la disposición que la responde en el lector (`/biblioteca/...`) y copie su ruta (`?p=`) y un fragmento
   literal corto como `supporting_text`.
3. Agréguela como `review_status: "draft"` con el siguiente `id` (`q-0NN`). Sin datos personales ni casos
   identificables.
4. Ejecute `uv run pytest tests/integration/corpus tests/e2e/test_golden_set_corpus.py`: si el `path` o el texto no
   coinciden con el corpus, la prueba dice cuál.
5. Como cambia el número de preguntas, hay que regenerar la línea base (ver abajo).

Las preguntas **sin respuesta** más útiles son las de «falso amigo»: comparten palabras con un pasaje del
corpus pero no lo tienen como respuesta (p. ej. «velocidad máxima en carretera» frente al *limitador de
velocidad* de los buses). Ponen a prueba que la búsqueda no presente algo parecido como si fuera la respuesta.

## Métricas

Se calculan **solo sobre las preguntas con respuesta que tienen alguna disposición esperada**, por método y en
dos niveles:

| Nivel | Cuándo un resultado es acierto |
|---|---|
| **unidad** | Es del mismo artículo, disposición o anexo (la *unidad de lectura* que abre el lector) que la esperada. Es el nivel de los umbrales del producto |
| **disposición** | Es la disposición esperada o una que está **debajo** de ella (el artículo esperado se satisface con uno de sus numerales). Una disposición «padre» no cuenta |

- **Acierto@K** (`hit@K`): porcentaje de preguntas con alguna disposición esperada entre los K primeros
  resultados distintos (K = 1, 3, 5, 10).
- **Cobertura@K** (`recall@K`): promedio de la fracción de disposiciones esperadas encontradas (importa en
  preguntas con varias citas).
- **MRR**: promedio de 1/posición de la primera disposición esperada encontrada (0 si no aparece).
- **Latencia** p50 / p95 por pregunta, y **peor resueltas** (las que no quedaron en 1.er lugar).
- **Sin respuesta**: cuántas devolvieron algo y, si el método da puntaje, su distribución. El umbral para
  abstenerse se calibra en la spec 005; aquí solo se informa.

Se informan también por etiqueta, por intención y por estado de revisión (borrador / aprobada).

## Comandos

```bash
cd backend
uv run drtc-retrieval eval --modes exact                      # mide y muestra el resumen
uv run drtc-retrieval eval --modes exact --out ../evaluation/reports/   # además escribe .json y .md
uv run drtc-retrieval eval --modes exact --check-baseline     # falla (código 1) si algo empeoró
```

## La línea base y la compuerta de CI

`baseline.json` fija las métricas aceptadas de los métodos **deterministas** (los que no necesitan red ni
claves: la búsqueda exacta y, desde la fase de palabras, la búsqueda por palabras), en total y por etiqueta.
La prueba `tests/e2e/test_retrieval_baseline.py` las vuelve a medir sobre las tres normas reales y **falla si
alguna cifra baja más de 0,02** (o si cambia el número de preguntas puntuadas, lo que indica que el golden set o
el corpus cambiaron y hay que regenerar la línea base a propósito).

Para cambiar la línea base (porque se amplió el golden set, o porque una decisión de diseño acepta una caída):

```bash
uv run drtc-retrieval eval --modes exact,lexical --write-baseline --reason "Motivo, qué cambió y quién lo aprobó"
```

El comando exige `--reason` y agrega por sí mismo una entrada fechada en `CHANGELOG.md`: no se puede mover la
línea base sin dejar constancia. Los métodos que necesitan una clave (significado y combinada) se miden a mano,
con confirmación de costo, y su informe se guarda en `reports/` y se resume en el ADR de la búsqueda.

## Reglas

- Sin datos personales ni casos reales identificables.
- Toda pregunta nueva entra como `draft`; la aprueba el revisor jurídico en un PR.
- Los borradores y las aprobadas se reportan por separado; solo las aprobadas cuentan para el criterio de lanzamiento.
- Las cifras de una corrida con un modelo de pago se guardan en `reports/` con su costo real.
