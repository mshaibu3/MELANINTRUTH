# Roadmap

## Completed

* Phase 1 foundation scaffold.
* Phase 2 backend hardening domain services for auth, consent, image upload, analysis lifecycle, rendering lifecycle, safety gate, audit, privacy, and governance.
* Phase 3 API-facing integration with SQLite-backed repositories, structured API errors, OpenAPI contract metadata, persistent lifecycle records, and API integration tests.
* Phase 3.5 FastAPI route factory, Pydantic schemas, normalized SQL schema specs, PostgreSQL-ready Alembic migrations, and OpenAPI tests.
* Phase 3.6 dependency-enabled Docker/CI path, pinned API dependencies, FastAPI TestClient coverage, concrete SQLModel models, repository adapters, and OpenAPI export.
* Phase 3.7 runtime repository verification and production fail-fast configuration.
* Phase 3.8 no-skip FastAPI CI, SQL-backed reads, required-table migration verification, and tenant-safe redaction.
* Phase 3.9 SQL-read completion and dependency-light regression coverage.

## Phase 3.10 — dependency-enabled CI proof gate completed

On 2026-07-10 UTC, commit `6458f1591fbaedd46316b2468d6b18e49ec4557f` passed both required GitHub Actions workflows:

* `api-integration` run `29109587040` completed successfully with dependency installation, Alembic migration, migration verification, no-skip FastAPI tests, OpenAPI generation, OpenAPI validation, zero OpenAPI drift, and PostgreSQL-compatible repository verification.
* `ci` run `29109587214` completed successfully with installation, linting, backend tests, and AI safety tests.

This evidence unlocks Phase 4 mobile implementation.

## Phase 4 — consent-first mobile foundation

Phase 4 delivers a testable Flutter application foundation with:

* onboarding that states the exact scientific limitation before analysis;
* separate required image/cloud consent and optional model-improvement consent;
* memory-only session handling with no token, password, or raw-image logging;
* guided capture telemetry that rejects underexposed, overexposed, and unstable conditions before analysis;
* governed result presentation with confidence, uncertainty, capture quality, lighting quality, explanation, and no-filter language;
* privacy export and deletion controls;
* an API gateway abstraction for authenticated backend integration without fabricating image uploads when secure camera-byte transport is unavailable;
* a dedicated `mobile-ci` workflow running Flutter dependency resolution, analysis, widget/controller tests, and coverage upload.

## Phase 4 follow-on increments

After the Phase 4 foundation passes mobile CI, the next increments are:

* native camera integration and device-permission handling;
* secure signed-upload transport for real camera bytes;
* platform secure storage for refresh-session persistence;
* accessibility verification on physical Android and iOS devices;
* offline retry, network-loss recovery, and production API environment configuration;
* device-level integration tests for capture, consent withdrawal, export, and deletion.
