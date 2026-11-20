# Entorno local

## Requisitos

| Herramienta | Versión | Instalación |
|---|---|---|
| uv | ≥ 0.13 | `pip install uv` o el instalador oficial de astral.sh |
| Python | 3.14 | `uv python install 3.14` (uv lo gestiona; no requiere pyenv) |
| nvm + Node | Node 26 (`.nvmrc`) | `nvm install 26` (Angular 22 exige Node ≥ 22.22.3, 24.15 o 26) |
| Docker + Compose | Compose v2+ | — |
| make | — | — |

## Primer arranque

```bash
cp .env.example .env
nvm use                 # Node 26 en este repositorio
make bootstrap
make dev-db && make migrate
make dev-backend        # http://localhost:8000/api/docs
make dev-frontend       # http://localhost:4200
```

## Ingesta y pruebas con base de datos

```bash
make test-db          # PostgreSQL+pgvector temporal en :55432 (red de host; no necesita publicar puertos)
export DRTC_TEST_DATABASE_URL=postgresql+psycopg://drtc:drtc@127.0.0.1:55432/drtc_chatbot_test
make test-backend     # corre también las pruebas que necesitan PostgreSQL
make ingest           # (contra la base de desarrollo) carga el manifiesto e ingiere los tres PDF
```

Sin `DRTC_TEST_DATABASE_URL`, las pruebas usan testcontainers (necesitan que Docker publique puertos); si no
hay ninguna base disponible, esas pruebas se omiten en local y **fallan en CI**.

## Puertos

| Servicio | Puerto local | Variable |
|---|---|---|
| PostgreSQL (compose) | 5433 | `DRTC_DB_HOST_PORT` (5432 suele estar ocupado) |
| API | 8000 | `DRTC_API_HOST_PORT` |
| Frontend (contenedor) | 8080 | `DRTC_WEB_HOST_PORT` |
| Frontend (`ng serve`) | 4200 | — |

## Problemas conocidos

**Docker no publica puertos o los contenedores no tienen red** (ocurrió el 17-11-2026 y se resolvió reiniciando Docker) (errores como
`Unable to enable DNAT rule … iptables: No chain/target/match by that name` o `error resolving DNS`
durante `docker build`). Suele pasar en Fedora cuando firewalld se recarga después de que arrancó
Docker y se pierden sus cadenas de iptables. Solución:

```bash
sudo systemctl restart docker   # reinicia también los contenedores en ejecución
```

Mientras tanto, los tests marcados `docker` se omiten si Docker no responde, y se puede construir con
`docker build --network host`.

**`pyenv: version '3.14' is not installed`:** no cree un `.python-version` en `backend/` si usa pyenv;
uv ya selecciona Python 3.14 a partir de `requires-python`.

**Angular pide otra versión de Node:** ejecute `nvm use` en la raíz del repo (lee `.nvmrc`).
