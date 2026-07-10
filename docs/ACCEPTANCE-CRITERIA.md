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

## Phase 5 mobile production-integration acceptance criteria — satisfied

* Native capture uses the platform camera picker and surfaces cancellation or denied permission without fabricating image bytes.
* Only JPEG or PNG captures of 10 MB or less are accepted, and every capture is assigned a SHA-256 checksum before transport.
* Production API base URLs require HTTPS, except explicit emulator/local-development hosts.
* The upload path follows the backend contract exactly: authenticated upload request, HTTPS binary PUT, authenticated upload completion, then authenticated analysis creation.
* The signed binary PUT is the only automatically retried state in the upload lifecycle; retries are bounded and limited to transport, timeout, rate-limit, and server failures.
* Access tokens remain memory-only. Refresh token and session ID are persisted through platform secure storage, rotated through `/auth/refresh`, and cleared after privacy deletion or invalid refresh.
* Restored sessions are not admitted to the home screen until required image-processing and cloud-processing consent are revalidated through `/consent`.
* Gateway tests verify request ordering, raw bytes, checksum headers, bounded retry, refresh rotation, consent revalidation, HTTPS enforcement, and deletion-state clearing.
* Post-merge commit `8855ffc4bdbd8e83e499089ca5c82654ec950a8d` passed `ci`, `mobile-ci`, and `api-integration`.

## Phase 6 native release-hardening acceptance criteria

Phase 6 is accepted only when all of the following are true:

* Canonical Android and iOS platform projects are committed and use `com.hakilixlabs.melanintruth` as the production identity.
* Android declares CAMERA and INTERNET permissions, disables application backup, blocks cleartext traffic, enables release shrinking, and contains no release fallback to the debug signing key.
* Android release signing is read only from an ignored `key.properties` file and no keystore or signing secret is committed.
* iOS includes a precise camera usage description, blocks arbitrary network loads, declares only exempt encryption, and targets iOS 13.0 or later.
* Release-mode application startup fails closed when `MELANINTRUTH_API_BASE_URL` is absent, malformed, or non-HTTPS; it must never silently enter preview mode.
* Telemetry accepts only allow-listed coarse lifecycle fields and rejects tokens, signed URLs, checksums, raw bytes, and user identifiers.
* `tool/verify_native_config.py` passes against the committed native configuration.
* `mobile-ci` passes formatting, static analysis, and all unit/widget/controller/gateway tests.
* `mobile-native-ci` builds unsigned Android and iOS release artifacts and runs the consent/accessibility smoke test on an Android emulator.
* Existing `ci` and `api-integration` workflows remain green on the same Phase 6 head commit.
* Phase 6 does not claim store-release readiness until production signing, store entitlements, physical-device camera and permission testing, accessibility review, privacy declarations, and release governance approval are recorded.
