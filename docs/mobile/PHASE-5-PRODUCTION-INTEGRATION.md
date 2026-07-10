# Phase 5 Mobile Production Integration

Phase 5 connects the Flutter application to the existing governed backend image lifecycle. It does not change the scientific limitation or permit beautification, whitening, smoothing, reshaping, or identity alteration.

## Runtime sequence

1. The user grants image-processing and cloud-processing consent and signs in.
2. The access token remains in memory. The refresh token and session ID are written through platform secure storage.
3. Before a stored session is restored, the app rotates the refresh token and reads current server-side consent records.
4. The existing capture-quality gate must pass before native camera access is requested.
5. The platform camera picker returns JPEG or PNG bytes. Cancellation, denial, empty files, unsupported formats, and files over 10 MB fail closed.
6. The app computes a SHA-256 checksum locally.
7. The app requests a signed upload URL from `/images/upload-request`.
8. The app requires the signed URL to use HTTPS and uploads the original bytes with content type and checksum headers.
9. Only this binary PUT is automatically retried because it is idempotent. State-creating API calls are not automatically replayed.
10. The app calls `/images/upload-complete`, then `/analysis/jobs` with the returned image ID.
11. Confidence, uncertainty, lighting quality, capture quality, explanation, and scientific limitation are rendered from the governed service response.

## Security and privacy properties

* Raw image bytes are never logged or persisted by the mobile application.
* Passwords and access tokens are never written to secure storage or logs.
* Refresh-session material is cleared after invalid refresh and privacy deletion.
* Non-local production API endpoints must use HTTPS.
* Signed upload URLs must always use HTTPS.
* Model-improvement consent remains separate, optional, and off by default.
* Restored sessions are rejected unless required consent is still active on the server.

## Retry policy

Only the signed binary PUT is retried. The retry policy is bounded to three attempts by default and handles network transport errors, timeouts, HTTP 408, HTTP 429, and HTTP 5xx responses. Upload-request, upload-complete, consent, analysis, export, deletion, login, and refresh calls are not automatically replayed because they may create or rotate state.

## Native release boundary

The Dart integration uses `image_picker` and `flutter_secure_storage`, but this repository does not yet contain generated Android and iOS application projects. A production mobile release therefore still requires:

* generated and reviewed Android/iOS platform scaffolding;
* camera usage descriptions and platform permission declarations;
* application IDs, signing keys, entitlements, and store configuration;
* environment-specific HTTPS API configuration;
* physical-device accessibility, camera, cancellation, permission-denial, offline, export, deletion, and consent-withdrawal tests.

No production-store readiness claim should be made until that evidence is committed and CI/device-farm results are recorded.
