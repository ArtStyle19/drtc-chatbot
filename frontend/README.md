# Frontend — Asistente normativo DRTC Puno

Angular 22 (standalone, signals, zoneless), Tailwind v4, NgRx SignalStore. Arquitectura y reglas:
[docs/architecture/frontend.md](../docs/architecture/frontend.md). Dirección de diseño:
[docs/ux/design-direction.md](../docs/ux/design-direction.md).

```bash
nvm use                 # Node 26 (.nvmrc en la raíz del repo)
npm ci
npm start               # http://localhost:4200, proxy de /api a http://localhost:8000
npm run test:ci         # Vitest
npm run lint            # ESLint (incluye accesibilidad de plantillas)
npm run e2e             # Playwright + axe (API simulada; E2E_REAL_API=1 para la real)
npm run api:types       # regenera src/app/core/api/schema.d.ts desde ../backend/openapi.json
npm run build           # build de producción en dist/
```

Reglas de Angular para Claude Code: [CLAUDE.md](CLAUDE.md).
