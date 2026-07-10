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

* CI must run `make api-install`, `make api-migrate`, `make migration-verify`, `make api-test`, `make api-openapi`, `make openapi-check`, `git diff --exit-code docs/api/openapi.json`, and `make test-postgres-real` against PostgreSQL.
* `REQUIRE_FASTAPI_TESTS=1` converts missing FastAPI dependencies into failures, preventing accidental skipped API coverage in CI.
* SQLModel repositories provide read and write helpers for core aggregates and return redacted image/session views.
* Production startup must not fall back to memory or SQLite repositories.

## Phase 3.9 acceptance status

* Dependency-light lint, backend, AI, API-service, migration-smoke, OpenAPI, and PostgreSQL-compatible tests must pass locally.
* `REQUIRE_FASTAPI_TESTS=1 make api-test` must fail in constrained environments without FastAPI and pass without skips in dependency-enabled CI.
* Backend production readiness is not accepted until dependency installation, Alembic migration, migration verification, OpenAPI drift protection, and PostgreSQL-backed tests pass in CI.

## Phase 3.10 backend unlock criteria — satisfied

* `.github/workflows/api-integration.yml` passed with PostgreSQL on 2026-07-10 UTC as run `29109587040` for commit `6458f1591fbaedd46316b2468d6b18e49ec4557f`.
* The run proved dependency installation, Alembic migration, migration verification, no-skip FastAPI coverage, OpenAPI generation and validation, zero OpenAPI drift, and PostgreSQL-compatible repository verification.
* The general `ci` workflow also passed as run `29109587214` for the same commit.

## Phase 4 mobile acceptance criteria — satisfied

* `.github/workflows/mobile-ci.yml` passes `flutter pub get`, strict Dart formatting, `flutter analyze`, and all Flutter tests without skips.
* The first-run flow displays the exact scientific limitation before capture or analysis.
* Image-processing and cloud-processing consent are required and independently represented; model-improvement consent remains optional and off by default.
* No screen or gateway path claims exact biological melanin measurement, beauty enhancement, whitening, lightening, smoothing, reshaping, or identity alteration.
* Phase 4 access credentials remain memory-only and are never logged.
* Capture-quality logic rejects underexposed, overexposed, and unstable conditions before analysis.
* Results include confidence, uncertainty, lighting quality, capture quality, explanation, limitation language, and explicit no-filter status.
* Privacy controls expose data-export and data-deletion requests, and deletion clears the local session and consent state.
* Widget and controller tests cover the consent-first happy path, unsafe capture rejection, optional model-improvement consent, and deletion-state clearing.

## Phase 5 mobile production-integration acceptance criteria

Phase 5 is accepted only when all of the following are true:

* Native capture uses the platform camera picker and surfaces cancellation or denied permission without fabricating image bytes.
* Only JPEG or PNG captures of 10 MB or less are accepted, and every capture is assigned a SHA-256 checksum before transport.
* Production API base URLs require HTTPS, except explicit emulator/local-development hosts.
* The upload path follows the backend contract exactly: authenticated upload request, HTTPS binary PUT, authenticated upload completion, then authenticated analysis creation.
* The signed binary PUT is the only automatically retried state in the upload lifecycle; retries are bounded and limited to transport, timeout, rate-limit, and server failures.
* Access tokens remain memory-only. Refresh token and session ID are persisted through platform secure storage, rotated through `/auth/refresh`, and cleared after privacy deletion or invalid refresh.
* Restored sessions are not admitted to the home screen until required image-processing and cloud-processing consent are revalidated through `/consent`.
* Gateway tests verify request ordering, raw bytes, checksum headers, bounded retry, refresh rotation, consent revalidation, HTTPS enforcement, and deletion-state clearing.
* The existing `ci`, `api-integration`, and `mobile-ci` workflows pass on the Phase 5 pull request without skipped mobile tests.
* Phase 5 does not claim a production Android or iOS release until platform scaffolding, camera usage descriptions, application signing, store entitlements, accessibility checks, and physical-device tests are completed and recorded.
