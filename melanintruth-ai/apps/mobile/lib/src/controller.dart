import 'dart:math' as math;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'gateway.dart';
import 'models.dart';

final gatewayProvider = Provider<MelaninTruthGateway>(
  (ref) => const LocalPreviewGateway(),
);

final mobileControllerProvider =
    NotifierProvider<MobileController, MobileState>(MobileController.new);

class MobileController extends Notifier<MobileState> {
  AuthSession? _session;

  MelaninTruthGateway get _gateway => ref.read(gatewayProvider);

  @override
  MobileState build() {
    Future<void>.microtask(_restoreSession);
    return const MobileState();
  }

  Future<void> _restoreSession() async {
    try {
      final session = await _gateway.restoreSession();
      if (session == null ||
          state.stage != MobileStage.welcome ||
          state.signedIn) {
        return;
      }
      final consent = await _gateway.consentSnapshot(session: session);
      if (!consent.requiredConsentGranted) {
        return;
      }
      _session = session;
      state = state.copyWith(
        signedIn: true,
        stage: MobileStage.home,
        imageProcessingConsent: consent.imageProcessing,
        cloudProcessingConsent: consent.cloudProcessing,
        modelImprovementConsent: consent.modelImprovement,
        notice: 'Secure session restored and consent revalidated.',
        clearError: true,
      );
    } on Object {
      // Startup must remain usable when secure storage or the network is unavailable.
    }
  }

  void continueFromWelcome() {
    state = state.copyWith(
      stage: MobileStage.consent,
      clearError: true,
      clearNotice: true,
    );
  }

  void setImageProcessingConsent(bool value) {
    state = state.copyWith(imageProcessingConsent: value, clearError: true);
  }

  void setCloudProcessingConsent(bool value) {
    state = state.copyWith(cloudProcessingConsent: value, clearError: true);
  }

  void setModelImprovementConsent(bool value) {
    state = state.copyWith(modelImprovementConsent: value);
  }

  void continueToSignIn() {
    if (!state.requiredConsentGranted) {
      state = state.copyWith(
        error:
            'Image-processing and cloud-processing consent are required for analysis.',
      );
      return;
    }
    state = state.copyWith(stage: MobileStage.signIn, clearError: true);
  }

  Future<void> signIn(String email, String password) async {
    state = state.copyWith(loading: true, clearError: true, clearNotice: true);
    try {
      final session = await _gateway.signIn(email: email, password: password);
      await _gateway.grantConsent(
        session: session,
        imageProcessing: state.imageProcessingConsent,
        cloudProcessing: state.cloudProcessingConsent,
        modelImprovement: state.modelImprovementConsent,
      );
      _session = session;
      state = state.copyWith(
        loading: false,
        signedIn: true,
        stage: MobileStage.home,
        notice:
            'Signed in. Access credentials remain in memory and refresh-session material uses secure platform storage.',
      );
    } on GatewayException catch (error) {
      state = state.copyWith(loading: false, error: error.message);
    } catch (_) {
      state = state.copyWith(
        loading: false,
        error: 'Unable to sign in safely. Try again.',
      );
    }
  }

  void startCapture() {
    if (!state.signedIn || _session == null) {
      state = state.copyWith(
        stage: MobileStage.signIn,
        error: 'Sign in before starting a capture.',
      );
      return;
    }
    state = state.copyWith(
      stage: MobileStage.capture,
      clearAssessment: true,
      clearResult: true,
      clearError: true,
      clearNotice: true,
    );
  }

  void updateBrightness(double value) {
    state = state.copyWith(brightness: value, clearError: true);
  }

  void updateStability(double value) {
    state = state.copyWith(stability: value, clearError: true);
  }

  void assessCapture() {
    final brightness = state.brightness;
    final stability = state.stability;

    late final CaptureQuality quality;
    late final String guidance;
    if (brightness < 0.30) {
      quality = CaptureQuality.tooDark;
      guidance = 'Move toward even indirect light and avoid deep shadow.';
    } else if (brightness > 0.78) {
      quality = CaptureQuality.tooBright;
      guidance = 'Move away from direct light and avoid highlights or glare.';
    } else if (stability < 0.75) {
      quality = CaptureQuality.unstable;
      guidance = 'Hold the device steady and keep the face centred.';
    } else {
      quality = CaptureQuality.acceptable;
      guidance =
          'Capture conditions are suitable. The production gateway will request camera permission before upload.';
    }

    final lightingQuality =
        (1 - ((brightness - 0.55).abs() / 0.55)).clamp(0.0, 1.0).toDouble();
    final captureQuality = math.min(lightingQuality, stability).toDouble();
    final assessment = CaptureAssessment(
      quality: quality,
      brightness: brightness,
      stability: stability,
      lightingQuality: lightingQuality,
      captureQuality: captureQuality,
      guidance: guidance,
    );

    state = state.copyWith(
      stage: MobileStage.quality,
      assessment: assessment,
      clearError: true,
    );
  }

  void retakeCapture() {
    state = state.copyWith(
      stage: MobileStage.capture,
      clearAssessment: true,
      clearError: true,
    );
  }

  Future<void> analyseCapture() async {
    final session = _session;
    final assessment = state.assessment;
    if (session == null || assessment == null || !assessment.isAcceptable) {
      state = state.copyWith(error: 'A valid capture assessment is required.');
      return;
    }
    state = state.copyWith(loading: true, clearError: true);
    try {
      final result = await _gateway.analyse(
        session: session,
        assessment: assessment,
      );
      state = state.copyWith(
        loading: false,
        stage: MobileStage.result,
        result: result,
      );
    } on GatewayException catch (error) {
      state = state.copyWith(loading: false, error: error.message);
    } catch (_) {
      state = state.copyWith(
        loading: false,
        error: 'Analysis could not be completed safely.',
      );
    }
  }

  void openPrivacy() {
    state = state.copyWith(
      stage: MobileStage.privacy,
      clearError: true,
      clearNotice: true,
    );
  }

  void goHome() {
    state = state.copyWith(
      stage: MobileStage.home,
      clearError: true,
      clearNotice: true,
    );
  }

  Future<void> requestDataExport() async {
    final session = _session;
    if (session == null) {
      state = state.copyWith(error: 'Sign in before requesting an export.');
      return;
    }
    state = state.copyWith(loading: true, clearError: true);
    try {
      final requestId = await _gateway.requestDataExport(session: session);
      state = state.copyWith(
        loading: false,
        notice: 'Data export requested: $requestId',
      );
    } on GatewayException catch (error) {
      state = state.copyWith(loading: false, error: error.message);
    }
  }

  Future<void> requestDataDeletion() async {
    final session = _session;
    if (session == null) {
      state = state.copyWith(error: 'Sign in before requesting deletion.');
      return;
    }
    state = state.copyWith(loading: true, clearError: true);
    try {
      await _gateway.requestDataDeletion(session: session);
      _session = null;
      state = const MobileState(
        notice: 'Deletion requested. Local secure-session data was cleared.',
      );
    } on GatewayException catch (error) {
      state = state.copyWith(loading: false, error: error.message);
    }
  }
}
