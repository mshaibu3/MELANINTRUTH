# MelaninTruth Mobile

Consent-first Flutter application for governed visible skin-appearance analysis. The application does not claim exact biological melanin measurement and does not provide whitening, lightening, smoothing, reshaping, or identity-changing effects.

## Development

```bash
flutter pub get
flutter run
```

A development build without `MELANINTRUTH_API_BASE_URL` uses the local preview gateway. Release builds fail closed instead of entering preview mode.

## Configured builds

```bash
flutter run \
  --dart-define=MELANINTRUTH_API_BASE_URL=https://api.example.com
```

Production endpoints must use HTTPS.

## Verification

```bash
dart format --output=none --set-exit-if-changed lib test integration_test
flutter analyze
flutter test
python tool/verify_native_config.py
```

The `mobile-native-ci` workflow also builds unsigned Android and iOS release artifacts and runs the consent/accessibility smoke test on an Android emulator.

## Android signing

Copy `android/key.properties.example` to `android/key.properties` and provide the protected release-keystore values locally or through the release environment. Never commit the real properties file, keystore, passwords, or aliases.

The committed Gradle configuration does not fall back to debug signing for release builds.

## Release boundary

The committed native projects support reproducible unsigned release builds. Store submission still requires protected signing credentials, store entitlements, final production endpoint configuration, privacy declarations, approved branding assets, physical-device camera and permission testing, accessibility review, and release governance approval.
