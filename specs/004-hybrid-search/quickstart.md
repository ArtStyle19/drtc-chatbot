# Guía de validación (quickstart) — spec 004

Cómo comprobar, de punta a punta, que la búsqueda por contenido funciona. Los detalles de datos están en [data-model.md](data-model.md) y los contratos en [contracts/](contracts/README.md).

## Requisitos

- PostgreSQL con pgvector: `make test-db` (puerto 55432) y `export DRTC_TEST_DATABASE_URL=postgresql+psycopg://drtc:drtc@127.0.0.1:55432/drtc_chatbot_test`.
- Base de desarrollo con las tres normas: crear `drtc_chatbot_dev`, `alembic upgrade head` y `drtc-ingest run --all` con `DRTC_DATABASE_URL` apuntando a ella.
- Para el significado: `DRTC_OPENAI_API_KEY` en `.env` (nunca en la línea de comandos ni en el repositorio).

## 1. Evaluación primero (sin red)

```bash
cd backend
uv run pytest tests/integration/corpus/test_golden_set.py -q      # integridad del golden set (ruta, páginas, texto)
uv run drtc-retrieval eval --modes exact --check-baseline         # línea base de la búsqueda exacta
```

Esperado: el golden set tiene ≥ 50 preguntas (≥ 8 sin respuesta) y todas pasan; la exacta ubica en 1.er lugar toda pregunta con referencia explícita (SC-001, SC-002).

## 2. Índice y búsqueda por palabras (sin red)

```bash
uv run drtc-retrieval index            # primera vez: agrega ~2.600 pasajes
uv run drtc-retrieval index            # segunda vez: 0 agregados, 0 cambiados, 0 borrados
uv run drtc-retrieval search "plazo para interponer recurso administrativo" --mode lexical
uv run drtc-retrieval eval --modes exact,lexical --check-baseline
```

Esperado: el numeral 218.2 del TUO aparece entre los primeros resultados; la segunda corrida de `index` no cambia nada; la evaluación pasa la línea base.

## 3. Significado (con clave; **cuesta céntimos, pide confirmación**)

```bash
uv run drtc-retrieval embed --dry-run                  # estima ventanas, tokens y costo; no llama a OpenAI
uv run drtc-retrieval embed --yes                      # pide los vectores; imprime el uso real
uv run drtc-retrieval eval --modes lexical,vector,hybrid --k 1,3,5,10 --out ../evaluation/reports/
```

Esperado: informe comparando palabras, significado y combinada; la combinada ≥ la mejor de las otras en Recall@10 (SC-004); costo total < 0,50 USD (SC-010). Repetir con el segundo modelo para compararlos.

## 4. Degradación (SC-006)

Quitar `DRTC_OPENAI_API_KEY` y buscar: la API responde 200 con resultados por palabras y `degraded: ["vector_unavailable"]`; la pantalla muestra el aviso.

## 5. API y pantalla

```bash
cd backend && uv run uvicorn drtc_chatbot.main:app --port 8000
cd frontend && npx ng serve                                  # http://localhost:4200
```

- `GET /api/v1/search?q=mototaxi` devuelve resultados con cita, página, `snippet` por segmentos y `verification_status`.
- En el buscador del encabezado: `art. 5 Ley 27181` → abre el lector (como antes); `plazo para apelar` + Enter → `/buscar?q=plazo%20para%20apelar` con resultados, filtro por norma y el aviso "coincidencias, no una respuesta".
- `?debug=true` solo muestra diagnóstico en entornos `local`/`test`.

## 6. Verificación automática

```bash
make check      # lint, tipos, 6 contratos de import-linter, pruebas (incluye la compuerta exacta + palabras), frontend, build
make e2e        # Playwright con API simulada + axe (WCAG 2.2 AA)
E2E_REAL_API=1 npx playwright test e2e/search.spec.ts   # con el backend real
```

Esperado: todo en verde; la compuerta falla si se degrada deliberadamente la búsqueda por palabras (SC-007, comprobar una vez a mano).
