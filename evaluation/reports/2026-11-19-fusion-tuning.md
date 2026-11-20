# Ajuste de la fusión de palabras y significado (spec 004, T037)

Golden set `golden-v1` (61 preguntas, 52 con respuesta, todas borrador), modelo `gemini-embedding-2` (3.072 dimensiones),
corpus completo vectorizado (2.896 ventanas). Nivel **unidad de lectura** salvo donde se indica. **Cada pregunta con
respuesta vale ≈ 2 puntos porcentuales**: diferencias de una o dos preguntas son ruido. Todas las configuraciones se
corrieron en un solo proceso, con el vector de cada pregunta pedido una sola vez.

## 1. El problema: con pesos iguales la combinada empeora al método bueno

| Método | Acierto@1 | @3 | @5 | @10 | MRR | Disposición @10 / MRR |
|---|---|---|---|---|---|---|
| Palabras solas | 31 % | 51 % | 59 % | 67 % | 0,445 | 47 % / 0,301 |
| **Significado solo** | **84 %** | **96 %** | **98 %** | **100 %** | **0,907** | **98 % / 0,852** |
| Combinada, pesos iguales, k = 60 (informe `…-equal-weights`) | 71 % | 84 % | 88 % | 98 % | 0,792 | 80 % / 0,564 |

La combinada quedó **por debajo del significado solo** (98 % < 100 % de acierto@10): incumple SC-004. Con pesos iguales el brazo
más débil arrastra al más fuerte.

## 2. Los dos brazos son complementarios (por qué no basta con apagar las palabras)

Posición de la unidad esperada, solo donde la combinada con pesos iguales difiere del significado solo:

| Pregunta | Palabras | Significado | Combinada 1:1 | Combinada ×3, k = 20 |
|---|---|---|---|---|
| q-013 «¿Es obligatorio sacar el SOAT…?» | 1 | 2 | 1 | 1 |
| q-032 «…una multa grande, ¿puedo pagarla en cuotas?» | 1 | 2 | 1 | 1 |
| q-044 «El trámite de mi expediente está paralizado…» | 1 | 2 | 1 | 1 |
| q-046 «¿En qué casos el silencio de la entidad…?» | 1 | 6 | 3 | 6 |
| q-023 «¿El Estado debe favorecer la competencia…?» | — | 1 | **9** | 1 |
| q-022 «¿Qué busca lograr el Estado con su intervención…?» | — | 1 | **5** | 1 |
| q-005 «¿El RENAT se aplica al servicio de mototaxis?» | — | 3 | **9** | 3 |
| q-045 «¿Cómo se cuentan los plazos en días…?» | — | 2 | **10** | 3 |

Las palabras **ganan** cuando la pregunta trae un término exacto (SOAT, multa, plazo) y **fallan por completo** cuando el vocabulario
es otro (mototaxi / «vehículos menores»). Con pesos iguales, los resultados sin relación que devuelven las palabras empujan
hacia abajo lo que el significado ya tenía bien.

## 3. Barrido (un cambio por vez, luego rejilla)

**k de RRF** (pesos 1:1, 50 candidatos por brazo): k = 10 → @10 100 %, MRR 0,818 · k = 20 → 98 %, 0,800 · k = 60 → 98 %, 0,792 · k = 100 → 98 %, 0,789.

**Peso del significado** (k = 60): ×1,5 → 100 %, 0,823 · ×2 → 100 %, 0,848 · ×3 → 100 %, 0,855 · ×5 → 100 %, 0,872 · ×10 → 100 %, 0,900.

**Candidatos por brazo N** (k = 60, ×3): 20 → 0,874 · 50 → 0,855 · 100 → 0,867 · 200 → 0,868 (ruido: se deja en 50).

**Agrupar por unidad con el mejor pasaje (`max`) o con la suma de sus pasajes (`sum`)**: `sum` es claramente peor (MRR 0,593 con 1:1; 0,598 con ×3;
acierto@10 82 % y 92 %) porque premia a los artículos con muchos numerales. Se conserva `max`.

