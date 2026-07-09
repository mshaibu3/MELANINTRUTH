# MelaninTruth AI

**True skin. True tone. No filter.**

MelaninTruth AI is a production-shaped platform for capturing, analysing, standardising, and explaining visible skin appearance under different lighting conditions without beautifying, whitening, smoothing, reshaping, or altering identity.

A phone RGB image cannot perfectly measure biological melanin. The platform only reports estimated visible skin appearance under standardised lighting assumptions and always includes confidence, uncertainty, quality scores, and limitations.

## Repository layout

Core implementation lives under `melanintruth-ai/` with FastAPI services, ML safety baselines, Flutter/Next.js app skeletons, infrastructure, documentation, and tests.

## Quick start

```bash
make install
make lint
make test
```

## Safety promise

The only allowed transformation is scientifically constrained standardised-lighting rendering that preserves skin texture, pigmentation, scars, pores, vitiligo, hyperpigmentation, hypopigmentation, and identity.


## Phase 2 backend hardening

Phase 2 adds tested domain services for authentication, consent enforcement, secure image upload, analysis jobs, authentic rendering jobs, no-beautification safety reports, audit redaction, privacy export/deletion, and governance model release controls. The executable Phase 2 core intentionally uses dependency-light Python services so safety and security logic can be tested even when external package installation is unavailable.

## Phase 3 API and persistence integration

Phase 3 wires the tested Phase 2 services into a FastAPI-facing API application service with explicit route contracts, structured errors, SQLite-backed persistence for API integration tests, persistent audit/event records, privacy workflows, and OpenAPI contract generation. In this environment FastAPI is optional because the package is unavailable; the API logic remains executable through the same service layer and can be mounted by FastAPI when dependencies are installed.

## Phase 3.5 FastAPI mounting

The API package now declares real FastAPI, Pydantic, SQLModel/SQLAlchemy, Alembic, PostgreSQL driver, JWT, password-hashing, HTTPX, and pytest dependencies in `melanintruth-ai/services/api/pyproject.toml`. Install with:

```bash
python -m pip install -e melanintruth-ai/services/api[dev]
uvicorn app.main:app --app-dir melanintruth-ai/services/api
```

In constrained environments where package installation is blocked, dependency-light tests continue to exercise the same service boundary and OpenAPI contract fallback.

## Phase 3.6 dependency-enabled verification

Dependency-enabled API verification is available through Docker and requirements files:

```bash
make api-docker-build
make api-docker-test
make postgres-up
make api-migrate
make test-postgres-real
make postgres-down
```

The local constrained path remains:

```bash
make lint make test make test-fastapi make openapi-check
```

## Runtime repository selection

Application startup now builds `ApiApplication` with a repository selected from settings. SQLite URLs use the dependency-light repository; production SQL URLs require SQLModel dependencies and a DB session, and production refuses test JWT secrets.

## Phase 3.7 runtime verification

The dependency-enabled API path now uses pinned FastAPI/Pydantic/SQLModel dependencies from `melanintruth-ai/services/api/requirements.txt`. Run `make api-install`, then start the real app with `make api-run` (`PYTHONPATH=melanintruth-ai/services/api uvicorn app.main:app --reload`). When `DATABASE_URL` is configured and SQLModel dependencies are installed, runtime wiring selects the SQLModel repository path; production mode fails fast if the database URL or non-test `JWT_SECRET` are missing.

For PostgreSQL verification, use `make postgres-up`, `make api-migrate`, `make test-postgres-real`, and `make postgres-down`, or run `make api-docker-test` to execute the API tests in the Docker Compose stack. `make api-openapi` exports the live FastAPI contract to `docs/api/openapi.json`.

## Phase 3.8 CI evidence and SQL-backed reads

The API integration workflow now runs with `REQUIRE_FASTAPI_TESTS=1`, so missing FastAPI dependencies become CI failures instead of skips. The workflow installs pinned dependencies, runs Alembic migrations against PostgreSQL, verifies migrated tables, executes FastAPI tests, regenerates OpenAPI, checks OpenAPI drift, and runs PostgreSQL-compatible repository tests.

Runtime repository selection is explicit: `memory://` is allowed only for tests, SQLite is allowed for local dependency-light work, and production requires a non-SQLite `DATABASE_URL` plus SQL repository mode. Repository mode logging redacts credentials.

## Phase 3.9 verification status

Phase 3.9 keeps the dependency-light verification path passing and adds SQL-mode read preference for core getters. Dependency-enabled verification is still blocked in this execution environment: `make api-install` cannot reach the package index (`403 Forbidden` for FastAPI), `REQUIRE_FASTAPI_TESTS=1 make api-test` correctly fails when FastAPI is unavailable, and Docker/PostgreSQL commands cannot run because Docker is not installed. The committed CI workflow remains the required proof path before any production-readiness claim.

## Phase 3.10 CI proof gate

The dependency-enabled backend is not yet cleared for Phase 4 mobile from this container. On 2026-07-09 UTC, local dependency-light checks passed, but GitHub Actions could not be triggered because `gh` is unavailable and no git remote is configured. `make api-install` still fails here with a `403 Forbidden` package-index tunnel error for FastAPI, `REQUIRE_FASTAPI_TESTS=1 make api-test` fails as intended when FastAPI is missing, and Docker/PostgreSQL commands cannot run because Docker is not installed. Follow `docs/deployment/API-CI-RUNBOOK.md` and record a passing `api-integration` workflow before unlocking mobile work.
