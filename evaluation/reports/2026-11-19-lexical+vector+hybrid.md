# Informe de evaluación de la búsqueda

Golden set: `golden-v1` · fecha: 2026-11-19. *Acierto@K* = porcentaje de preguntas con respuesta cuya disposición esperada aparece entre los K primeros resultados; *MRR* = rango recíproco medio. **Unidad** cuenta como acierto cualquier resultado del mismo artículo, disposición o anexo (lo que abre el lector); **disposición** exige la disposición esperada o una que esté debajo de ella.

## Método: lexical

61 preguntas (52 con respuesta) · latencia p50 16.2 ms, p95 39.2 ms

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

## Método: vector

61 preguntas (52 con respuesta) · latencia p50 531.3 ms, p95 933.2 ms

**Nivel unidad de lectura**

| Grupo | Preguntas | Acierto@1 | Acierto@3 | Acierto@5 | Acierto@10 | MRR |
|---|---|---|---|---|---|---|
| Todas | 51 | 84 % | 96 % | 98 % | 100 % | 0.907 |
| etiqueta: colloquial | 29 | 76 % | 93 % | 97 % | 100 % | 0.859 |
| etiqueta: cross_norm | 4 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| etiqueta: explicit_reference | 6 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: comparison | 5 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: concept | 7 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: exact_provision | 9 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: exceptions | 7 | 71 % | 86 % | 86 % | 100 % | 0.786 |
| intención: practical_case | 7 | 57 % | 100 % | 100 % | 100 % | 0.786 |
| intención: requirements | 16 | 81 % | 94 % | 100 % | 100 % | 0.891 |
| revisión: draft | 51 | 84 % | 96 % | 98 % | 100 % | 0.907 |

**Nivel disposición**

| Grupo | Preguntas | Acierto@1 | Acierto@3 | Acierto@5 | Acierto@10 | MRR |
|---|---|---|---|---|---|---|
| Todas | 51 | 76 % | 94 % | 96 % | 98 % | 0.852 |
| etiqueta: colloquial | 29 | 62 % | 90 % | 93 % | 97 % | 0.763 |
| etiqueta: cross_norm | 4 | 75 % | 100 % | 100 % | 100 % | 0.875 |
| etiqueta: explicit_reference | 6 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: comparison | 5 | 80 % | 100 % | 100 % | 100 % | 0.900 |
| intención: concept | 7 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: exact_provision | 9 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: exceptions | 7 | 43 % | 86 % | 86 % | 86 % | 0.608 |
| intención: practical_case | 7 | 57 % | 86 % | 100 % | 100 % | 0.743 |
| intención: requirements | 16 | 75 % | 94 % | 94 % | 100 % | 0.844 |
| revisión: draft | 51 | 76 % | 94 % | 96 % | 98 % | 0.852 |

**Sin respuesta en el corpus**: 9 preguntas; 9 devolvieron algún resultado.
Mejor puntaje devuelto: {'min': 0.6169, 'median': 0.672, 'max': 0.7393}.

**Peor resueltas** (las que no quedaron en 1.er lugar):

- `q-046` ¿En qué casos el silencio de la entidad significa que me negaron lo que pedí? — esperada: articulo:38/numeral:38.1 · rangos de unidad: [6] · devolvió: articulo:199/numeral:199.3, articulo:36/numeral:36.1, articulo:199/numeral:199.1
- `q-018` ¿Quiénes no pueden obtener autorización para prestar servicio de transporte? — esperada: articulo:4-A/numeral:4-A.1 · rangos de unidad: [4] · devolvió: articulo:55/numeral:55.1/numeral:55.1.10, articulo:37/numeral:37.9, articulo:57/numeral:57.3/numeral:57.3.4
- `q-005` ¿El RENAT se aplica al servicio de mototaxis? — esperada: articulo:2 · rangos de unidad: [3] · devolvió: articulo:3/numeral:3.63/numeral:3.63.6, articulo:7/numeral:7.1/numeral:7.1.2/numeral:7.1.2.6, articulo:2
- `q-013` ¿Es obligatorio sacar el SOAT para que un carro pueda circular? — esperada: articulo:30/numeral:30.1 · rangos de unidad: [2] · devolvió: articulo:28, articulo:30/numeral:30.1, articulo:30/numeral:30.2
- `q-032` Me pusieron una multa grande, ¿puedo pagarla en cuotas? — esperada: articulo:132/numeral:132.1 · rangos de unidad: [2] · devolvió: articulo:134/numeral:134.1/numeral:134.1.1, articulo:134/numeral:134.1/numeral:134.1.2, articulo:134/numeral:134.1/numeral:134.1.4
- `q-036` ¿Qué pasa si una empresa presta servicio de transporte sin tener autorización? ¿Cuál es la infracción? — esperada: anexo:2 · rangos de unidad: [2] · devolvió: articulo:103/numeral:103.2/numeral:103.2.1, anexo:2, articulo:97/numeral:97.1/numeral:97.1.1
- `q-044` El trámite de mi expediente está paralizado y el funcionario no responde, ¿qué puedo hacer? — esperada: articulo:169/numeral:169.1, articulo:169/numeral:169.2 · rangos de unidad: [2, 2] · devolvió: articulo:265/literal:a, articulo:169/numeral:169.2, articulo:265/literal:b
- `q-045` ¿Cómo se cuentan los plazos en días en un trámite administrativo? — esperada: articulo:144/numeral:144.1 · rangos de unidad: [2] · devolvió: articulo:145/numeral:145.1, articulo:144/numeral:144.1, articulo:145/numeral:145.3

