# DRTC Puno – Asistente normativo. Run `make help` to list the targets.
# Node is managed with nvm (.nvmrc = 26); Python with uv (backend/pyproject.toml).

SHELL := /bin/bash
.DEFAULT_GOAL := help

NVM := export NVM_DIR="$${NVM_DIR:-$$HOME/.nvm}"; [ -s "$$NVM_DIR/nvm.sh" ] && . "$$NVM_DIR/nvm.sh" && nvm use --silent >/dev/null;
BACKEND := cd backend &&
FRONTEND := $(NVM) cd frontend &&

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# --------------------------------------------------------------------------- setup
.PHONY: bootstrap
bootstrap: ## Install every dependency and the git hooks
	$(BACKEND) uv sync
	$(FRONTEND) npm ci
	pre-commit install

# --------------------------------------------------------------------------- run
.PHONY: dev-db
dev-db: ## Start only PostgreSQL + pgvector (host port 5433)
	docker compose up -d db

TEST_DB_PORT ?= 55432
.PHONY: test-db
test-db: ## Throwaway PostgreSQL+pgvector on :55432 for DB tests (host network; works when port publishing is broken)
	-docker rm -f drtc-test-db >/dev/null 2>&1
	docker run -d --rm --name drtc-test-db --network host -e POSTGRES_USER=drtc -e POSTGRES_PASSWORD=drtc \
	  -e POSTGRES_DB=drtc_chatbot_test pgvector/pgvector:0.8.7-pg18-trixie postgres -c port=$(TEST_DB_PORT) -c listen_addresses=127.0.0.1
	@until docker exec drtc-test-db pg_isready -h 127.0.0.1 -p $(TEST_DB_PORT) -U drtc >/dev/null 2>&1; do sleep 1; done
	@echo "Ready. Run the DB tests with:  export DRTC_TEST_DATABASE_URL=postgresql+psycopg://drtc:drtc@127.0.0.1:$(TEST_DB_PORT)/drtc_chatbot_test"

.PHONY: test-db-stop
test-db-stop: ## Stop the throwaway test database
	-docker rm -f drtc-test-db

.PHONY: migrate
migrate: ## Apply database migrations to the dev database
	$(BACKEND) uv run alembic upgrade head

.PHONY: ingest
ingest: ## Load the manifest and ingest every corpus PDF into the dev database (spec 002)
	$(BACKEND) uv run drtc-ingest run --all

.PHONY: dev-backend
dev-backend: ## Run the API with auto-reload on http://localhost:8000
	$(BACKEND) uv run uvicorn drtc_chatbot.main:app --reload --port 8000

.PHONY: dev-frontend
dev-frontend: ## Run Angular on http://localhost:4200 (proxies /api to :8000)
	$(FRONTEND) npm start

.PHONY: up
up: ## Build and run the full stack in Docker (web on http://localhost:8080)
	docker compose --profile app up -d --build

.PHONY: down
down: ## Stop the Docker stack
	docker compose --profile app down

# --------------------------------------------------------------------------- quality
.PHONY: format
format: ## Format backend and frontend code
	$(BACKEND) uv run ruff format src tests migrations && uv run ruff check --fix src tests migrations
	$(FRONTEND) npm run format

.PHONY: lint
lint: ## Lint backend (ruff) and frontend (eslint + prettier)
	$(BACKEND) uv run ruff format --check src tests migrations && uv run ruff check src tests migrations
	$(FRONTEND) npm run lint && npm run format:check

.PHONY: typecheck
typecheck: ## Static type checking (mypy strict)
	$(BACKEND) uv run mypy

.PHONY: arch
arch: ## Check the architecture contracts (import-linter)
	$(BACKEND) uv run lint-imports

.PHONY: test-backend
test-backend: ## Backend tests with coverage (Docker tests are skipped if Docker is unavailable)
	$(BACKEND) uv run pytest --cov --cov-report=term-missing:skip-covered

.PHONY: test-frontend
test-frontend: ## Frontend unit tests (Vitest)
	$(FRONTEND) npm run test:ci

.PHONY: test
test: test-backend test-frontend ## All unit/integration tests

.PHONY: e2e
e2e: ## End-to-end + accessibility tests (Playwright; API mocked unless E2E_REAL_API=1)
	$(FRONTEND) npx playwright test

.PHONY: build
build: ## Production build of the frontend
	$(FRONTEND) npm run build

.PHONY: openapi
openapi: ## Export the API contract and regenerate the frontend types
	$(BACKEND) uv run python -m drtc_chatbot.entrypoints.http.export_openapi openapi.json
	$(FRONTEND) npm run api:types

.PHONY: corpus-check
corpus-check: ## Verify the original PDFs still match corpus/manifest.yaml
	$(BACKEND) uv run pytest -q tests/integration/corpus

.PHONY: check
check: lint typecheck arch test build ## Everything CI runs (except e2e)
