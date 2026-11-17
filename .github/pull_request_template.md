## Qué cambia y por qué

<!-- Resumen breve. Enlace a la spec y a las historias/tareas afectadas. -->

- Spec: `specs/NNN-.../spec.md` · Historia: US-? · Tareas: T???
- Requisitos cubiertos: FR-???, SC-???

## Cómo se verificó

<!-- Tests nuevos o modificados, demo, capturas, comandos ejecutados. -->

## Definition of Done (docs/process/definition-of-ready-done.md)

- [ ] La spec se actualizó si cambió el comportamiento (spec y código en el mismo PR)
- [ ] Tests automatizados de los escenarios de aceptación (marcados con su requisito)
- [ ] `make check` en verde (lint, tipos, contratos de arquitectura, tests, build)
- [ ] `make e2e` en verde si cambió la interfaz (incluye accesibilidad axe)
- [ ] Contrato OpenAPI y tipos del frontend regenerados (`make openapi`) si cambió la API
- [ ] ADR nuevo o actualizado si se tomó una decisión de arquitectura
- [ ] Sin regresión en la evaluación (golden set) cuando aplica (desde spec 004)
- [ ] Principios jurídicos respetados: nada no verificado se presenta como vigente; ninguna cita sin validar
- [ ] Sin secretos, datos personales ni textos de expedientes en el código, los logs o los tests
