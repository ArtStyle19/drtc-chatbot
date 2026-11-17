# Contexto `ingestion` — Ingesta documental (subdominio de soporte)

**Responsabilidad:** convertir un PDF fuente en disposiciones estructuradas y revisables
(artículo → numeral → literal) con su página exacta, sin modificar nunca el original.

Conceptos previstos (spec 002): `IngestionJob` (máquina de estados: recibido → extraído → analizado →
en revisión → aprobado → publicado / fallido), estrategias de análisis por norma (Ley 27181, RENAT,
TUO), detección de notas de modificación `(*)` y textos sustituidos, y un reporte de revisión.

Publica sus resultados en `legal_corpus` únicamente a través de `contexts.legal_corpus.api`.
