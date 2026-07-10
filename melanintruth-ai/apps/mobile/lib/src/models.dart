import 'constants.dart';

enum MobileStage {
  welcome,
  consent,
  signIn,
  home,
  capture,
  quality,
  result,
  privacy,
}

enum CaptureQuality {
  unknown,
  acceptable,
  tooDark,
  tooBright,
  unstable,
}

class AuthSession {
  const AuthSession({
    required this.accessToken,
    required this.sessionId,
  });

  final String accessToken;
  final String sessionId;
}

class CaptureAssessment {
  const CaptureAssessment({
    required this.quality,
    required this.brightness,
    required this.stability,
    required this.lightingQuality,
    required this.captureQuality,
    required this.guidance,
  });

  final CaptureQuality quality;
  final double brightness;
  final double stability;
  final double lightingQuality;
  final double captureQuality;
  final String guidance;

  bool get isAcceptable => quality == CaptureQuality.acceptable;
}

class AnalysisResult {
  const AnalysisResult({
    required this.confidence,
    required this.uncertainty,
    required this.lightingQuality,
    required this.captureQuality,
    required this.explanation,
    this.limitationWarning = scientificLimitation,
  });

  final double confidence;
  final double uncertainty;
  final double lightingQuality;
  final double captureQuality;
  final String explanation;
  final String limitationWarning;
}

class MobileState {
  const MobileState({
    this.stage = MobileStage.welcome,
    this.imageProcessingConsent = false,
    this.cloudProcessingConsent = false,
    this.modelImprovementConsent = false,
    this.signedIn = false,
    this.brightness = 0.55,
    this.stability = 0.90,
    this.assessment,
    this.result,
    this.loading = false,
    this.notice,
    this.error,
  });

  final MobileStage stage;
  final bool imageProcessingConsent;
  final bool cloudProcessingConsent;
  final bool modelImprovementConsent;
  final bool signedIn;
  final double brightness;
  final double stability;
  final CaptureAssessment? assessment;
  final AnalysisResult? result;
  final bool loading;
  final String? notice;
  final String? error;

  bool get requiredConsentGranted =>
      imageProcessingConsent && cloudProcessingConsent;

  MobileState copyWith({
    MobileStage? stage,
    bool? imageProcessingConsent,
    bool? cloudProcessingConsent,
    bool? modelImprovementConsent,
    bool? signedIn,
    double? brightness,
    double? stability,
    CaptureAssessment? assessment,
    AnalysisResult? result,
    bool? loading,
    String? notice,
    String? error,
    bool clearAssessment = false,
    bool clearResult = false,
    bool clearNotice = false,
    bool clearError = false,
  }) {
    return MobileState(
      stage: stage ?? this.stage,
      imageProcessingConsent:
          imageProcessingConsent ?? this.imageProcessingConsent,
      cloudProcessingConsent:
          cloudProcessingConsent ?? this.cloudProcessingConsent,
      modelImprovementConsent:
          modelImprovementConsent ?? this.modelImprovementConsent,
      signedIn: signedIn ?? this.signedIn,
      brightness: brightness ?? this.brightness,
      stability: stability ?? this.stability,
      assessment: clearAssessment ? null : (assessment ?? this.assessment),
      result: clearResult ? null : (result ?? this.result),
      loading: loading ?? this.loading,
      notice: clearNotice ? null : (notice ?? this.notice),
      error: clearError ? null : (error ?? this.error),
    );
  }
}
