# Registro de cambios de la línea base de evaluación

Cada vez que cambia `baseline.json` se agrega aquí una entrada con la fecha, el motivo y las cifras
nuevas (lo hace `drtc-retrieval eval --write-baseline --reason "…"`). La compuerta de CI compara contra
esa línea base: empeorar más que la tolerancia falla; cambiar la línea base exige dejar esta constancia.

## 2026-11-19

Línea base inicial del brazo exacto (referencia explícita) sobre golden-v1, medida antes de que existiera cualquier búsqueda por contenido. Solo entiende referencias: 6 de 6 preguntas con referencia explícita quedan en 1.er lugar y ninguna pregunta sin respuesta devuelve resultados.

- **exact**: unidad acierto@10 12 %, MRR 0.118
