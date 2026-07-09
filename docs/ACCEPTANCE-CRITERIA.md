# Acceptance Criteria

Phase 3.5 acceptance requires:

* FastAPI route factory defines concrete route decorators for auth, consent, images, analysis, renders, privacy, and governance.
* Pydantic schemas exist for public request and response contracts when dependencies are installed, with dependency-light fallbacks for constrained test environments.
* OpenAPI contract includes required public paths and bearer-auth metadata.
* Normalized database table specs and postgres-ready Alembic migration cover users, sessions, consent, images, analysis, renders, safety reports, audit, privacy, governance, datasets, bias reports, and incidents.
* Existing dependency-light tests continue to pass.
* API contract tests verify required paths and normalized table coverage.

## Phase 3.6 acceptance

* FastAPI TestClient tests exist and are skipped only when FastAPI is unavailable locally.
* Docker and CI paths install the real dependency set.
* Concrete SQLModel models exist for core aggregates.
* SQLModel repository adapter mirrors Phase 2 writes into SQL tables when dependencies are installed.
* `docs/api/openapi.json` is generated and committed.

## Phase 3.7 acceptance criteria

* The FastAPI app starts through `app.main:app` with secure headers, CORS from settings, structured error envelopes, and bearer auth in OpenAPI.
* Analysis and render API responses preserve the exact scientific limitation statement and include confidence, uncertainty, quality, and safety metadata.
* SQLModel runtime repositories persist core aggregates when a SQL session is available and retain tenant/user redaction guarantees.
* PostgreSQL migrations run from Alembic metadata in CI before dependency-enabled API tests.

## Phase 3.8 acceptance criteria

* CI must run `make api-install`, `make api-migrate`, `make migration-verify`, `make api-test`, `make api-openapi`, `make openapi-check`, and `make test-postgres-real` against PostgreSQL.
* `REQUIRE_FASTAPI_TESTS=1` converts missing FastAPI dependencies into failures, preventing accidental skipped API coverage in CI.
* SQLModel repositories provide read and write helpers for core aggregates and return redacted image/session views.
* Production startup must not fall back to memory or SQLite repositories.

## Phase 3.9 acceptance status

* Dependency-light lint, backend, AI, API-service, migration-smoke, OpenAPI, and PostgreSQL-compatible tests must pass locally.
* `REQUIRE_FASTAPI_TESTS=1 make api-test` must fail in constrained environments without FastAPI and pass without skips in dependency-enabled CI.
* Backend production readiness is not accepted until dependency installation, Alembic migration, migration verification, OpenAPI drift protection, and PostgreSQL-backed tests pass in CI.

## Phase 3.10 backend unlock criteria

* The backend is **not accepted as dependency-enabled verified** until `.github/workflows/api-integration.yml` passes with a PostgreSQL service.
* The passing run must prove `make api-install`, `make api-migrate`, `make migration-verify`, `REQUIRE_FASTAPI_TESTS=1 make api-test`, `make api-openapi`, `make openapi-check`, `git diff --exit-code docs/api/openapi.json`, and `make test-postgres-real`.
* Phase 4 mobile remains blocked until the workflow status, UTC timestamp, commit SHA, and no-skip FastAPI/PostgreSQL/OpenAPI proof are documented.
