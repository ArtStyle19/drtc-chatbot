# Definition of Ready y Definition of Done

## Definition of Ready (una historia puede entrar al sprint si…)

- [ ] Está en una spec (`specs/NNN-slug/spec.md`) con prioridad y "prueba independiente".
- [ ] Sus escenarios *Dado / Cuando / Entonces* son verificables.
- [ ] No quedan `[NEEDS CLARIFICATION]` que la afecten.
- [ ] Si toca conocimiento jurídico, el revisor jurídico aprobó la spec.
- [ ] Las dependencias (datos, accesos, decisiones) están disponibles o planificadas.
- [ ] Cabe en un sprint; si no, se divide en historias más pequeñas.

## Definition of Done (una historia está terminada si…)

- [ ] Los escenarios de aceptación están automatizados y marcados con su requisito
      (`@pytest.mark.spec("NNN-FR-xxx")` o en el nombre del test e2e).
- [ ] `make check` en verde: ruff, mypy, contratos de arquitectura, pytest (≥ 80 % de cobertura),
      eslint, prettier, Vitest y build.
- [ ] Si cambió la interfaz: `make e2e` en verde, sin violaciones serias de accesibilidad (axe), y
      revisada en escritorio y móvil.
- [ ] Si cambió la API: `make openapi` y contrato + tipos commiteados.
- [ ] La spec, la documentación y, si aplica, un ADR están actualizados en el mismo PR.
- [ ] Desde la spec 004: sin regresión en las métricas del golden set.
- [ ] Se cumplen los principios jurídicos de la constitución.
- [ ] PR revisado y aprobado por al menos otra persona; integrado en `main`.
- [ ] Demostrado en la sprint review.
