# Phase 6 Native Release Hardening

Phase 6 converts the Phase 5 Flutter package into committed Android and iOS projects with reproducible native release verification. It preserves the scientific limitation, consent requirements, identity-preservation controls, and privacy guarantees established in earlier phases.

## Native identities

Both platforms use the production identity `com.hakilixlabs.melanintruth`.

* Android minimum SDK: 23.
* iOS minimum deployment target: 13.0.
* Android application backups and cleartext traffic are disabled.
* iOS arbitrary network loads are disabled.
* Camera use is declared explicitly on both platforms.

## Release configuration

`MELANINTRUTH_API_BASE_URL` is a compile-time setting. Development builds may use the local preview gateway when it is absent. Release builds fail closed and display a configuration error instead of silently entering preview mode. Release endpoints must use HTTPS.

## Signing boundary

Android release signing is optional during unsigned CI builds and is loaded only from the ignored `android/key.properties` file. The generated debug-key fallback has been removed. Real keystores and secrets must be supplied through a protected release environment.

iOS CI uses `--no-codesign`. Distribution certificates, provisioning profiles, entitlements, and App Store Connect configuration are intentionally outside the unsigned verification workflow.

## Privacy-safe telemetry

The mobile telemetry schema allows only coarse lifecycle fields:

* retry attempt number;
* outcome class;
* HTTP status class;
* lifecycle stage.

The schema rejects arbitrary fields and values, including access tokens, refresh tokens, signed URLs, checksums, raw bytes, and user identifiers. The default sink is a no-op; no external telemetry vendor is enabled by this phase.

## Automated evidence

`mobile-ci` verifies formatting, analysis, and unit/widget/controller/gateway tests.

`mobile-native-ci` verifies:

1. committed permission, identity, signing, transport, backup, and environment configuration;
2. an unsigned Android release app bundle;
3. an unsigned iOS release application;
4. first-run scientific disclosure, disabled consent continuation, labelled controls, and Android tap-target guidance on an emulator.

The existing backend `ci` and PostgreSQL `api-integration` gates remain mandatory.

## Unresolved store-release evidence

Phase 6 is not a store-release approval. The following evidence remains required:

* protected production signing and notarised/provisioned builds;
* final store entitlements and privacy declarations;
* final icon, launch, screenshots, and listing assets;
* physical-device camera capture, cancellation, permission denial, and offline recovery;
* consent withdrawal, export, and deletion on physical or managed devices;
* accessibility review across representative Android and iOS devices;
* release-candidate security and governance approval.
