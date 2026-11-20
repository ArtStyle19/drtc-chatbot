# Implementation Plan: Ingesta del corpus en disposiciones estructuradas

**Branch**: `002-corpus-ingestion` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

## Summary

Un analizador de texto **puro** convierte las páginas normativas de cada PDF en disposiciones
(artículo → numeral → literal) con ruta estructural estable, páginas exactas y cajas de texto. Las
sustituciones (`“…”` + notas `(*)`) se modelan como revisiones: el texto anterior queda `superseded`, el
nuevo es el vigente de la edición. Lo publica en PostgreSQL a través de la fachada de `legal_corpus`;
una versión solo es legible por la API cuando está aprobada (política `manual` | `auto_dev`, ADR-0011).

## Technical Context

**Language/Version**: Python 3.14 · **Dependencies**: pypdfium2 (ADR-0012), Typer, SQLAlchemy 2.1, Alembic
**Storage**: PostgreSQL 18 (migración `0002`) · **Testing**: pytest (unitarias, PDF reales, PostgreSQL, e2e)
**Project Type**: backend + CLI (`drtc-ingest`) + API de lectura
**Performance Goals**: las tres normas en < 2 min (medido: ≈ 5 s con base de datos)
**Constraints**: no se modifica nunca un PDF; lo que no se puede interpretar se reporta, no se adivina
**Scale/Scope**: 3 PDF, 509 páginas, ≈ 2 900 disposiciones vigentes

## Constitution Check

| Principio | Cumplimiento |
|---|---|
| I. Fidelidad jurídica | SHA-256 verificado antes de leer; revisiones inmutables; aprobar ≠ verificar; Manual del TUO excluido; párrafos sustituidos marcados como anomalía y no aplicados por conjetura |
| I.5 (revisión previa) | Excepción acotada `auto_dev` solo en `local`/`test` (ADR-0011, constitución 1.1.0) |
| III. Clean Architecture | Analizador en `ingestion/domain` sin dependencias; `ingestion` solo habla con `legal_corpus.api`; 6 contratos import-linter en verde |
| IV. Test-first | 130 tests de backend (95 % cobertura): invariantes, 3 PDF reales, golden set (SC-005), PostgreSQL |
| V. Cortes verticales | US1 (Ley 27181) de punta a punta antes que RENAT y TUO |
| VIII. Simplicidad | Eventos legales como JSON en cada revisión (sin tabla `legal_events`); CLI en lugar de cola de trabajos |

## Project Structure

```text
backend/src/drtc_chatbot/contexts/
├── ingestion/
│   ├── domain/{job,review_report}.py · domain/parsing/{model,engine,notes,profiles}.py
│   ├── application/{ports}.py · commands/{run_ingestion,preview_ingestion}.py
│   ├── infrastructure/{pdfium_extractor,corpus_gateway,sql_jobs,models}.py
│   └── presentation/cli/app.py       → entrypoints/cli/ingest.py (drtc-ingest)
└── legal_corpus/
    ├── domain/{provisions,approval}.py
    ├── application/commands/{sync_corpus_manifest,publish_provisions,approve_version}.py
    ├── application/queries/{list_provisions,get_provision}.py
    ├── infrastructure/{models,sql_store,manifest_reader}.py
    └── presentation/http/{router,schemas}.py
backend/migrations/versions/2026_11_18_0002_corpus_provisions_and_ingestion_jobs.py
```
