# Informe de evaluación de la búsqueda

Golden set: `golden-v1` · fecha: 2026-11-19. *Acierto@K* = porcentaje de preguntas con respuesta cuya disposición esperada aparece entre los K primeros resultados; *MRR* = rango recíproco medio. **Unidad** cuenta como acierto cualquier resultado del mismo artículo, disposición o anexo (lo que abre el lector); **disposición** exige la disposición esperada o una que esté debajo de ella.

## Método: exact

61 preguntas (52 con respuesta) · latencia p50 2.6 ms, p95 25 ms

**Nivel unidad de lectura**

| Grupo | Preguntas | Acierto@1 | Acierto@3 | Acierto@5 | Acierto@10 | MRR |
|---|---|---|---|---|---|---|
| Todas | 51 | 12 % | 12 % | 12 % | 12 % | 0.118 |
| etiqueta: colloquial | 29 | 0 % | 0 % | 0 % | 0 % | 0.000 |
| etiqueta: cross_norm | 4 | 0 % | 0 % | 0 % | 0 % | 0.000 |
| etiqueta: explicit_reference | 6 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: comparison | 5 | 0 % | 0 % | 0 % | 0 % | 0.000 |
| intención: concept | 7 | 0 % | 0 % | 0 % | 0 % | 0.000 |
| intención: exact_provision | 9 | 67 % | 67 % | 67 % | 67 % | 0.667 |
| intención: exceptions | 7 | 0 % | 0 % | 0 % | 0 % | 0.000 |
| intención: practical_case | 7 | 0 % | 0 % | 0 % | 0 % | 0.000 |
| intención: requirements | 16 | 0 % | 0 % | 0 % | 0 % | 0.000 |
| revisión: draft | 51 | 12 % | 12 % | 12 % | 12 % | 0.118 |

**Nivel disposición**

| Grupo | Preguntas | Acierto@1 | Acierto@3 | Acierto@5 | Acierto@10 | MRR |
|---|---|---|---|---|---|---|
| Todas | 51 | 12 % | 12 % | 12 % | 12 % | 0.118 |
| etiqueta: colloquial | 29 | 0 % | 0 % | 0 % | 0 % | 0.000 |
| etiqueta: cross_norm | 4 | 0 % | 0 % | 0 % | 0 % | 0.000 |
| etiqueta: explicit_reference | 6 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: comparison | 5 | 0 % | 0 % | 0 % | 0 % | 0.000 |
| intención: concept | 7 | 0 % | 0 % | 0 % | 0 % | 0.000 |
| intención: exact_provision | 9 | 67 % | 67 % | 67 % | 67 % | 0.667 |
| intención: exceptions | 7 | 0 % | 0 % | 0 % | 0 % | 0.000 |
| intención: practical_case | 7 | 0 % | 0 % | 0 % | 0 % | 0.000 |
| intención: requirements | 16 | 0 % | 0 % | 0 % | 0 % | 0.000 |
| revisión: draft | 51 | 12 % | 12 % | 12 % | 12 % | 0.118 |

**Sin respuesta en el corpus**: 9 preguntas; 0 devolvieron algún resultado.

**Peor resueltas** (las que no quedaron en 1.er lugar):

- `q-001` ¿Cuál es el plazo máximo de un procedimiento administrativo de evaluación previa? — esperada: articulo:39 · rangos de unidad: [None] · devolvió: —
- `q-002` ¿Cuántos días tengo para interponer un recurso administrativo y en qué plazo debe resolverse? — esperada: articulo:218/numeral:218.2 · rangos de unidad: [None] · devolvió: —
- `q-003` ¿Cuándo un procedimiento de evaluación previa está sujeto a silencio administrativo positivo? — esperada: articulo:35/numeral:35.1 · rangos de unidad: [None] · devolvió: —
- `q-004` ¿Qué competencias tienen los gobiernos regionales en materia de transporte terrestre según el RENAT? — esperada: articulo:10 · rangos de unidad: [None] · devolvió: —
- `q-005` ¿El RENAT se aplica al servicio de mototaxis? — esperada: articulo:2 · rangos de unidad: [None] · devolvió: —
- `q-006` ¿La Ley 27181 se aplica al transporte por cable? — esperada: articulo:1/numeral:1.2 · rangos de unidad: [None] · devolvió: —
- `q-007` ¿Cómo define la Ley 27181 el servicio complementario? — esperada: articulo:2/literal:d · rangos de unidad: [None] · devolvió: —
- `q-009` ¿Qué competencias tienen las municipalidades provinciales en transporte y tránsito terrestre? — esperada: articulo:17/numeral:17.1 · rangos de unidad: [None] · devolvió: —
- `q-011` Mi chofer cometió una infracción de tránsito mientras manejaba, ¿quién responde ante la autoridad: él o yo como dueño del vehículo? — esperada: articulo:24/numeral:24.1, articulo:24/numeral:24.2 · rangos de unidad: [None, None] · devolvió: —
- `q-012` ¿Cómo se clasifican las infracciones de tránsito y de transporte terrestre? — esperada: articulo:25 · rangos de unidad: [None] · devolvió: —

## Método: lexical

61 preguntas (52 con respuesta) · latencia p50 16.2 ms, p95 39.9 ms

**Nivel unidad de lectura**

