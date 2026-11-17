# Frontend: estructura estándar de Angular

Angular 22 con componentes standalone, signals, detección de cambios sin zone.js (zoneless) y
OnPush por defecto. Estilos con Tailwind v4 y tokens propios. Pruebas con Vitest y Playwright.

## Estructura

```text
frontend/src/
├── main.ts               carga /config.json y arranca la app
├── styles.css            tokens de diseño (@theme) y estilos base
└── app/
    ├── app.ts · app.config.ts · app.routes.ts    rutas de features con carga diferida
    ├── core/             servicios únicos y transversales
    │   ├── api/          schema.d.ts (generado del OpenAPI) + models.ts (alias)
    │   ├── config/       configuración en tiempo de ejecución (RUNTIME_CONFIG)
    │   ├── http/         interceptores (base URL, X-Session-Id), problem details
    │   └── session/      identificador anónimo del navegador
    ├── layout/           marco de la aplicación (cabecera, navegación, avisos), 404
    ├── shared/ui/        componentes de diseño reutilizables (ValiditySeal, …)
    ├── features/
    │   ├── library/      Biblioteca normativa
    │   │   ├── data-access/   LibraryApi + LibraryStore (NgRx SignalStore)
    │   │   ├── feature/       LibraryPage (contenedor, provee el store)
    │   │   └── ui/            InstrumentCard (presentacional)
    │   ├── chat/         Consultas (spec 005; hoy marcador de posición)
    │   └── reader/       Folio: visor del PDF (spec 003)
    └── testing/          fixtures para tests
```

## Reglas

1. **Features autocontenidas:** una feature solo importa de `core`, `shared` y de sí misma. Así se
   puede trasladar al sistema DRTC existente (también Angular) si se decide integrarlo.
2. **Tres tipos de carpeta por feature:**
   - `data-access/`: comunicación con la API y estado (SignalStore). Sin plantillas.
   - `feature/`: componentes de página que conectan el store con la interfaz.
   - `ui/`: componentes presentacionales con `input()`/`output()`; sin servicios ni estado global.
3. **Estado:** signals locales en componentes; SignalStore por feature, provisto por la página.
4. **Contrato:** los tipos de la API se generan con `npm run api:types` (o `make openapi`); nunca se
   escriben a mano.
5. **Servicios únicos:** `@Service()` (Angular 22) con `inject()`.
6. **SSR-safe:** sin acceso directo a `window`/`localStorage` fuera de `isPlatformBrowser`.
7. **Accesibilidad:** WCAG 2.2 AA; `ng lint` incluye reglas de accesibilidad de plantillas y la
   suite e2e corre axe.
8. **Idioma y formato:** `LOCALE_ID = es-PE`; textos en español en las plantillas.
9. **Fuentes autoalojadas** (`@fontsource/*`): sin llamadas a Google Fonts.

## Configuración por entorno

`public/config.json` se lee al arrancar (`apiBaseUrl`). La misma build sirve para cualquier entorno:
en desarrollo el proxy de `ng serve` (`proxy.conf.json`) y en contenedores nginx redirigen `/api` al
backend, por lo que `apiBaseUrl` queda vacío (mismo origen).

## Pruebas

| Tipo | Herramienta | Ejemplo |
|---|---|---|
| Unitarias de componentes y stores | Vitest + TestBed | `validity-seal.spec.ts`, `library.store.spec.ts` |
| End-to-end + accesibilidad | Playwright + axe | `e2e/library.spec.ts` (API simulada; `E2E_REAL_API=1` para la real) |
