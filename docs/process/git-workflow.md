# Flujo de git

## Ramas

- `main` siempre desplegable y protegida (PR obligatorio, CI en verde, 1 aprobación).
- Ramas cortas (≤ 3 días): `NNN-slug` para una spec (p. ej. `002-corpus-ingestion`), `fix/<tema>`,
  `docs/<tema>`, `chore/<tema>`.

## Commits (en inglés, Conventional Commits)

```text
<type>(<scope>): <summary>

feat(legal-corpus): add provision versions with page spans
fix(frontend): announce library load errors to screen readers
docs(adr): record pgvector dimension decision
test(retrieval): cover RRF tie-breaking
chore(deps): bump fastapi to 0.164
```

Tipos: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`, `ci`, `build`. Alcances habituales:
`legal-corpus`, `ingestion`, `retrieval`, `consultation`, `identity`, `frontend`, `corpus`, `specs`.

## Pull requests

- Pequeños y enfocados en una historia o parte de ella; plantilla completa.
- Integración por *squash*; el título del PR sigue Conventional Commits.
- Cambios del corpus (`corpus/`) o del golden set (`evaluation/`) requieren aprobación del revisor
  jurídico.

## Versiones

SemVer por release (`v0.1.0` = R0, `v0.2.0` = R1, …) con etiquetas anotadas y notas de versión
generadas desde los commits.

## Primer commit del repositorio

El hook `no-commit-to-branch` bloquea commits directos a `main`. Para el commit inicial:

```bash
git add -A
SKIP=no-commit-to-branch git commit -m "chore: bootstrap project (sprint 0)"
```
