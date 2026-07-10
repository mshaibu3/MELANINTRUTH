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

Commit `85339451e4c69c22818035373cae6b34d20a4ae1` passed `ci`, `api-integration`, and `mobile-ci` on 2026-07-10 UTC. Phase 4 delivered onboarding, independent consent, quality gating, governed results, privacy controls, and strict Flutter CI.

## Phase 5 — mobile production integration completed

Commit `8855ffc4bdbd8e83e499089ca5c82654ec950a8d` passed post-merge `ci` run `29116800297`, `mobile-ci` run `29116800314`, and `api-integration` run `29116800346`. Phase 5 delivered:

* native camera capture through `image_picker`;
* JPEG/PNG and 10 MB limits plus local SHA-256 checksums;
* authenticated signed-upload request, HTTPS binary PUT, upload completion, and analysis creation;
* bounded retry only for the idempotent binary PUT;
* platform secure storage for refresh token and session ID, with access tokens retained in memory;
* refresh-token rotation, invalid-session clearing, and server-side consent revalidation;
* gateway and controller tests covering transport order, bytes, checksum headers, retry, session restoration, and privacy deletion.

## Phase 6 — native release hardening

Phase 6 closes the generated-platform and native-build gap while retaining a strict no-store-release boundary:

* commit canonical Android and iOS Flutter projects;
* use the stable package and bundle identity `com.hakilixlabs.melanintruth`;
* declare camera use explicitly and prohibit arbitrary or cleartext network transport;
* disable Android application backup and remove the generated debug-key release-signing fallback;
* support secret-backed Android signing without committing keystores or credentials;
* fail closed in release builds when `MELANINTRUTH_API_BASE_URL` is absent or non-HTTPS;
* emit only allow-listed, non-identifying lifecycle telemetry;
* verify native configuration in code;
* build unsigned Android and iOS release artifacts in CI;
* execute consent and accessibility smoke coverage on an Android emulator.

## Phase 6 release boundary

Phase 6 proves reproducible unsigned native builds and emulator-level acceptance. It does not claim App Store or Play Store readiness until production signing credentials, store entitlements, final icons/launch assets, environment-specific endpoints, physical camera and permission-denial tests, accessibility review on real devices, privacy declarations, and release-candidate approval are completed and recorded.

## Phase 7 candidates

* Add signed release-candidate workflows backed by protected environments and short-lived credentials.
* Run physical-device or managed device-farm tests for camera capture, permission denial, cancellation, offline recovery, consent withdrawal, export, and deletion.
* Add server-issued upload expiry and idempotency contracts.
* Complete store privacy manifests, data-safety declarations, screenshots, and release governance evidence.
