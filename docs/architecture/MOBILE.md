# Mobile Architecture

## Purpose

The Flutter application provides consent-first access to governed visible skin appearance analysis for melanin-rich skin. It reports estimates under standardised lighting assumptions and must never claim exact biological melanin measurement.

The application must never implement beauty filtering, whitening, lightening, smoothing, reshaping, identity alteration, or race inference.

## Phase 4 structure

The mobile implementation is organised under `melanintruth-ai/apps/mobile/lib/src/`:

* `constants.dart` contains the exact scientific limitation, safety promise, and privacy language shared across screens.
* `models.dart` defines immutable mobile stages, consent state, capture-quality assessment, authentication session metadata, and governed analysis results.
* `gateway.dart` defines the backend boundary. `LocalPreviewGateway` supports deterministic tests and safe UI demonstration. `HttpMelaninTruthGateway` supports authenticated login, consent, export, and deletion requests.
* `controller.dart` uses Riverpod to enforce navigation and state transitions. Required consent precedes sign-in; sign-in precedes capture; acceptable capture quality precedes analysis.
* `app.dart` provides the Material 3 user experience for onboarding, consent, sign-in, home, guided capture, quality review, results, and privacy controls.

## Security model

* Access tokens and session identifiers remain in memory only in the Phase 4 foundation.
* Tokens, passwords, raw image bytes, and raw storage paths must never be logged.
* The HTTP gateway sends bearer credentials only in the `Authorization` header.
* The application does not persist credentials until a platform secure-storage adapter and associated threat review are implemented.
* Deletion requests clear the local session and consent state immediately after the backend request succeeds.

## Consent model

Image-processing and cloud-processing consent are represented separately and are required for the current analysis workflow. Model-improvement consent is a separate optional choice and is off by default.

No image may be used for training unless the optional model-improvement purpose has been explicitly granted. Withdrawing or deleting data must prevent further processing.

## Capture-quality model

The Phase 4 foundation evaluates capture telemetry before analysis:

* brightness below `0.30` is rejected as underexposed;
* brightness above `0.78` is rejected as overexposed;
* stability below `0.75` is rejected as unstable;
* acceptable captures receive lighting-quality and capture-quality scores.

The current UI uses deterministic telemetry controls because native camera-byte transport is not yet connected. The production HTTP gateway deliberately refuses to fabricate an image upload when secure camera transport is unavailable.

## Result contract

Every displayed analysis result includes:

* confidence;
* uncertainty;
* lighting quality;
* capture quality;
* a plain-language explanation;
* the exact scientific limitation;
* explicit confirmation that no filter was applied and identity/texture were preserved.

## Privacy controls

The mobile privacy screen exposes:

* data-export requests;
* data-deletion requests;
* the no-raw-image-logging rule;
* the separate optional model-improvement consent rule.

## Verification

`.github/workflows/mobile-ci.yml` installs Flutter dependencies, performs static analysis, executes widget and controller tests, and uploads coverage. Phase 4 is not accepted until this workflow passes on the target `main` commit.
