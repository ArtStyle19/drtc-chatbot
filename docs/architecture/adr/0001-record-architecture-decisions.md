# 0001. Registrar las decisiones de arquitectura con ADR

- Estado: aceptada
- Fecha: 2026-11-17

## Contexto y problema

El equipo (2-4 personas) cambiará con el tiempo y el sistema puede integrarse luego con otras
aplicaciones de la DRTC. Las razones de las decisiones se pierden si solo viven en conversaciones.

## Decisión

Registrar cada decisión significativa o difícil de revertir como ADR en `docs/architecture/adr/`,
con formato MADR y en español. Un ADR aceptado no se reescribe: se sustituye con uno nuevo.

## Consecuencias

- (+) Historia de decisiones consultable por nuevos integrantes y por Claude Code.
- (+) Las specs pueden referenciar ADR en lugar de repetir justificaciones.
- (−) Requiere disciplina: la Definition of Done exige un ADR cuando se toma una decisión de arquitectura.
