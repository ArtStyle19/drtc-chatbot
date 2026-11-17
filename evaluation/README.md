# Evaluación (golden set)

La calidad del asistente se mide con preguntas jurídicas revisadas, no con impresiones
(constitución, principio I.10). El arnés de métricas llega con la spec 004.

```text
evaluation/
└── datasets/
    ├── golden-questions.schema.json   esquema de cada pregunta
    └── golden-v0.jsonl                10 preguntas BORRADOR tomadas de los PDF iniciales
```

## Formato

Una pregunta por línea (JSONL). Campos principales:

- `question`, `intent` (`exact_provision`, `concept`, `requirements`, `exceptions`, `comparison`,
  `practical_case`, `out_of_scope`, `historical`), `audience`.
- `answerable`: si el corpus permite responderla; si es `false`, se espera abstención.
- `expected.citations[]`: `version_id`, disposición, páginas del PDF, texto exacto de respaldo y si la
  página es normativa o explicativa.
- `review_status`: `draft` → `reviewed` → `approved` (solo `approved` cuenta para el criterio de
  lanzamiento) y `reviewed_by`.

**Las expectativas están ligadas a una versión** (`version_id`). Cuando SPIKE-01 cargue los textos
vigentes (p. ej. el TUO del DS 006-2026-JUS, que puede renumerar artículos), cada pregunta debe
revisarse y apuntar a la versión nueva.

## Métricas previstas (specs 004-005)

Recall@K y MRR (recuperación) · precisión y cobertura de citas · fidelidad · calidad de abstención ·
precisión de vigencia. Objetivo: ampliar a 100 preguntas y luego a 200-300, con revisión de un abogado.

## Reglas

- Sin datos personales ni casos reales identificables.
- Toda pregunta nueva entra como `draft`; la aprueba el revisor jurídico en un PR.
- La suite del backend verifica que cada cita apunte a una versión y a páginas existentes del manifiesto,
  y que el texto de respaldo aparezca en esas páginas del PDF.
