# 0008. Frontend Angular 22 con features autocontenidas

- Estado: aceptada
- Fecha: 2026-11-17

## Contexto y problema

Se pidió Angular con la estructura estándar y una UX/UI premium. El sistema DRTC existente usa
Angular 21 + Tailwind v4, y el chat podría migrarse a esa aplicación.

## Decisión

- Angular 22 (estable actual): componentes standalone, signals, zoneless, OnPush por defecto,
  `@Service()`, Vitest; TypeScript estricto.
- Estructura `core / layout / shared / features`, con `data-access / feature / ui` dentro de cada
  feature; estado con NgRx SignalStore; rutas con carga diferida.
- Tailwind v4 con tokens propios basados en la marca DRTC; Angular CDK para accesibilidad e
  interacción; iconos `@lucide/angular`; fuentes autoalojadas; pdf.js para el visor (spec 003).
- Tipos de la API generados del OpenAPI (`openapi-typescript`).
- Código SSR-safe y features sin dependencias cruzadas para poder trasladarlas.

## Consecuencias

- (+) Mismo stack que el sistema DRTC: integración y mantenimiento compartidos.
- (+) Contrato tipado de punta a punta.
- (−) Angular 22 requiere Node ≥ 22.22.3/24.15/26 (`.nvmrc` = 26), distinto del Node del sistema
  DRTC; al integrarse habrá que actualizarlo a Angular 22 o publicar la feature como Angular Element.
