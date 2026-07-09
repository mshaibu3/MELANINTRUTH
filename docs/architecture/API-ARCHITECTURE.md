# API Architecture

The Phase 3.5 API uses a thin FastAPI route factory in `app.api.router`. Route decorators validate payloads with Pydantic schemas when dependencies are installed, extract bearer tokens, and call `ApiApplication`. `ApiApplication` delegates business rules to the tested Phase 2 services for auth, consent, image upload, analysis, rendering, privacy, governance, and audit.

Persistence is split into dependency-light SQLite-compatible repository tests and a postgres-ready normalized migration. The next phase should bind the normalized tables to SQLModel repositories while preserving the existing service boundary.

All analysis and render outputs preserve the scientific limitation language and no-beautification safety gate semantics.

## SQLModel runtime adapter

`app.db.models` defines concrete SQLModel ORM classes when SQLModel/SQLAlchemy are installed. `SQLModelRepository` preserves the existing service boundary while mirroring users, sessions, consent, images, analysis jobs, render jobs, safety reports, audit logs, and model versions into SQL tables.

## Runtime repository selection

`app.services.container.repository_from_settings` selects `SQLiteRepository` for SQLite/test URLs and `SQLModelRepository` for production SQL URLs when SQLModel and a DB session are available. Production startup validates that `JWT_SECRET` is not a test value before constructing the runtime container.

## Phase 3.7 runtime wiring

`app.main` builds an `ApiApplication` with `repository_from_settings()`. Test and development SQLite URLs use the dependency-light SQLite repository. Configured SQL URLs in dependency-enabled environments select `SQLModelRepository`; production refuses to silently fall back to in-memory state. FastAPI route handlers remain thin and call the service boundary instead of duplicating auth, consent, safety, or governance logic.

## Phase 3.8 SQL read model

`SQLModelRepository` now exposes read helpers for IDs, users, tenants, active records, render safety reports, privacy/governance records, and redacted public views. These helpers preserve AI metadata while excluding refresh token hashes and internal image storage references from API-facing dictionaries.

## Phase 3.9 SQL runtime reads

When `SQLModelRepository` has an active SQL session, core getters read SQL first for users, sessions, consent, images, analysis jobs, and render jobs, then refresh the service maps. Memory-first reads remain only for dependency-light mode without SQL dependencies/session.

## Phase 3.10 backend verification gate

Architecture remains backend-ready but not mobile-unlocked until the dependency-enabled CI path proves the real FastAPI runtime with PostgreSQL migrations. The current local environment proves the dependency-light service boundary and SQL-read tests only; it does not prove installed FastAPI, Alembic, SQLModel, or PostgreSQL execution.
