# MelaninTruth AI

**True skin. True tone. No filter.**

MelaninTruth AI is a production-shaped platform for capturing, analysing, standardising, and explaining visible skin appearance under different lighting conditions without beautifying, whitening, smoothing, reshaping, or altering identity.

A phone RGB image cannot perfectly measure biological melanin. The platform only reports estimated visible skin appearance under standardised lighting assumptions and always includes confidence, uncertainty, quality scores, and limitations.

## Repository layout

Core implementation lives under `melanintruth-ai/` with FastAPI services, ML safety baselines, Flutter/Next.js applications, infrastructure, documentation, and tests.

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

Phase 3 wires the tested Phase 2 services into a FastAPI-facing API application service with explicit route contracts, structured errors, SQLite-backed persistence for API integration tests, persistent audit/event records, privacy workflows, and OpenAPI contract generation.

## Phase 3.5–3.9 backend completion

The API package declares FastAPI, Pydantic, SQLModel/SQLAlchemy, Alembic, PostgreSQL, JWT, password-hashing, HTTPX, and pytest dependencies. Runtime repository selection is explicit: memory mode is test-only, SQLite supports constrained local work, and production requires a non-SQLite database with SQL repository mode.

The dependency-enabled workflow installs pinned dependencies, applies Alembic migrations to PostgreSQL, verifies required tables, runs no-skip FastAPI tests, regenerates and validates OpenAPI, protects against OpenAPI drift, and runs PostgreSQL-compatible repository tests.

## Phase 3.10 CI proof gate — completed

On 2026-07-10 UTC, commit `6458f1591fbaedd46316b2468d6b18e49ec4557f` passed:

* `api-integration` run `29109587040`;
* `ci` run `29109587214`.

This evidence cleared the backend gate for Phase 4 mobile work.

## Phase 4 consent-first Flutter foundation

The mobile application now provides:

* scientific-limitation onboarding;
* separate image/cloud consent and optional model-improvement consent;
* memory-only authenticated sessions;
* guided capture-quality telemetry and retake guidance;
* governed results with confidence, uncertainty, lighting quality, capture quality, explanation, and explicit no-filter status;
* privacy export and deletion controls;
* a backend gateway abstraction that refuses to fabricate image uploads when secure camera-byte transport is unavailable;
* Flutter widget/controller tests and a dedicated `mobile-ci` workflow.

Run the mobile app in local preview mode:

```bash
cd melanintruth-ai/apps/mobile
flutter pub get
flutter run
```

Configure an API base URL for authenticated backend operations:

```bash
flutter run --dart-define=MELANINTRUTH_API_BASE_URL=https://api.example.com
```

The Phase 4 foundation intentionally does not claim native camera-byte upload is complete. Native camera integration, secure signed upload, platform secure storage, and physical-device accessibility testing are follow-on increments documented in `docs/ROADMAP.md`.
