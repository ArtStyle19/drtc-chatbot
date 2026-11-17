# Implementation Plan: Catálogo de normas con sello de vigencia

**Branch**: `001-instrument-catalog` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

## Summary

Walking skeleton de punta a punta: la Biblioteca (Angular) consume `GET /api/v1/instruments`
(FastAPI), que ejecuta el caso de uso `ListLegalInstruments` sobre el puerto `LegalInstrumentCatalog`,
implementado por un adaptador que lee `corpus/manifest.yaml`. Incluye la estructura completa del
monorepo, la documentación, CI y las reglas de arquitectura verificadas.

## Technical Context

**Language/Version**: Python 3.14 (backend), TypeScript 6 / Angular 22 (frontend)
**Primary Dependencies**: FastAPI 0.163, Pydantic 2.14, SQLAlchemy 2.1, Alembic 1.20, structlog;
Angular 22, NgRx Signals 22, Tailwind 4, @lucide/angular
**Storage**: `corpus/manifest.yaml` para el catálogo; PostgreSQL 18 + pgvector preparado (migración de extensiones)
**Testing**: pytest (+ testcontainers, import-linter), Vitest, Playwright + axe
**Target Platform**: contenedores Linux; navegadores modernos de escritorio y móvil
**Project Type**: aplicación web (backend + frontend)
**Performance Goals**: listado < 200 ms en red local (3 normas, en memoria tras la primera lectura)
**Constraints**: sin login; sin datos personales; texto no verificado nunca presentado como vigente
**Scale/Scope**: 3 normas, 1 página funcional

## Constitution Check

| Principio | Cumplimiento |
|---|---|
| I. Fidelidad jurídica | `VerificationStatus.may_be_presented_as_current`; sello de vigencia; SHA-256 de fuentes; Manual del TUO marcado como explicativo |
| II. Spec antes que código | Esta spec + tests marcados `001-FR-*` |
| III. Clean Architecture/DDD | Contextos con capas; 6 contratos import-linter en verde |
| IV. Test-first | 61 tests de backend (≈ 90 % de cobertura; 2 requieren Docker), 15 unitarios de frontend, 4 e2e con axe |
| V. Cortes verticales | Un corte UI → API → dominio → adaptador; sin infraestructura especulativa |
| VI. Privacidad | Sin claves ni datos personales; sesión anónima por UUID |
| VII. UX accesible | axe sin violaciones serias; es-PE; estados de carga/vacío/error |
| VIII. Simplicidad | Cableado manual, manifiesto YAML en lugar de base de datos para el catálogo |

## Project Structure

```text
backend/src/drtc_chatbot/
├── contexts/legal_corpus/
│   ├── domain/{value_objects,legal_instrument}.py
│   ├── application/{ports,dto}.py · application/queries/list_legal_instruments.py
│   ├── infrastructure/{manifest_schema,manifest_catalog}.py
│   └── presentation/http/{router,schemas,dependencies}.py · api.py
├── contexts/identity/infrastructure/anonymous_identity_provider.py
├── shared_kernel/ · bootstrap/ · entrypoints/http/
frontend/src/app/
├── core/{api,config,http,session}/ · layout/{app-shell,not-found}/
├── shared/ui/validity-seal/
└── features/{library/{data-access,feature,ui},chat/feature}/
```

**Structure Decision**: monolito modular (ADR-0002) y Angular por features (ADR-0008).

## Complexity Tracking

Sin violaciones de la constitución.
