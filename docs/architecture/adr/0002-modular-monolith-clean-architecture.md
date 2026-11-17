# 0002. Monolito modular con bounded contexts y Clean Architecture

- Estado: aceptada
- Fecha: 2026-11-17

## Contexto y problema

Se pidió un backend escalable, mantenible y comprensible con Clean Architecture, SOLID y DDD. El
corpus es pequeño (tres normas) y el equipo también; los microservicios agregarían costo operativo sin
beneficio.

## Opciones consideradas

1. Arquitectura en capas "por tipo" (`models/`, `services/`, `api/`), como el sistema DRTC actual.
2. Microservicios por función (ingesta, búsqueda, chat).
3. **Monolito modular**: bounded contexts con capas internas de Clean Architecture.

## Decisión

Opción 3. Contextos `legal_corpus`, `ingestion`, `retrieval`, `consultation`, `identity` y un
`shared_kernel` mínimo. Dentro de cada uno: `domain → application → infrastructure | presentation`,
más una fachada `api.py` como única puerta para otros contextos. Raíz de composición manual en
`bootstrap/container.py` (sin framework de inyección hasta que el cableado lo justifique; candidato:
dishka). Reglas verificadas con **import-linter** en tests y CI.

## Consecuencias

- (+) El dominio se prueba sin base de datos, HTTP ni IA; los proveedores son intercambiables.
- (+) Los límites permiten separar un contexto en un servicio o worker después, si hace falta.
- (+) Las reglas no dependen de la memoria del equipo: romperlas rompe la build.
- (−) Más archivos y mapeos explícitos (ORM ↔ dominio, DTO ↔ esquemas HTTP) que un CRUD directo.
