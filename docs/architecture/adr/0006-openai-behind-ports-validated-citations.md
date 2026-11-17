# 0006. OpenAI detrás de puertos; citas validadas por el backend

- Estado: aceptada
- Fecha: 2026-11-17

## Contexto y problema

Se eligió OpenAI como primer proveedor de IA para generación y embeddings. Las citas deben ser
exactas: un número de artículo inventado es un riesgo jurídico.

## Decisión

- El dominio define puertos (`QueryAnalyzer`, `AnswerGenerator`, `EmbeddingProvider`); los adaptadores
  OpenAI viven en `infrastructure/`. Los IDs de modelo vienen de la configuración
  (`DRTC_OPENAI_*`) y se fijan al iniciar la spec 005, tras revisar la lista vigente de modelos y la
  versión del SDK (`openai` 3.x).
- La respuesta se pide como **salida estructurada (JSON Schema)**; cada afirmación referencia IDs de
  evidencia que **genera el backend**. El `CitationValidator` del dominio verifica cada cita; lo que no
  se valida no se muestra; sin respaldo, el sistema se abstiene.
- Se envían solo los pasajes necesarios, nunca PDF completos.

## Consecuencias

- (+) Cambiar de proveedor (u operar dos para comparar) es agregar un adaptador.
- (+) La exactitud de las citas no depende de la "buena conducta" del modelo.
- (−) Costo por consulta y dependencia de un servicio externo: se registran tokens, costo y latencia,
  con timeouts y reintentos acotados.
