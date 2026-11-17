# Cómo contribuir

Trabajamos con **Spec-Driven Development + Scrum-lite** (sprints de 2 semanas). El detalle está en
[docs/process/way-of-working.md](docs/process/way-of-working.md); esto es el resumen operativo.

## 1. Antes de programar: la spec

1. La historia está en el tablero y cumple la **Definition of Ready**
   ([docs/process/definition-of-ready-done.md](docs/process/definition-of-ready-done.md)).
2. Su spec existe o se crea con Spec Kit desde Claude Code:
   - `/speckit-specify <descripción>` → `specs/NNN-slug/spec.md` (qué y por qué)
   - `/speckit-clarify` → resuelve ambigüedades (`[NEEDS CLARIFICATION]`)
   - `/speckit-plan` → `plan.md`, `research.md`, `data-model.md`, `contracts/`
   - `/speckit-tasks` → `tasks.md`; `/speckit-analyze` → consistencia
3. La spec se revisa en el PR igual que el código. Si el comportamiento cambia, la spec cambia en el
   mismo PR.

## 2. Ramas y commits

- Rama corta desde `main`: `NNN-slug` (p. ej. `002-corpus-ingestion`) o `fix/<tema>`.
- [Conventional Commits](https://www.conventionalcommits.org/) **en inglés**:
  `feat(legal-corpus): add provision versioning`, `fix(frontend): ...`, `docs(adr): ...`.
- PR pequeño, con la plantilla completa y **1 aprobación** como mínimo. Integración por squash.
- El hook `no-commit-to-branch` impide commits directos a `main`. Solo para el commit inicial del
  repositorio: `SKIP=no-commit-to-branch git commit -m "chore: bootstrap project"`.

## 3. Dónde va cada cosa (backend)

| Si escribes… | va en… |
|---|---|
| Una regla de negocio o invariante | `contexts/<ctx>/domain/` (Python puro) |
| Un caso de uso / puerto | `contexts/<ctx>/application/` |
| SQL, archivos, OpenAI, PyMuPDF | `contexts/<ctx>/infrastructure/` (implementa un puerto) |
| Un endpoint o comando CLI | `contexts/<ctx>/presentation/` |
| El cableado de dependencias | `bootstrap/container.py` (único lugar) |
| Algo que otro contexto necesita | `contexts/<ctx>/api.py` (fachada pública) |

`make arch` falla si una importación viola estas reglas. Más en
[docs/architecture/backend.md](docs/architecture/backend.md).

## 4. Dónde va cada cosa (frontend)

`features/<feature>/{data-access, feature, ui}`; componentes reutilizables en `shared/ui`;
servicios únicos en `core`. Más en [docs/architecture/frontend.md](docs/architecture/frontend.md).

## 5. Tests y calidad

- Backend: `@pytest.mark.spec("NNN-FR-xxx")` en los tests de aceptación.
- Frontend: Vitest para componentes y stores; Playwright + axe para flujos.
- Antes del PR: `make check` (y `make e2e` si tocaste la interfaz).
- Si cambias la API: `make openapi` y commitea `backend/openapi.json` y los tipos generados.

## 6. Reglas jurídicas que nunca se rompen

Lee la [constitución](.specify/memory/constitution.md), principio I. En particular: nada no
verificado se presenta como vigente, ninguna cita sale de la memoria del modelo, y los PDF de
`corpus/sources/` jamás se modifican.

## 7. Decisiones de arquitectura

Toda decisión difícil de revertir se registra como ADR en `docs/architecture/adr/` (formato MADR).
