# CLAUDE.md — Asistente normativo DRTC Puno

Guía para Claude Code en este repositorio. Léela antes de cambiar código.

## Qué es

Chatbot con citas verificables sobre tres normas de transporte (Ley 27181, RENAT DS 017-2009-MTC,
TUO Ley 27444) para el personal de la DRTC Puno; ciudadanía más adelante. Arquitectura de referencia:
`docs/architecture/reference/arquitectura_rag_consultoria_legal_peru.md` (desviaciones en ADR-0010).

## Reglas de idioma

- Interfaz, documentación y specs: **español**. Código, identificadores, comentarios y commits: **inglés**.
- Términos del dominio: usar el glosario `docs/domain/ubiquitous-language.md` (p. ej. Disposición =
  `Provision`, Norma = `LegalInstrument`, Vigencia = validity).

## Flujo de trabajo (Spec-Driven Development)

1. Todo cambio de comportamiento parte de una spec en `specs/NNN-slug/` (comandos `/speckit-*`).
2. Respeta la constitución `.specify/memory/constitution.md` (principio I: fidelidad jurídica).
3. Implementa historia por historia (P1 primero), con tests de aceptación marcados
   `@pytest.mark.spec("NNN-FR-xxx")`.
4. Actualiza la spec, la documentación y, si hay decisión de arquitectura, un ADR.

## Comandos

```bash
make check          # lint + mypy + import-linter + pytest + eslint + vitest + build
make e2e            # Playwright + axe (API simulada)
make arch           # solo contratos de arquitectura
make test-db        # PostgreSQL temporal para las pruebas (luego export DRTC_TEST_DATABASE_URL=… que imprime)
make ingest         # manifiesto -> BD + ingesta de los tres PDF (cd backend && uv run drtc-ingest --help)
make index          # prepara el índice de búsqueda (palabras); se puede repetir
make embed          # vectores de significado: muestra el costo y pide confirmación antes de gastar
make search Q="…"   # busca el contenido como la aplicación (referencia + palabras + significado)
make eval           # compuerta de evaluación (exacta + palabras vs evaluation/baseline.json; sin red ni costo)
make openapi        # exporta backend/openapi.json y regenera frontend/src/app/core/api/schema.d.ts
cd backend && uv run pytest -q -m "not docker"   # tests rápidos sin Docker
```

Node se gestiona con nvm (`.nvmrc` = 26): en shells nuevos ejecuta `nvm use` antes de `npm`/`npx`.

## Backend (Clean Architecture + DDD)

- `src/drtc_chatbot/contexts/<ctx>/{domain,application,infrastructure,presentation}` + `api.py`.
- `domain`: Python puro (nada de fastapi, sqlalchemy, pydantic, yaml, httpx, openai).
- `application`: casos de uso que reciben un `Actor` y dependen de **puertos** (Protocol).
- `infrastructure`: adaptadores que implementan puertos. ORM ≠ entidades (mapeo explícito).
- `presentation`: routers FastAPI/CLI; obtienen casos de uso de `app.state` vía Protocol.
- `bootstrap/container.py`: único lugar donde se instancian adaptadores concretos.
- Un contexto solo importa `contexts.<otro>.api`. `make arch` lo verifica.
- Errores: excepciones de dominio con `code` estable → RFC 9457 en `entrypoints/http/errors.py`.

## Frontend (Angular 22)

- Sigue además `frontend/CLAUDE.md` (buenas prácticas oficiales de Angular: signals, `@Service()`,
  control flow nativo, OnPush por defecto, sin `standalone: true` explícito).
- `features/<f>/{data-access (SignalStore + API), feature (páginas), ui (presentacionales)}`.
- Tipos de API solo desde `core/api/models.ts` (generados del OpenAPI; nunca edites `schema.d.ts`).
- Tokens de diseño en `src/styles.css`; dirección visual en `.interface-design/system.md`.
- Código SSR-safe (sin acceso directo a `window`), WCAG 2.2 AA.

## Reglas jurídicas (no negociables)

- Nunca presentes un texto no verificado como vigente (`may_be_presented_as_current`).
- Nunca generes citas, artículos, páginas o URLs desde el modelo de IA: el backend crea los IDs de
  evidencia y valida cada cita.
- No modifiques `corpus/sources/*.pdf`; una edición nueva es un documento fuente nuevo en
  `corpus/manifest.yaml`.
- El material explicativo (Manual del TUO, pp. 23-68) no es norma.

## No hagas

- No hagas commits ni push sin que el usuario lo pida.
- No agregues infraestructura (Redis, colas, OCR, reranker) sin una spec que la justifique.
- No pongas claves de API ni datos personales en código, tests, logs o fixtures.
- No envíes nada a un proveedor externo (OpenAI o Gemini: `embed`, `eval --modes vector,hybrid`) sin mostrar antes la estimación y el aviso de datos, y que la persona usuaria confirme; el texto de una búsqueda nunca se registra.
- Cambiar `evaluation/baseline.json` exige `--reason` y una entrada en `evaluation/CHANGELOG.md`: ninguna mejora de la búsqueda se funde si empeora el golden set.
