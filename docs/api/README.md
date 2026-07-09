# API Lifecycle Notes

## Authentication

Clients register with `POST /auth/register`, authenticate with `POST /auth/login`, rotate refresh tokens with `POST /auth/refresh`, invalidate sessions with `POST /auth/logout`, inspect sessions with `GET /auth/sessions`, and request account deletion with `POST /auth/account-deletion-request`.

Use bearer tokens for protected endpoints. Structured errors follow:

```json
{"error":{"code":"CONSENT_REQUIRED","message":"Image-processing consent is required before analysis.","details":{}}}
```

## Consent enforcement

Image upload, cloud analysis, rendering, progress, model improvement, and enterprise sharing must call service-layer consent checks before processing. Revoked consent blocks future processing.

## Upload lifecycle

`POST /images/upload-request` validates authentication, image-processing consent, content type, size, and SHA-256 checksum, then returns a signed URL abstraction. `POST /images/upload-complete` stores metadata. `GET /images/{image_id}` never returns raw storage paths.

## Analysis lifecycle

`POST /analysis/jobs` moves jobs through pending, quality_checked, rejected_low_quality, analysing, completed, failed, and deleted. Completed results include confidence, uncertainty, lighting quality score, capture quality score, limitation warning, and retake recommendation.

## Rendering lifecycle

`POST /renders` requires a completed analysis. The no-beautification safety gate blocks whitening, smoothing, excessive brightness shifts, histogram shifts, edge loss, and low-confidence renders. Blocked renders are persisted but not returned as valid image outputs.

## Privacy lifecycle

`POST /privacy/export` creates a scoped export with profile, consent, image metadata, analysis metadata, render metadata, and audit summary. `POST /privacy/delete` revokes sessions and consent, marks image records deleted, and blocks future processing.

## Governance workflow

Normal users cannot mutate governance records. Admin model versions require known limitations; production versions require approval fields. Dataset versions require provenance notes, incidents require severity and mitigation status, and production model approval is audited.

## OpenAPI

The Phase 3 application exposes an OpenAPI-compatible contract with auth, consent, image, analysis, render, privacy, governance, audit, error schema, and bearer-auth security scheme metadata.

## FastAPI mounting

`app.api.router.create_fastapi_app()` creates the real FastAPI app when dependencies are installed. It mounts concrete decorators for health, auth, consent, images, analysis jobs, renders, privacy, governance, and audit routes. Routes are thin and call `ApiApplication`, which delegates to the tested Phase 2 services.

## Local run

```bash
python -m pip install -e melanintruth-ai/services/api[dev]
uvicorn app.main:app --app-dir melanintruth-ai/services/api --reload
```

## OpenAPI check

```bash
make openapi-check
```

## PostgreSQL readiness

Migration `0003_normalized_phase35_schema.py` creates postgres-ready normalized tables with tenant/user indexes, JSON payloads, unique email index, and refresh-token hash lookup index. Local fallback tests use SQLite when PostgreSQL is unavailable.

## Dependency-enabled verification

Run real FastAPI tests in an environment with dependencies installed:

```bash
make api-install
make test-fastapi
make api-openapi
```

The TestClient suite under `melanintruth-ai/tests/api_fastapi` exercises real mounted routes when FastAPI is importable and is skipped in constrained environments.

## Phase 3.7 API runtime

Install pinned API dependencies with `make api-install`. Start the app with `make api-run`, then inspect `/health` and `/openapi.json`. Protected routes use bearer tokens returned from `/auth/login`; image upload, analysis, rendering, privacy, and governance routes enforce authentication and service-level consent/role checks.

Generate and commit the live contract with `make api-openapi`. CI runs the same export and fails if `docs/api/openapi.json` changes without being committed.

## Phase 3.8 CI API verification

CI sets `REQUIRE_FASTAPI_TESTS=1` before running `make api-test`; this turns FastAPI import skips into failures. After `make api-openapi`, CI runs both `make openapi-check` and `git diff --exit-code docs/api/openapi.json` so the committed contract cannot drift from the generated app contract.

## Phase 3.9 OpenAPI proof status

`make api-openapi` and `make openapi-check` pass in the dependency-light environment. The real FastAPI OpenAPI proof must be completed in CI after `make api-install`; CI sets `REQUIRE_FASTAPI_TESTS=1` so any missing dependency or unexpected FastAPI skip fails the workflow.

## Phase 3.10 FastAPI proof gate

FastAPI tests are allowed to skip only in constrained local environments without optional dependencies. CI must set `REQUIRE_FASTAPI_TESTS=1`, which converts missing FastAPI dependencies into failures. The API contract is not considered dependency-enabled verified until `make api-install`, `REQUIRE_FASTAPI_TESTS=1 make api-test`, `make api-openapi`, `make openapi-check`, and `git diff --exit-code docs/api/openapi.json` pass in the API integration workflow.
