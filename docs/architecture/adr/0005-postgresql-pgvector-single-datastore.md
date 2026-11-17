# 0005. PostgreSQL 18 + pgvector + búsqueda textual como único almacén

- Estado: aceptada
- Fecha: 2026-11-17

## Contexto y problema

El sistema necesita datos jurídicos relacionales (normas, versiones, disposiciones, eventos), búsqueda
textual en español y búsqueda semántica. Con tres normas, una base vectorial separada sería
complejidad sin beneficio.

## Decisión

PostgreSQL 18 con las extensiones `vector` (pgvector 0.8.7), `unaccent` y `pg_trgm`
(migración `0001`). Imagen de desarrollo: `pgvector/pgvector:0.8.7-pg18-trixie`. PostgreSQL es la
fuente de verdad jurídica; los índices (FTS, vectores) son derivados y reconstruibles. Acceso con
SQLAlchemy 2.1 asíncrono y psycopg 3; migraciones con Alembic.

## Consecuencias

- (+) Una sola base que respaldar y operar; transacciones sobre todo el modelo.
- (+) Coherente con el stack del sistema DRTC existente (PostgreSQL).
- (−) Búsqueda BM25 avanzada limitada; se evaluará OpenSearch solo con decenas de miles de documentos.
- (−) Los índices HNSW de `vector` admiten hasta 2000 dimensiones: el modelo de embeddings debe
  ajustarse (dimensiones reducidas o `halfvec`).
