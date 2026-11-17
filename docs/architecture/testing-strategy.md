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
| Frontend e2e + a11y | Flujos de usuario y axe (WCAG 2.2 AA) | Playwright | `frontend/e2e/` |
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
