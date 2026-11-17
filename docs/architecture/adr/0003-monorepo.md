# 0003. Monorepo con backend, frontend, specs, docs, corpus y evaluación

- Estado: aceptada
- Fecha: 2026-11-17

## Contexto y problema

Una spec cambia a la vez el contrato de la API, el backend, el frontend y a veces el corpus o el
golden set. Separarlos en repositorios obligaría a coordinar versiones para cada historia.

## Decisión

Un solo repositorio:

```text
backend/  frontend/  specs/  docs/  corpus/  evaluation/  infra/  .specify/
```

Nombres de carpetas y archivos en inglés; contenido documental en español. El contrato
`backend/openapi.json` se versiona y CI verifica que el frontend use tipos generados de él.

## Consecuencias

- (+) Un PR por historia, con spec, código y pruebas juntos.
- (+) CI único que verifica la coherencia entre contrato, backend y frontend.
- (−) Los PDF del corpus viven en git (~16 MB hoy); si crece, se migrará a Git LFS o a almacenamiento S3.
