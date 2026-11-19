# Estrategia de pruebas

## Pirámide

| Nivel | Qué prueba | Herramienta | Carpeta |
|---|---|---|---|
| Unitarias de dominio | Invariantes y reglas (vigencia, rangos de páginas, citas) | pytest | `backend/tests/unit/` |
| Casos de uso | Orquestación con puertos falsos en memoria | pytest | `backend/tests/unit/` |
| Integración | Adaptadores reales: manifiesto YAML, PostgreSQL + pgvector (testcontainers), migraciones | pytest | `backend/tests/integration/` |
| API (e2e del backend) | HTTP de punta a punta, errores RFC 9457, `request_id` | pytest + httpx | `backend/tests/e2e/` |
| Contrato | `openapi.json` al día; tipos del frontend generados del contrato | pytest + CI | `backend/tests/e2e/test_openapi_contract.py` |
| Arquitectura | Reglas de dependencia y estructura de los contextos | import-linter + pytest | `backend/tests/architecture/` |
| Frontend unitarias | Componentes, stores, utilidades | Vitest | `frontend/src/**/*.spec.ts` |
| Frontend e2e + a11y | Flujos de usuario y axe (WCAG 2.2 AA), con API simulada (respuestas capturadas de la real) o `E2E_REAL_API=1` | Playwright | `frontend/e2e/` |
| Verificación contra el corpus real | Alineación del resaltado (tinta del canvas bajo cada caja) y bytes realmente descargados del PDF (CDP) | Playwright con la API real | `frontend/e2e/reader.spec.ts` (bloque «Contra el backend real») |
| Evaluación jurídica | Recall@K, MRR, precisión y cobertura de citas, abstención, fidelidad | arnés propio (spec 004) | `evaluation/` |

## Reglas

- **Trazabilidad:** cada test de aceptación lleva `@pytest.mark.spec("NNN-FR-xxx")`.
- **Sin red ni claves reales** en la suite normal: los proveedores de IA se sustituyen por fakes.
  Las evaluaciones que llaman a OpenAI se ejecutan aparte (cuestan dinero) y con aprobación.
- **Docker opcional en local:** los tests marcados `docker` se omiten si Docker no está disponible;
  en CI siempre corren.
- **Cobertura mínima** del backend: 80 % (`fail_under`).
- **Datos de prueba** sin datos personales reales.

## Evaluación (desde la spec 004)

El golden set (`evaluation/datasets/`) tiene preguntas con disposición, página y texto de respaldo
esperados, y un `review_status`. Ningún cambio en recuperación o generación se integra si empeora las
métricas sin una decisión registrada. Las preguntas `draft` no cuentan para el criterio de lanzamiento
hasta que un abogado las apruebe.

### La compuerta determinista (spec 004)

Una prueba marcada `docker` (`tests/e2e/test_retrieval_baseline.py`, corre en CI sin red) ingesta las tres
normas, prepara el índice **sin vectores**, evalúa los brazos exacto y de palabras con el golden set y los
compara con `evaluation/baseline.json` (tolerancia 0,02 por métrica). Verifica además que sin proveedor
de significado la búsqueda sigue respondiendo con palabras (SC-006/007) y que preparar el índice dos veces
no cambia nada. `make eval` ejecuta la misma compuerta a mano. Las métricas de significado y de la búsqueda
combinada necesitan la clave: se corren a mano (`drtc-retrieval eval --modes vector,hybrid`, con estimación y
confirmación de costo) y su informe se guarda en `evaluation/reports/`.

Otras garantías que prueba la suite: el golden set es coherente con el corpus ingerido (la ruta existe, sus
páginas incluyen las citadas y su texto contiene el texto de respaldo); el texto de una búsqueda no aparece en
ningún registro ni respuesta de error; el adaptador de OpenAI nunca deja la clave ni el texto en un mensaje de error
(transporte simulado).
