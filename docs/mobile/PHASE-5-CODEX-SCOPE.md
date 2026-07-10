# Phase 5 Codex Scope

This branch implements the production-integration layer for the existing consent-first Flutter application.

Included:

* native camera selection;
* secure refresh-session persistence;
* refresh rotation and consent revalidation;
* SHA-256 capture metadata;
* signed HTTPS upload transport;
* bounded idempotent upload retry;
* governed analysis response parsing;
* privacy-deletion session clearing;
* mobile gateway and controller tests;
* Phase 5 roadmap, architecture, and acceptance criteria.

Excluded from this pull request:

* Android/iOS generated platform projects;
* application signing and store entitlements;
* physical-device and device-farm evidence;
* production release claims.
