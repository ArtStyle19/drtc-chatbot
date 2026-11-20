# Registro de cambios de la línea base de evaluación

Cada vez que cambia `baseline.json` se agrega aquí una entrada con la fecha, el motivo y las cifras
nuevas (lo hace `drtc-retrieval eval --write-baseline --reason "…"`). La compuerta de CI compara contra
esa línea base: empeorar más que la tolerancia falla; cambiar la línea base exige dejar esta constancia.

## 2026-11-19

Línea base inicial del brazo exacto (referencia explícita) sobre golden-v1, medida antes de que existiera cualquier búsqueda por contenido. Solo entiende referencias: 6 de 6 preguntas con referencia explícita quedan en 1.er lugar y ninguna pregunta sin respuesta devuelve resultados.

- **exact**: unidad acierto@10 12 %, MRR 0.118

## 2026-11-19

Brazo de palabras ajustado con el golden set (T024): normalización de ts_rank_cd = 2 (longitud del pasaje) y pesos (0,1; 0,2; 0,4; 0,4). Subió el acierto@10 por unidad de 55 % a 67 % y el MRR de 0,226 a 0,445. El detalle de la cuadrícula está en evaluation/reports/2026-11-19-lexical-tuning.md. Se vuelve a fijar el brazo exacto sin cambios.

- **exact**: unidad acierto@10 12 %, MRR 0.118
- **lexical**: unidad acierto@10 67 %, MRR 0.445

## 2026-11-19

Medición del brazo de significado y de la combinada con `gemini-embedding-2` (corpus completo vectorizado). **`baseline.json` no cambia**: la compuerta determinista sigue siendo exacta + palabras, porque significado y combinada necesitan una clave y cuestan dinero. Lo que sí cambia es el ajuste de fusión por defecto (`DRTC_SEARCH_RRF_K` 60 → 5 y nuevo `DRTC_SEARCH_VECTOR_WEIGHT` = 6): con pesos iguales la combinada (acierto@10 98 %, MRR 0,792) quedaba por debajo del significado solo (100 %, 0,907) y SC-004 fallaba; con el ajuste la combinada iguala al significado (100 %, 0,907). Detalle en `evaluation/reports/2026-11-19-fusion-tuning.md` y en `…-lexical+vector+hybrid.md`; el informe con pesos iguales se conserva como `…-equal-weights`.

- **lexical**: unidad acierto@10 67 %, MRR 0.445 (sin cambios)
- **vector** (`gemini-embedding-2`): unidad acierto@10 100 %, MRR 0.907
- **hybrid** (k = 5, significado × 6): unidad acierto@10 100 %, MRR 0.907