## Método: hybrid

61 preguntas (52 con respuesta) · latencia p50 41.4 ms, p95 525.7 ms

**Nivel unidad de lectura**

| Grupo | Preguntas | Acierto@1 | Acierto@3 | Acierto@5 | Acierto@10 | MRR |
|---|---|---|---|---|---|---|
| Todas | 51 | 84 % | 96 % | 98 % | 100 % | 0.907 |
| etiqueta: colloquial | 29 | 76 % | 93 % | 97 % | 100 % | 0.859 |
| etiqueta: cross_norm | 4 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| etiqueta: explicit_reference | 6 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: comparison | 5 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: concept | 7 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: exact_provision | 9 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: exceptions | 7 | 71 % | 86 % | 86 % | 100 % | 0.786 |
| intención: practical_case | 7 | 57 % | 100 % | 100 % | 100 % | 0.786 |
| intención: requirements | 16 | 81 % | 94 % | 100 % | 100 % | 0.891 |
| revisión: draft | 51 | 84 % | 96 % | 98 % | 100 % | 0.907 |

**Nivel disposición**

| Grupo | Preguntas | Acierto@1 | Acierto@3 | Acierto@5 | Acierto@10 | MRR |
|---|---|---|---|---|---|---|
| Todas | 51 | 76 % | 88 % | 92 % | 94 % | 0.830 |
| etiqueta: colloquial | 29 | 62 % | 83 % | 90 % | 93 % | 0.732 |
| etiqueta: cross_norm | 4 | 75 % | 100 % | 100 % | 100 % | 0.875 |
| etiqueta: explicit_reference | 6 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: comparison | 5 | 80 % | 100 % | 100 % | 100 % | 0.900 |
| intención: concept | 7 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: exact_provision | 9 | 100 % | 100 % | 100 % | 100 % | 1.000 |
| intención: exceptions | 7 | 43 % | 71 % | 71 % | 71 % | 0.569 |
| intención: practical_case | 7 | 57 % | 71 % | 86 % | 100 % | 0.679 |
| intención: requirements | 16 | 75 % | 88 % | 94 % | 94 % | 0.818 |
| revisión: draft | 51 | 76 % | 88 % | 92 % | 94 % | 0.830 |

**Sin respuesta en el corpus**: 9 preguntas; 9 devolvieron algún resultado.
Mejor puntaje devuelto: {'min': 1.0, 'median': 1.0, 'max': 1.125}.

**Peor resueltas** (las que no quedaron en 1.er lugar):

- `q-046` ¿En qué casos el silencio de la entidad significa que me negaron lo que pedí? — esperada: articulo:38/numeral:38.1 · rangos de unidad: [6] · devolvió: articulo:199/numeral:199.3, articulo:199/numeral:199.1, articulo:199/numeral:199.4
- `q-018` ¿Quiénes no pueden obtener autorización para prestar servicio de transporte? — esperada: articulo:4-A/numeral:4-A.1 · rangos de unidad: [4] · devolvió: articulo:55/numeral:55.1/numeral:55.1.10, articulo:55/numeral:55.1/numeral:55.1.11, articulo:55
- `q-005` ¿El RENAT se aplica al servicio de mototaxis? — esperada: articulo:2 · rangos de unidad: [3] · devolvió: articulo:3/numeral:3.63/numeral:3.63.6, articulo:3/numeral:3.63, articulo:3/numeral:3.63/numeral:3.63.4
- `q-013` ¿Es obligatorio sacar el SOAT para que un carro pueda circular? — esperada: articulo:30/numeral:30.1 · rangos de unidad: [2] · devolvió: articulo:28, articulo:30/numeral:30.1, articulo:30/numeral:30.2
- `q-032` Me pusieron una multa grande, ¿puedo pagarla en cuotas? — esperada: articulo:132/numeral:132.1 · rangos de unidad: [2] · devolvió: articulo:134/numeral:134.1/numeral:134.1.1, articulo:134/numeral:134.1/numeral:134.1.2, articulo:134/numeral:134.1/numeral:134.1.4
- `q-036` ¿Qué pasa si una empresa presta servicio de transporte sin tener autorización? ¿Cuál es la infracción? — esperada: anexo:2 · rangos de unidad: [2] · devolvió: articulo:103/numeral:103.2/numeral:103.2.1, articulo:103/numeral:103.2/numeral:103.2.8, anexo:2
- `q-044` El trámite de mi expediente está paralizado y el funcionario no responde, ¿qué puedo hacer? — esperada: articulo:169/numeral:169.1, articulo:169/numeral:169.2 · rangos de unidad: [2, 2] · devolvió: articulo:265/literal:a, articulo:265/literal:b, articulo:265
- `q-045` ¿Cómo se cuentan los plazos en días en un trámite administrativo? — esperada: articulo:144/numeral:144.1 · rangos de unidad: [2] · devolvió: articulo:145/numeral:145.1, articulo:145/numeral:145.3, articulo:145/numeral:145.2
