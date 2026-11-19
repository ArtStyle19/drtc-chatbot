# Ajuste del brazo de palabras (spec 004, T024)

Golden set `golden-v1` (61 preguntas, 51 puntuadas, todas borrador). Nivel **unidad de lectura**
salvo donde se indica. Se cambió **una cosa por vez**, sobre el índice real de las tres normas
(2.880 pasajes). Cada pregunta vale ≈ 2 puntos porcentuales: diferencias de 1-2 preguntas son ruido.

## 0. Punto de partida

| Configuración | Acierto@1 | @3 | @5 | @10 | MRR | p95 |
|---|---|---|---|---|---|---|
| Pesos (0,1; 0,2; 0,4; 1,0), normalización 1 | 10 % | 24 % | 39 % | 55 % | 0,226 | 52 ms |

## 1. Normalización de `ts_rank_cd` (pesos por defecto)

| Banderas | @1 | @3 | @10 | MRR | MRR disposición |
|---|---|---|---|---|---|
| 0 (ninguna) | 5,9 % | 17,6 % | 47,1 % | 0,181 | 0,135 |
| 1 (log de la longitud) | 9,8 % | 23,5 % | 54,9 % | 0,226 | 0,156 |
| **2 (longitud del pasaje)** | **27,5 %** | **45,1 %** | **62,7 %** | **0,397** | 0,176 |
| 4 (distancia armónica) | 17,6 % | 31,4 % | 51,0 % | 0,285 | 0,177 |
| 8 (palabras únicas) | 27,5 % | 39,2 % | 60,8 % | 0,373 | 0,149 |
| 16 | 9,8 % | 21,6 % | 49,0 % | 0,215 | 0,146 |
| 32 (escala r/(r+1)) | 5,9 % | 17,6 % | 47,1 % | 0,181 | 0,135 |
| 1+4 | 21,6 % | 39,2 % | 52,9 % | 0,326 | 0,196 |

*Control de cordura*: la bandera 32 solo reescala el puntaje sin cambiar el orden, y da exactamente lo mismo que 0.
**Decisión: 2.** Dividir por la longitud evita que un anexo de 35.000 caracteres (Anexos 1 y 2 del RENAT) gane
solo por acumular coincidencias; es el cambio más grande de todo el ajuste y tiene explicación causal.

## 2. Pesos (D, C, B, A) con normalización 2

A = título · B = texto · C = miga de pan y encabezado del padre · D = (sin uso).

| Pesos | @1 | @3 | @10 | MRR | disp. @10 | disp. MRR |
|---|---|---|---|---|---|---|
| 0,1 · 0,2 · 0,4 · 1,0 (inicial) | 27,5 % | 45,1 % | 62,7 % | 0,397 | 29,4 % | 0,176 |
| 0,0 · 0,0 · 0,4 · 1,0 (sin contexto) | 31,4 % | 45,1 % | 64,7 % | 0,433 | 31,4 % | 0,182 |
| 0,2 · 0,3 · 0,6 · 1,0 | 27,5 % | 45,1 % | 70,6 % | 0,409 | 39,2 % | 0,212 |
| **0,1 · 0,2 · 0,4 · 0,4** | **31,4 %** | **51,0 %** | 66,7 % | **0,445** | **47,1 %** | 0,301 |
| 0,0 · 0,2 · 0,4 · 0,4 | 31,4 % | 51,0 % | 66,7 % | 0,445 | 47,1 % | 0,301 |
| 0,2 · 0,2 · 0,4 · 0,4 | 31,4 % | 51,0 % | 66,7 % | 0,445 | 47,1 % | 0,301 |
| 0,0 · 0,0 · 0,4 · 0,4 (sin contexto) | 19,6 % | 41,2 % | 64,7 % | 0,340 | 45,1 % | 0,276 |
| 0,1 · 0,1 · 0,4 · 0,4 | 29,4 % | 51,0 % | 64,7 % | 0,425 | 43,1 % | 0,297 |
| 0,1 · 0,3 · 0,4 · 0,4 | 23,5 % | 49,0 % | 68,6 % | 0,404 | 39,2 % | 0,241 |
| 0,1 · 0,2 · 0,4 · 0,2 | 31,4 % | 49,0 % | 64,7 % | 0,423 | 47,1 % | 0,327 |
| 0,1 · 0,2 · 0,4 · 0,6 | 27,5 % | 47,1 % | 70,6 % | 0,413 | 41,2 % | 0,220 |
| 0,1 · 0,2 · 0,6 · 0,6 | 27,5 % | 51,0 % | 64,7 % | 0,418 | 43,1 % | 0,295 |
| 0,1 · 0,2 · 0,2 · 0,4 | 25,5 % | 39,2 % | 62,7 % | 0,382 | 29,4 % | 0,174 |

