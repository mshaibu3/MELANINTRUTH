# DPIA

## Processing

MelaninTruth AI processes high-risk skin and face image metadata to estimate visible skin appearance under standardised lighting assumptions. Biological melanin, race, ethnicity, and disease diagnosis are not inferred.

## Phase 3 API controls

* Explicit purpose-specific consent is required for image processing, cloud processing, model improvement, and enterprise sharing.
* Upload, analysis, and rendering call service-level consent checks before processing.
* Model improvement records are excluded unless opt-in consent exists.
* Privacy exports are scoped to the requesting user and tenant and exclude raw storage paths.
* Deletion revokes consent and sessions, marks images deleted, and blocks future processing.
* Audit events avoid unnecessary personal data and redact raw image paths and tokens.

## Phase 3.5 additions

FastAPI routes preserve service-level consent enforcement and redacted response contracts. Pydantic schemas avoid raw storage path fields, and OpenAPI docs expose only privacy-safe metadata fields for upload, analysis, render, export, and deletion workflows.

## Phase 3.6 additions

Concrete ORM models separate internal encrypted storage references from public metadata schemas. FastAPI TestClient coverage validates consent-gated upload, analysis, render, privacy export, and deletion flows in dependency-enabled environments.

## Phase 3.7 privacy verification

FastAPI tests exercise consent grant/revoke, image upload blocking after revocation, tenant-scoped export, deletion-triggered processing blocks, and response redaction. SQLModel image records keep internal storage references in non-public fields; API responses expose only safe metadata and never raw personal image data.

## Phase 3.8 privacy controls

SQL-backed read helpers support active-record filtering, tenant/user scoping, redacted image metadata, and privacy request persistence. Audit tests assert tokens and storage paths are removed from metadata before persistence, and deleted/revoked states remain available for processing-block checks without exposing raw image data.

## Phase 3.9 privacy verification note

SQL-mode image and session reads continue to redact internal storage references and refresh-token hashes from API-facing dictionaries. Full PostgreSQL privacy-flow proof remains blocked locally by package-index and Docker availability and must run in CI before production claims.