| Grupo | Preguntas | Acierto@1 | Acierto@3 | Acierto@5 | Acierto@10 | MRR |
|---|---|---|---|---|---|---|
| Todas | 51 | 31 % | 51 % | 59 % | 67 % | 0.445 |
| etiqueta: colloquial | 29 | 24 % | 48 % | 52 % | 62 % | 0.391 |
| etiqueta: cross_norm | 4 | 25 % | 50 % | 50 % | 50 % | 0.411 |
| etiqueta: explicit_reference | 6 | 50 % | 67 % | 67 % | 67 % | 0.575 |
| intención: comparison | 5 | 40 % | 40 % | 40 % | 60 % | 0.457 |
| intención: concept | 7 | 29 % | 57 % | 71 % | 71 % | 0.464 |
| intención: exact_provision | 9 | 56 % | 67 % | 78 % | 78 % | 0.628 |
| intención: exceptions | 7 | 29 % | 43 % | 43 % | 57 % | 0.395 |
| intención: practical_case | 7 | 14 % | 71 % | 71 % | 71 % | 0.416 |
| intención: requirements | 16 | 25 % | 38 % | 50 % | 62 % | 0.366 |
| revisión: draft | 51 | 31 % | 51 % | 59 % | 67 % | 0.445 |

**Nivel disposición**

| Grupo | Preguntas | Acierto@1 | Acierto@3 | Acierto@5 | Acierto@10 | MRR |
|---|---|---|---|---|---|---|
| Todas | 51 | 20 % | 37 % | 37 % | 47 % | 0.301 |
| etiqueta: colloquial | 29 | 14 % | 28 % | 28 % | 38 % | 0.220 |
| etiqueta: cross_norm | 4 | 0 % | 25 % | 25 % | 25 % | 0.094 |
| etiqueta: explicit_reference | 6 | 33 % | 50 % | 50 % | 50 % | 0.434 |
| intención: comparison | 5 | 20 % | 20 % | 20 % | 20 % | 0.217 |
| intención: concept | 7 | 29 % | 57 % | 57 % | 57 % | 0.438 |
| intención: exact_provision | 9 | 44 % | 56 % | 56 % | 67 % | 0.530 |
| intención: exceptions | 7 | 29 % | 29 % | 29 % | 43 % | 0.302 |
| intención: practical_case | 7 | 0 % | 43 % | 43 % | 71 % | 0.230 |
| intención: requirements | 16 | 6 % | 25 % | 25 % | 31 % | 0.169 |
| revisión: draft | 51 | 20 % | 37 % | 37 % | 47 % | 0.301 |

**Sin respuesta en el corpus**: 9 preguntas; 9 devolvieron algún resultado.
Mejor puntaje devuelto: {'min': 0.0203, 'median': 0.0525, 'max': 0.0644}.

**Peor resueltas** (las que no quedaron en 1.er lugar):

- `q-005` ¿El RENAT se aplica al servicio de mototaxis? — esperada: articulo:2 · rangos de unidad: [None] · devolvió: articulo:100/numeral:100.4/numeral:100.4.1/numeral:100.4.1.5, articulo:1, articulo:56
- `q-018` ¿Quiénes no pueden obtener autorización para prestar servicio de transporte? — esperada: articulo:4-A/numeral:4-A.1 · rangos de unidad: [None] · devolvió: articulo:55, articulo:54, articulo:62/numeral:62.4
- `q-022` ¿Qué busca lograr el Estado con su intervención en el transporte y el tránsito? — esperada: articulo:3 · rangos de unidad: [None] · devolvió: seccion:sexta/disposiciones:complementarias-finales/segunda, articulo:36, disposiciones:transitorias/segunda
- `q-023` ¿El Estado debe favorecer que haya competencia entre las empresas de transporte? — esperada: articulo:4/numeral:4.1 · rangos de unidad: [None] · devolvió: articulo:10, articulo:15, articulo:16
- `q-036` ¿Qué pasa si una empresa presta servicio de transporte sin tener autorización? ¿Cuál es la infracción? — esperada: anexo:2 · rangos de unidad: [None] · devolvió: articulo:62/numeral:62.4, articulo:54, articulo:55
- `q-038` ¿Puede un pasajero subir al bus en estado de ebriedad? — esperada: articulo:77/numeral:77.1/numeral:77.1.3 · rangos de unidad: [None] · devolvió: articulo:VII/numeral:1, articulo:120/numeral:120.2, articulo:158/numeral:158.2
- `q-045` ¿Cómo se cuentan los plazos en días en un trámite administrativo? — esperada: articulo:144/numeral:144.1 · rangos de unidad: [None] · devolvió: articulo:153, articulo:66, articulo:147/numeral:147.4
- `q-039` Según el numeral 24.1 del artículo 24 del TUO de la LPAG, ¿en cuántos días debe notificarse un acto administrativo? — esperada: articulo:24/numeral:24.1 · rangos de unidad: [18] · devolvió: articulo:15, articulo:8, articulo:1
- `q-047` Según el numeral 213.3 del TUO, ¿cuánto tiempo tiene la entidad para anular de oficio un acto administrativo? — esperada: articulo:213/numeral:213.3 · rangos de unidad: [17] · devolvió: articulo:15, articulo:8, articulo:1
- `q-053` ¿Qué plazo de prescripción se aplica para sancionar una infracción de transporte: el del reglamento de transporte o el de la ley del procedimiento administrativo? — esperada: articulo:130/numeral:130.1, articulo:252/numeral:252.1 · rangos de unidad: [15, 26] · devolvió: articulo:24, articulo:I, articulo:199/numeral:199.6
