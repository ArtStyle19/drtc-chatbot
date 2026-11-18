# Quickstart (spec 002)

```bash
make test-db                      # PostgreSQL temporal en :55432 (o `make dev-db` + `make migrate`)
export DRTC_DATABASE_URL=postgresql+psycopg://drtc:drtc@127.0.0.1:55432/drtc_chatbot_test
cd backend
uv run alembic upgrade head
uv run drtc-ingest sync           # manifiesto -> base de datos
uv run drtc-ingest run --all      # extrae, analiza, publica (y aprueba solo si la política es auto_dev)
uv run drtc-ingest report ley-27181@2020-05
uv run drtc-ingest sample ley-27181@2020-05 -n 20 --seed 1    # muestra para revisar contra el PDF
uv run drtc-ingest approve ley-27181@2020-05 --reviewer "Nombre Apellido"   # aprobación humana
curl localhost:8000/api/v1/instruments/ley-27181/provisions?kind=article&limit=5
```

Con Docker: `make up` ejecuta migraciones e ingesta (`ingest`) antes de levantar la API.
