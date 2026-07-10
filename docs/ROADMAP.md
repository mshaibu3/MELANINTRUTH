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

## Phase 4 — consent-first mobile foundation completed

Commit `85339451e4c69c22818035373cae6b34d20a4ae1` passed `ci`, `api-integration`, and `mobile-ci` on 2026-07-10 UTC. Phase 4 delivered:

* onboarding that states the exact scientific limitation before analysis;
* separate required image/cloud consent and optional model-improvement consent;
* memory-only access-session handling with no token, password, or raw-image logging;
* guided capture telemetry that rejects underexposed, overexposed, and unstable conditions before analysis;
* governed result presentation with confidence, uncertainty, capture quality, lighting quality, explanation, and no-filter language;
* privacy export and deletion controls;
* a dedicated strict `mobile-ci` workflow with Flutter analysis, tests, coverage, and read-only repository permissions.

## Phase 5 — mobile production integration

Phase 5 moves the Flutter foundation onto the real backend lifecycle while preserving the Phase 4 safety controls:

* native platform camera capture through `image_picker`, with cancellation and permission denial surfaced safely;
* JPEG/PNG and 10 MB limits plus local SHA-256 checksums;
* authenticated signed-upload request, HTTPS binary PUT, upload completion, and analysis creation;
* bounded retry only for the idempotent binary PUT;
* platform secure storage for refresh token and session ID, with access tokens retained in memory;
* refresh-token rotation, invalid-session clearing, and server-side consent revalidation before automatic restoration;
* gateway and controller tests covering transport order, bytes, checksum headers, retry, secure-session rotation, consent restoration, and privacy deletion.

## Phase 5 release boundary

The Phase 5 pull request may be merged after `ci`, `api-integration`, and `mobile-ci` pass. It does not constitute an Android or iOS production release. Native release readiness additionally requires generated platform projects, camera usage descriptions, application signing, environment-specific API configuration, store entitlements, accessibility verification, and physical-device integration tests.

## Phase 6 candidates

* Generate and harden Android/iOS platform projects and permission manifests.
* Add device-farm tests for camera permission denial, capture cancellation, offline upload recovery, consent withdrawal, export, and deletion.
* Add short-lived signed-upload expiry handling and server-issued idempotency keys.
* Add production observability that excludes tokens, raw images, checksums, and user-identifying paths.
