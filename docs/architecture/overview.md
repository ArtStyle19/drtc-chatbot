# Visión general de la arquitectura (C4)

Basada en la [arquitectura de referencia](reference/arquitectura_rag_consultoria_legal_peru.md):
**monolito modular**, PostgreSQL como fuente de verdad jurídica, búsqueda híbrida y validación de
citas. Las diferencias están en [ADR-0010](adr/0010-deviations-from-reference-architecture.md).

## Nivel 1 — Contexto

```mermaid
flowchart TB
  staff[Personal de la DRTC Puno<br/>OAJ, SDT, DCT, Mesa de Partes]
  citizen[Ciudadanía<br/>release R4]
  reviewer[Revisor jurídico]
  sys[Asistente normativo<br/>DRTC Puno]
  openai[(OpenAI API<br/>generación y embeddings)]
  drtc[(Sistema DRTC<br/>Habilitación Vehicular<br/>login, spec 007)]
  official[(SPIJ / El Peruano<br/>fuentes oficiales)]

  staff -->|consulta y lee normas| sys
  citizen -.->|R4| sys
  reviewer -->|verifica corpus y golden set| sys
  sys -->|pasajes de evidencia, nunca PDF completos| openai
  sys -.->|valida sesión| drtc
  reviewer -.->|obtiene textos vigentes| official
```

## Nivel 2 — Contenedores

```mermaid
flowchart LR
  browser[Navegador] --> web[Frontend<br/>Angular 22 + nginx]
  web -->|/api, HTTPS| api[Backend API<br/>FastAPI, monolito modular]
  api --> db[(PostgreSQL 18<br/>pgvector + FTS)]
  api --> files[(Corpus<br/>PDF inmutables)]
  api -.->|spec 005| llm[(OpenAI)]
  worker[Worker de ingesta<br/>spec 008] -.-> db
  worker -.-> files
```

- **Frontend:** SPA servida por nginx, que además hace de proxy de `/api` (mismo origen, SSE).
- **Backend:** API sin estado (escalable horizontalmente). La ingesta corre por CLI hasta la spec 008,
  donde se separa en un worker con el mismo código y otro punto de entrada.
- **PostgreSQL:** registro canónico del corpus, índice textual y vectorial (reconstruible).
- **Corpus:** PDF originales; en producción, almacenamiento compatible con S3 (MinIO, como el
  sistema DRTC) detrás del puerto `DocumentStorage`.

## Nivel 3 — Componentes del backend

```mermaid
flowchart TB
  subgraph entry[entrypoints/http]
    app[create_app · middleware · errores RFC 9457 · health]
  end
  subgraph boot[bootstrap]
    cont[container: cableado manual]
  end
  subgraph contexts[contexts]
    lc[legal_corpus]
    ing[ingestion]
    ret[retrieval]
    con[consultation]
    idn[identity]
  end
  sk[shared_kernel]
  app --> cont
  app --> lc
  cont --> lc & ing & ret & con & idn
  lc & ing & ret & con & idn --> sk
```

Cada contexto tiene `domain / application / infrastructure / presentation` y una fachada `api.py`.
Detalle en [backend.md](backend.md).

## Atributos de calidad y cómo se logran

| Atributo | Mecanismo |
|---|---|
| Mantenibilidad | Bounded contexts, regla de dependencias verificada (import-linter), ADR |
| Escalabilidad | API sin estado, índice derivado, worker separable, OpenSearch solo si llegan decenas de miles de documentos |
| Robustez | Tipado estricto (mypy, TS strict), validación de entrada, estados explícitos, health checks |
| Trazabilidad jurídica | SHA-256 de fuentes, versiones inmutables, citas validadas, `request_id` |
| Seguridad | Claves solo en el servidor, mínimos datos a terceros, contenedores no-root |
| Usabilidad | Sello de vigencia, citas verificables, WCAG 2.2 AA |