**Rejilla fina** (k × peso del significado; acierto@10 = 100 % en todas salvo k = 5, ×2 con 98 %):

| k \ peso | ×2 | ×3 | ×4 | ×6 |
|---|---|---|---|---|
| 5 | 0,900 / 0,769 | 0,893 / 0,794 | 0,894 / 0,794 | **0,907 / 0,830** |
| 10 | 0,913 / 0,754 | 0,893 / 0,758 | 0,894 / 0,773 | 0,894 / 0,796 |
| 20 | 0,898 / 0,730 | 0,891 / 0,729 | 0,913 / 0,764 | 0,904 / 0,777 |
| 40 | 0,851 / 0,629 | 0,873 / 0,661 | 0,890 / 0,694 | 0,900 / 0,768 |

(MRR por unidad / MRR por disposición; significado solo: 0,907 / 0,852.)

## 4. Decisión

**k = 5 y el significado pesa 6 veces lo que pesan las palabras** (`DRTC_SEARCH_RRF_K=5`, `DRTC_SEARCH_VECTOR_WEIGHT=6`).
Criterio fijado antes de elegir: el mayor promedio entre el MRR por unidad y por disposición dentro de la zona estable.
**Verificado pregunta por pregunta con la configuración elegida**: la combinada deja **el mismo orden de unidades que el significado solo en
las 61 preguntas**. Es decir, a este peso las palabras ya no cambian el ranking por unidad: no rescatan q-013, q-032 ni q-044 (eso solo
ocurría con pesos menores, como ×3 con k = 20, que a cambio perdía q-009, q-042 y q-051 frente al significado). En este golden set el balance entre
«rescatar términos exactos» y «no ensuciar lo que el significado ya acierta» es **neutro**: las dos opciones empatan, y se eligió por la regla fijada de antemano.
Lo que las palabras siguen aportando: el fragmento con las palabras coincidentes resaltadas, la etiqueta «Por palabras» y que la búsqueda siga funcionando sin proveedor.

| Método (unidad, 52 con respuesta) | Acierto@1 | @3 | @5 | @10 | MRR | Disposición @10 / MRR | p95 |
|---|---|---|---|---|---|---|---|
| Palabras | 31 % | 51 % | 59 % | 67 % | 0,445 | 47 % / 0,301 | 39 ms |
| Significado | 84 % | 96 % | 98 % | 100 % | 0,907 | 98 % / 0,852 | 933 ms (con la llamada a Google) |
| **Combinada (elegida)** | **84 %** | **96 %** | **98 %** | **100 %** | **0,907** | 94 % / 0,830 | 526 ms (el vector de la pregunta se reutiliza en la corrida) |

## 5. Lo que este ajuste NO demuestra (leer antes de fiarse de las cifras)

- **El óptimo está en el borde de la rejilla** (el peso más alto y la k más baja probados): significa que, en este golden set, lo mejor es
  acercarse a «solo significado». **No hay una ganancia medible de las palabras sobre el significado solo** (con la configuración elegida el orden por unidad es idéntico); su valor es la robustez
  (términos exactos, resaltado de las palabras coincidentes, y la búsqueda sigue funcionando sin proveedor). Se mantiene el brazo de palabras por eso, no por las cifras.
- El golden set lo redactó el asistente (preguntas completas, en lenguaje natural) y todas están en `draft`: puede **favorecer al significado**.
  Las preguntas reales del personal (con siglas, números de artículo, expresiones cortas) pueden dar otro equilibrio: hay que repetir este barrido cuando el revisor
  jurídico apruebe y aporte preguntas reales.
- A nivel de **disposición** la combinada queda algo por debajo del significado solo (94 % frente a 98 % en @10): el pasaje que se muestra como representante
  de una unidad no siempre es el exacto. Cada unidad lista hasta 5 pasajes coincidentes, y el lector abre la unidad completa.
- La reordenación por un modelo (*reranker*) **no se justifica**: el acierto@10 ya es 100 % y el cuello de botella no es el orden de los 10 primeros.
