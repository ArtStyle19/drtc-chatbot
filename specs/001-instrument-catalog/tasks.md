# Tasks: Catálogo de normas con sello de vigencia

**Input**: [spec.md](spec.md), [plan.md](plan.md) · `[P]` = paralelizable · todas completadas en el Sprint 0.

## Phase 1: Setup

- [x] T001 Instalar toolchain: uv, Python 3.14 (uv), pre-commit, Node 26 (nvm); `git init`
- [x] T002 Mover los PDF a `corpus/sources/` (nombres slug, bytes idénticos) y el documento de arquitectura a `docs/architecture/reference/`
- [x] T003 Inicializar Spec Kit con la integración de Claude Code y escribir la constitución
- [x] T004 [P] Inicializar backend con uv (`backend/pyproject.toml`) y dependencias
- [x] T005 [P] Generar el workspace Angular 22 (`frontend/`) con Tailwind, Vitest, zoneless y angular-eslint

## Phase 2: Foundational

- [x] T006 Shared kernel: `Entity`, `AggregateRoot`, `DomainEvent`, `DomainError`, `Actor`, puertos (`backend/src/drtc_chatbot/shared_kernel/`)
- [x] T007 Esqueleto de contextos con capas y `api.py` (`backend/src/drtc_chatbot/contexts/*`)
- [x] T008 Contratos import-linter (`backend/pyproject.toml`) y test de arquitectura (`backend/tests/architecture/`)
- [x] T009 HTTP: `create_app`, `RequestIdMiddleware`, errores RFC 9457, health (`backend/src/drtc_chatbot/entrypoints/http/`)
- [x] T010 Alembic async + migración de extensiones `vector`, `unaccent`, `pg_trgm`
- [x] T011 [P] Frontend core: runtime config, interceptores, problem details, sesión anónima, locale es-PE

## Phase 3: User Story 1 — Ver normas y su vigencia (P1) 🎯 MVP

- [x] T012 [US1] Objetos de valor y agregado `LegalInstrument` con reglas de vigencia y roles de página
- [x] T013 [US1] Puerto `LegalInstrumentCatalog`, DTO y caso de uso `ListLegalInstruments`
- [x] T014 [US1] Adaptador `ManifestInstrumentCatalog` + esquema Pydantic del manifiesto
- [x] T015 [US1] `corpus/manifest.yaml` con las 3 normas (páginas, ediciones, advertencias)
- [x] T016 [US1] Router `GET /api/v1/instruments` + esquemas de respuesta; export `backend/openapi.json`
- [x] T017 [P] [US1] Tokens de diseño, app shell, `ValiditySeal`, `InstrumentCard`, `LibraryStore`, `LibraryPage`
- [x] T018 [US1] Tests: dominio, caso de uso con fake, manifiesto real, API e2e, componentes, store, Playwright + axe

## Phase 4: User Story 2 — Integridad de documentos fuente (P2)

- [x] T019 [US2] Tests de integridad SHA-256 y de archivos no registrados (`backend/tests/integration/corpus/`)

## Phase 5: User Story 3 — Esqueleto verificable (P3)

- [x] T020 [US3] Tests de health, errores y `request_id` (`backend/tests/e2e/test_platform_api.py`)
- [x] T021 [US3] Test de migraciones contra PostgreSQL + pgvector (testcontainers, marcado `docker`)
- [x] T022 [US3] Test de contrato OpenAPI al día (`backend/tests/e2e/test_openapi_contract.py`)

## Phase 6: Polish & Cross-Cutting

- [x] T023 Dockerfiles (no-root), `compose.yaml`, nginx con proxy `/api` y soporte SSE
- [x] T024 Makefile, `.env.example`, pre-commit (ruff, prettier, gitleaks, import-linter), CI de GitHub Actions
- [x] T025 Documentación: README, CONTRIBUTING, CLAUDE.md, docs/ (producto, dominio, arquitectura, ADR 0001-0010, proceso, UX, operación)
- [x] T026 Borrador de la spec 002 para la planificación del Sprint 1
