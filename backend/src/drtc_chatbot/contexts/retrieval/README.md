# Contexto `retrieval` — Recuperación (dominio principal)

**Responsabilidad:** encontrar la evidencia correcta para una consulta. Índice **derivado** del corpus
(se puede reconstruir en cualquier momento).

Conceptos previstos (spec 004): `Chunk` (artículo = padre, numeral/literal = hijo), búsqueda exacta por
identificador ("art. 5 de la Ley 27181"), búsqueda textual en español (`tsvector` + `unaccent`),
búsqueda vectorial (pgvector), fusión RRF (función pura del dominio) y expansión de contexto.
