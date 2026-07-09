# Deployment Notes

## Install and run

```bash
python -m pip install -e melanintruth-ai/services/api[dev]
uvicorn app.main:app --app-dir melanintruth-ai/services/api --host 0.0.0.0 --port 8000
```

## PostgreSQL readiness

Set `DATABASE_URL` to a PostgreSQL DSN, run Alembic migrations through `make migrate`, and verify OpenAPI with `make openapi-check`. Migration `0003_normalized_phase35_schema.py` is postgres-ready and includes tenant/user indexes, JSON payload fields, unique user email, and refresh token hash lookup.

## Constrained environments

If dependency installation is blocked, run the dependency-light verification path: `make lint`, `make test`, `make test-api`, `make migrate-test`, and `make openapi-check`.

## API Docker verification

```bash
make api-docker-build
make api-docker-test
```

`docker-compose.api.yml` starts the API with PostgreSQL-ready settings. `make postgres-up`, `make api-migrate`, `make test-postgres-real`, and `make postgres-down` provide the intended PostgreSQL verification flow.

## Runtime configuration

The API settings cover `APP_ENV`, `DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, token TTLs, CORS origins, storage backend/root, maximum image bytes, cloud-processing enablement, and log level. Production startup fails if `JWT_SECRET` is unset or left at a test value.

## Phase 3.7 Docker and PostgreSQL flow

`docker-compose.api.yml` starts PostgreSQL 16 with a healthcheck, then runs Alembic migrations before launching Uvicorn. Use `make api-docker-build`, `make postgres-up`, `make api-migrate`, `make test-postgres-real`, and `make postgres-down` in Docker-enabled environments. GitHub Actions caches pip dependencies, runs migrations against PostgreSQL, exports OpenAPI, and executes FastAPI/PostgreSQL tests.

## Phase 3.8 CI verification workflow

The API integration workflow uses PostgreSQL 16, installs pinned API dependencies, runs Alembic migrations, executes `make migration-verify` to confirm required tables, runs no-skip FastAPI tests, regenerates OpenAPI, checks drift, and runs PostgreSQL-compatible repository tests. Required environment variables are `APP_ENV`, `DATABASE_URL`, `JWT_SECRET`, `PYTHONPATH`, and `REQUIRE_FASTAPI_TESTS=1`.

## Phase 3.9 dependency-enabled proof requirement

The dependency-enabled proof sequence is: `make api-install`, `make api-migrate`, `make migration-verify`, `REQUIRE_FASTAPI_TESTS=1 make api-test`, `make api-openapi`, `make openapi-check`, `git diff --exit-code docs/api/openapi.json`, and `make test-postgres-real`. This environment could not complete it because package installation is blocked and Docker is unavailable; run the sequence in GitHub Actions or a Docker-enabled runner before promoting the backend.

## Phase 3.10 CI execution status

On 2026-07-09 UTC, this container could not execute the API integration workflow directly: `gh` is not installed, no git remote is configured, dependency installation fails with `403 Forbidden` for FastAPI, and Docker is unavailable. The required proof path is documented in `docs/deployment/API-CI-RUNBOOK.md`. Phase 4 mobile remains blocked until `.github/workflows/api-integration.yml` passes and the run evidence is recorded.