**Decisión: (0,1; 0,2; 0,4; 0,4).** Es una **meseta estable**: variar D de 0 a 0,2 no cambia nada, y sus vecinos
inmediatos empeoran o no mejoran. Se observa además que:

- el contexto (miga de pan + encabezado del padre, peso C) **sí ayuda**: quitarlo baja el MRR de 0,445 a 0,340;
- el título debe pesar **igual que el texto**, no más: títulos como «Recursos administrativos» son genéricos;
- con A = 0,6 sube el acierto@10 (70,6 %) pero baja el MRR de disposición (0,220): se prefirió la mejor ubicación.

## 3. Resultado final del brazo de palabras

| Nivel | @1 | @3 | @5 | @10 | MRR |
|---|---|---|---|---|---|
| Unidad | 31 % | 51 % | 59 % | 67 % | 0,445 |
| Disposición | 20 % | 37 % | 37 % | 47 % | 0,301 |

Latencia p50 16 ms · p95 40 ms (objetivo SC-005: < 500 ms).
De 0,226 a 0,445 de MRR y de 55 % a 67 % de acierto@10 solo con dos cambios de configuración medidos.

## 4. Qué sigue fallando (lo que debe aportar la búsqueda por significado)

Todos los fallos del brazo de palabras son de **vocabulario**, no de ranking:

| Pregunta | La norma dice |
|---|---|
| «¿El RENAT se aplica al servicio de **mototaxis**?» | «vehículos menores motorizados» |
| «¿Quiénes **no pueden obtener** autorización…?» | «**impedidas** para obtener título habilitante» |
| «¿Qué busca lograr el Estado con su **intervención**…?» | «la **acción** estatal… se orienta a…» |
| «¿Debe **favorecer** que haya competencia…?» | «el Estado **incentiva** la libre y leal competencia» |
| «¿Puede un **pasajero** subir al **bus** ebrio?» | «los **usuarios**… el **vehículo**…» |

Las preguntas con referencia explícita (`explicit_reference`) quedan profundas aquí (rangos 15-18) porque las
palabras de la pregunta («días», «plazo») son comunes: la búsqueda exacta (que las pone en 1.er lugar) es la que
las resuelve, y la fusión la mantiene primero (constitución I.6).

Las 9 preguntas **sin respuesta** devuelven resultados con puntajes bajos (0,020 - 0,064): el umbral para
abstenerse se calibra en la spec 005, comparando con la distribución de las preguntas con respuesta.

## 5. Defecto de vocabulario encontrado (acentos)

La configuración `es_unaccent` planeada rompía el singular/plural de las palabras en «-ción» (apelación ↔
apelaciones): el lematizador solo reconoce «-ción» **con** tilde. Medido sobre el vocabulario real del corpus,
**366 de 6.403 palabras distintas** (202 en «-ción») se lematizan distinto si se teclean sin tilde. Solución
adoptada: configuración estándar `spanish` para los documentos y, en la consulta, ampliar cada palabra tecleada
sin tilde con su forma acentuada (vocabulario del corpus, con la regla «-ión» de respaldo).
