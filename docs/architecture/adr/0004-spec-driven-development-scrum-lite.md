# 0004. Spec-Driven Development (Spec Kit) + Scrum-lite

- Estado: aceptada
- Fecha: 2026-11-17

## Contexto y problema

Se pidió desarrollo guiado por especificaciones y ágil (no cascada). En un dominio jurídico, la
ambigüedad cuesta caro, pero especificar todo por adelantado sería cascada.

## Decisión

- **GitHub Spec Kit** (instalado con la integración de Claude Code: comandos `/speckit-*`). Cada
  funcionalidad tiene `specs/NNN-slug/` con `spec.md` (qué/por qué), `plan.md`, `research.md`,
  `data-model.md`, `contracts/`, `tasks.md`. La constitución (`.specify/memory/constitution.md`) es
  la compuerta de calidad.
- **Agilidad:** specs justo a tiempo (un sprint adelante), historias priorizadas e independientes
  (P1 = corte demostrable), specs vivas que cambian con el código en el mismo PR.
- **Scrum-lite** para un equipo de 2-4: sprints de 2 semanas, planificación, demo con un usuario de la
  DRTC, retrospectiva; tablero en GitHub Projects; DoR/DoD explícitas.

## Consecuencias

- (+) Requisitos trazables a pruebas (`FR-xxx` ↔ `@pytest.mark.spec`).
- (+) Claude Code trabaja con contexto explícito en lugar de suposiciones.
- (−) La herramienta Spec Kit evoluciona rápido: actualizarla de forma controlada (`specify self check`).
