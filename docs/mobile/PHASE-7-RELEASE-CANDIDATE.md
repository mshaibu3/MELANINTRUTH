# Phase 7 Release Candidate Controls

Phase 7 converts the Phase 6 unsigned native baseline into a protected release-candidate process. It does not publish to Google Play or App Store Connect automatically and it does not weaken the scientific, consent, identity-preservation, or privacy boundaries established in earlier phases.

## Protected signing

Signed builds run only through the `mobile-release` GitHub environment. That environment must require an authorised reviewer and must contain the platform credentials described by `.github/workflows/release-candidate.yml`.

Repository and pull-request workflows never receive signing secrets. They run policy validation only.

### Android credentials

* `ANDROID_KEYSTORE_BASE64`
* `ANDROID_KEYSTORE_PASSWORD`
* `ANDROID_KEY_ALIAS`
* `ANDROID_KEY_PASSWORD`

### iOS credentials

* `IOS_CERTIFICATE_P12_BASE64`
* `IOS_CERTIFICATE_PASSWORD`
* `IOS_PROVISIONING_PROFILE_BASE64`
* `IOS_KEYCHAIN_PASSWORD`
* `APPLE_TEAM_ID`

No credential, keystore, certificate, provisioning profile, password, signed upload URL, access token, refresh token, image checksum, or raw image data may be committed or printed.

## Upload reliability contract

The API issues a unique upload ID, an expiry timestamp, and a server-generated idempotency key. The mobile client must:

1. validate that the signed URL uses HTTPS;
2. request a fresh ticket when the current ticket is already expired or too close to expiry;
3. retry only the idempotent binary PUT;
4. send the upload ID and server idempotency key when completing the upload;
5. treat completion replay as success when the API returns the original image ID;
6. never retry analysis creation automatically.

Upload completion is atomic within the API process. A successful completion removes
the live ticket and retains only a hashed idempotency key plus the minimum metadata
needed for replay for one hour. Completed requests replay the original image ID even
after the five-minute upload ticket expires. Expired tickets and replay records are
removed opportunistically, and revoked image-processing consent blocks both first-time
completion and replay.

## Privacy and store declarations

* `ios/Runner/PrivacyInfo.xcprivacy` declares linked email and photo/video collection for app functionality and no tracking.
* `docs/mobile/google-play-data-safety.json` is the machine-readable source for the Google Play data-safety declaration.
* The application continues to expose account/data deletion and export controls.
* The product must not claim exact biological melanin measurement, beautification, whitening, lightening, smoothing, reshaping, or identity alteration.

## Real-device evidence

`docs/mobile/phase7-device-test-matrix.json` defines the required Android and iOS scenarios and evidence fields. Emulator success is not a substitute for physical or managed-device evidence.

Phase 7 code acceptance proves that the signing and evidence processes fail closed. Store release approval remains blocked until every required device scenario has a passing evidence record for the exact release-candidate commit.

## Release approval record

A release candidate may be promoted only when all of the following are recorded:

* exact Git commit and version/build number;
* successful `ci`, `api-integration`, `mobile-ci`, `mobile-native-ci`, and `release-candidate-policy` runs;
* successful signed Android and iOS build jobs from the protected environment;
* passing device evidence for every required matrix scenario;
* privacy and data-safety declarations reviewed against actual runtime behavior;
* scientific-governance approval;
* security and privacy approval;
* named release approver and UTC approval timestamp.

Until those external records exist, the correct state is `release_candidate_controls_ready`, not `store_ready` or `released`.
