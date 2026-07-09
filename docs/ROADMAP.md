# Roadmap

## Completed

* Phase 1 foundation scaffold.
* Phase 2 backend hardening domain services for auth, consent, image upload, analysis lifecycle, rendering lifecycle, safety gate, audit, privacy, and governance.
* Phase 3 API-facing integration with SQLite-backed repositories, structured API errors, OpenAPI contract metadata, persistent lifecycle records, and API integration tests.
* Phase 3.5 FastAPI route factory, Pydantic schema definitions with dependency-light fallback, normalized SQL schema specs, postgres-ready Alembic migration, and OpenAPI tests.

## Next

* Run dependency installation in CI/build images once package index access is available.
* Execute real FastAPI `TestClient` tests against the mounted app in CI.
* Replace compatibility repository facade with fully normalized SQLModel repositories per aggregate.
* Add PostgreSQL service-container tests with Alembic upgrade/downgrade execution.

## Phase 3.6 completed

* Added dependency-enabled Docker/CI path, requirements file, FastAPI TestClient tests that run when dependencies are installed, concrete SQLModel ORM definitions, SQLModel repository adapter, OpenAPI export command, and PostgreSQL-ready workflow targets.

## Phase 3.7 — runtime verification

* Pin dependency-enabled API versions for reproducible FastAPI, Pydantic, SQLModel, Alembic, HTTPX, and PostgreSQL test runs.
* Wire runtime repository selection so production requires SQL dependencies and a configured database, while dependency-light tests remain explicit.
* Expand FastAPI TestClient coverage across auth, consent, images, analysis, rendering, privacy, governance, and redaction controls.
* Verify OpenAPI export from the live app and PostgreSQL migration flow in CI/Docker environments.

## Phase 3.8 — CI evidence and SQL-backed reads

* Enforce no-skip FastAPI tests in dependency-enabled CI with `REQUIRE_FASTAPI_TESTS=1`.
* Add SQLModel read methods for core users, sessions, consent, images, analysis, renders, safety reports, audit, privacy, governance, and incident aggregates.
* Add a required-table migration verification script and Alembic revision for runtime table names.
* Preserve dependency-light local test paths while ensuring production fails fast on unsafe repository fallbacks.

## Phase 3.9 — SQL-read completion and blocked CI proof

* SQLModel runtime getters now prefer SQL reads when a SQL session is active, falling back to dependency-light maps only outside SQL mode.
* Local dependency-light tests pass, including a fake SQL-session regression test proving SQL reads override stale memory maps.
* Dependency-enabled CI proof remains required in an environment with package-index and Docker/PostgreSQL access.

## Phase 3.10 — dependency-enabled CI proof gate

* Local dependency-light verification remains green, including lint, backend, AI, API-service, migration smoke, OpenAPI, PostgreSQL-compatible contract tests, and OpenAPI export.
* This container cannot trigger GitHub Actions (`gh` unavailable and no git remote), cannot install FastAPI dependencies (`403 Forbidden` package-index tunnel), and cannot run Docker/PostgreSQL (`docker` unavailable).
* Phase 4 mobile remains blocked until `.github/workflows/api-integration.yml` passes in a dependency-enabled runner and the run evidence is recorded.
