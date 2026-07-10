import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melanintruth_mobile/src/controller.dart';
import 'package:melanintruth_mobile/src/models.dart';

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
