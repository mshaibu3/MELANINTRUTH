# Threat Model

## Key threats

* Credential stuffing and brute-force login attempts.
* Refresh-token theft and session replay.
* Cross-tenant access to image, analysis, render, privacy, or governance records.
* Raw image path leakage through metadata or logs.
* Unsafe rendering that lightens, whitens, smooths, or alters identity.
* Model release without documented limitations or approval.

## Phase 3 controls

* Protected API methods require bearer-token context.
* Login uses a rate-limit hook and structured failed-login audit events.
* Refresh tokens are hashed in session records and rotated on refresh.
* Logout invalidates sessions and persisted session state.
* Service-layer consent and ownership checks protect upload, analysis, and render workflows.
* SQLite-backed API integration records preserve tenant_id and user_id for scoped queries.
* Structured errors prevent accidental leakage of tokens, passwords, or raw storage paths.
* Audit metadata redacts tokens, passwords, raw images, raw paths, and biometric templates.
* Safety gate blocks excessive tone delta, smoothing, local contrast loss, histogram shift, brightness shift, and low confidence.

## Phase 3.5 additions

* FastAPI bearer dependencies protect sensitive route groups when FastAPI is installed.
* Secure headers middleware sets `X-Content-Type-Options`, `X-Frame-Options`, and `Referrer-Policy`.
* Route handlers unwrap structured service responses without logging tokens, passwords, or raw image data.
* Governance mutation routes require admin tokens through the same service boundary.

## Phase 3.6 additions

Dependency-enabled TestClient coverage verifies mounted FastAPI behavior when dependencies are available. SQLModel repositories keep token hashes and encrypted storage references out of user-facing response schemas and preserve audit redaction through the service layer.

## Phase 3.7 runtime threats and controls

Runtime fallback risk is mitigated by failing production startup when SQL dependencies or `DATABASE_URL` are unavailable. FastAPI protected routes use bearer authentication, governance mutations require admin roles, structured errors avoid stack traces, and SQLModel repositories preserve redaction of refresh tokens and internal image storage references. Audit metadata redaction is tested for tokens and raw storage paths.

## Phase 3.8 verification controls

CI now fails if FastAPI tests skip unexpectedly, if migrations fail, or if OpenAPI drift appears. Repository-mode logging uses redacted database labels, and production rejects memory/SQLite repository modes. SQL read helpers return redacted views for images and sessions to avoid storage-path and refresh-token-hash leakage.

## Phase 3.9 security verification note

SQL-mode getters now avoid stale memory-first reads for core authentication and processing resources. The no-skip FastAPI gate intentionally fails when dependencies are missing under `REQUIRE_FASTAPI_TESTS=1`, preventing CI from silently accepting skipped protected-route, admin-route, and redaction tests.
