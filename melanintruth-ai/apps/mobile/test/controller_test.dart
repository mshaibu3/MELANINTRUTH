import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melanintruth_mobile/src/controller.dart';
import 'package:melanintruth_mobile/src/gateway.dart';
import 'package:melanintruth_mobile/src/models.dart';

class _RestoringGateway extends LocalPreviewGateway {
  const _RestoringGateway();

  @override
  Future<AuthSession?> restoreSession() async {
    return const AuthSession(
      accessToken: 'restored-access',
      sessionId: 'restored-session',
      refreshToken: 'rotated-refresh',
    );
  }

  @override
  Future<ConsentSnapshot> consentSnapshot({
    required AuthSession session,
  }) async {
    return const ConsentSnapshot(
      imageProcessing: true,
      cloudProcessing: true,
      modelImprovement: false,
    );
  }
}

Future<void> _signIn(ProviderContainer container) async {
  final controller = container.read(mobileControllerProvider.notifier);
  controller.continueFromWelcome();
  controller.setImageProcessingConsent(true);
  controller.setCloudProcessingConsent(true);
  controller.continueToSignIn();
  await controller.signIn(
    'controller@example.com',
    'CorrectHorseBatteryStaple123!',
  );
}

void main() {
  test('restores secure session only after consent revalidation', () async {
    final container = ProviderContainer(
      overrides: [gatewayProvider.overrideWithValue(const _RestoringGateway())],
    );
    addTearDown(container.dispose);

    container.read(mobileControllerProvider);
    await Future<void>.delayed(Duration.zero);
    await Future<void>.delayed(Duration.zero);

    final state = container.read(mobileControllerProvider);
    expect(state.signedIn, isTrue);
    expect(state.stage, MobileStage.home);
    expect(state.requiredConsentGranted, isTrue);
    expect(state.modelImprovementConsent, isFalse);
  });

  test('rejects underexposed capture telemetry', () async {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    await _signIn(container);

    final controller = container.read(mobileControllerProvider.notifier);
    controller.startCapture();
    controller.updateBrightness(0.10);
    controller.assessCapture();

    final state = container.read(mobileControllerProvider);
    expect(state.stage, MobileStage.quality);
    expect(state.assessment?.quality, CaptureQuality.tooDark);
    expect(state.assessment?.isAcceptable, isFalse);
  });

  test('keeps model-improvement consent optional', () async {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    await _signIn(container);

    final state = container.read(mobileControllerProvider);
    expect(state.signedIn, isTrue);
    expect(state.modelImprovementConsent, isFalse);
    expect(state.requiredConsentGranted, isTrue);
  });

  test('deletion request clears the local session', () async {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    await _signIn(container);

    final controller = container.read(mobileControllerProvider.notifier);
    await controller.requestDataDeletion();

    final state = container.read(mobileControllerProvider);
    expect(state.stage, MobileStage.welcome);
    expect(state.signedIn, isFalse);
    expect(state.imageProcessingConsent, isFalse);
    expect(state.cloudProcessingConsent, isFalse);
  });
}
