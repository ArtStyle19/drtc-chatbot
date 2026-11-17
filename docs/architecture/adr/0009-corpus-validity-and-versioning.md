# 0009. Modelo de vigencia y versiones del corpus

- Estado: aceptada
- Fecha: 2026-11-17

## Contexto y problema

Los tres PDF iniciales están desactualizados en distinto grado (ver
[inventario](../../domain/corpus-inventory.md)): uno habría sido sustituido por un TUO nuevo
(DS 006-2026-JUS). Un asistente jurídico que no distinga vigencia es peligroso.

## Decisión

- Separar documento fuente (PDF, SHA-256, inmutable), norma, versión y disposición.
- Estado explícito por versión: `verified_current`, `unverified`, `pending_review`, `superseded`,
  `repealed`, `unknown`. Solo `verified_current` puede presentarse como vigente
  (`may_be_presented_as_current`).
- Las versiones nuevas se agregan; nunca se reemplazan archivos ni se sobrescriben textos.
- `corpus/manifest.yaml` es la fuente de verdad del catálogo hasta la spec 002 (luego, PostgreSQL),
  con prueba automática de integridad SHA-256.
- La interfaz muestra siempre el **sello de vigencia** y un aviso global mientras haya ediciones no
  verificadas.

## Consecuencias

- (+) El sistema puede usarse para pruebas sin riesgo de presentar textos desactualizados como ley.
- (+) Prepara la carga de los textos oficiales vigentes (SPIKE-01) sin perder trazabilidad.
- (−) Verificar exige trabajo jurídico humano y registrar quién, cuándo y contra qué fuente.
