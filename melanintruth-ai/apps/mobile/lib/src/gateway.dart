import 'dart:convert';
import 'dart:math' as math;

import 'package:http/http.dart' as http;

import 'capture.dart';
import 'models.dart';
import 'retry.dart';
import 'session_store.dart';
import 'telemetry.dart';

abstract interface class MelaninTruthGateway {
  Future<AuthSession> signIn({required String email, required String password});

  Future<AuthSession?> restoreSession();

  Future<ConsentSnapshot> consentSnapshot({required AuthSession session});

  Future<void> grantConsent({
    required AuthSession session,
    required bool imageProcessing,
    required bool cloudProcessing,
    required bool modelImprovement,
  });

  Future<AnalysisResult> analyse({
    required AuthSession session,
    required CaptureAssessment assessment,
  });

  Future<String> requestDataExport({required AuthSession session});

  Future<void> requestDataDeletion({required AuthSession session});
}

class GatewayException implements Exception {
  const GatewayException(this.message);

  final String message;

  @override
  String toString() => message;
}

class LocalPreviewGateway implements MelaninTruthGateway {
  const LocalPreviewGateway();

  @override
  Future<AuthSession> signIn({
    required String email,
    required String password,
  }) async {
    if (!email.contains('@')) {
      throw const GatewayException('Enter a valid email address.');
    }
    if (password.length < 12) {
      throw const GatewayException(
        'Password must contain at least 12 characters.',
      );
    }
    return const AuthSession(
      accessToken: 'memory-only-preview-token',
      sessionId: 'preview-session',
    );
  }

  @override
  Future<AuthSession?> restoreSession() async => null;

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

  @override
  Future<void> grantConsent({
    required AuthSession session,
    required bool imageProcessing,
    required bool cloudProcessing,
    required bool modelImprovement,
  }) async {
    if (!imageProcessing || !cloudProcessing) {
      throw const GatewayException(
        'Image-processing and cloud-processing consent are required for analysis.',
      );
    }
  }

  @override
  Future<AnalysisResult> analyse({
    required AuthSession session,
    required CaptureAssessment assessment,
  }) async {
    if (!assessment.isAcceptable) {
      throw const GatewayException('Retake the capture before analysis.');
    }
    final confidence = math
        .min(
          0.95,
          0.72 +
              (assessment.captureQuality * 0.15) +
              (assessment.lightingQuality * 0.08),
        )
        .toDouble();
    return AnalysisResult(
      confidence: confidence,
      uncertainty: 1 - confidence,
      lightingQuality: assessment.lightingQuality,
      captureQuality: assessment.captureQuality,
      explanation:
          'The preview combines capture stability and lighting quality. No beautification or identity-changing transformation is applied.',
    );
  }

  @override
  Future<String> requestDataExport({required AuthSession session}) async {
    return 'preview-export-request';
  }

  @override
  Future<void> requestDataDeletion({required AuthSession session}) async {}
}

class HttpMelaninTruthGateway implements MelaninTruthGateway {
  HttpMelaninTruthGateway({
    required String baseUrl,
    http.Client? client,
    CaptureSource? captureSource,
    SessionStore? sessionStore,
    RetryPolicy? uploadRetryPolicy,
    TelemetrySink? telemetry,
  }) : baseUrl = baseUrl.replaceFirst(RegExp(r'/$'), ''),
       _client = client ?? http.Client(),
       _captureSource = captureSource ?? ImagePickerCaptureSource(),
       _sessionStore = sessionStore ?? SecureSessionStore(),
       _uploadRetryPolicy = uploadRetryPolicy ?? RetryPolicy(),
       _telemetry = telemetry ?? const NoopTelemetrySink() {
    final uri = Uri.parse(this.baseUrl);
    final localDevelopmentHost =
        uri.host == 'localhost' ||
        uri.host == '127.0.0.1' ||
        uri.host == '10.0.2.2';
    if (uri.scheme != 'https' && !localDevelopmentHost) {
      throw const GatewayException(
        'The production API base URL must use HTTPS.',
      );
    }
  }

  final String baseUrl;
  final http.Client _client;
  final CaptureSource _captureSource;
  final SessionStore _sessionStore;
  final RetryPolicy _uploadRetryPolicy;
  final TelemetrySink _telemetry;

  Map<String, String> _headers([AuthSession? session]) => {
    'Content-Type': 'application/json',
    if (session != null) 'Authorization': 'Bearer ${session.accessToken}',
  };

  Map<String, dynamic> _decode(http.Response response) {
    final decoded = jsonDecode(response.body);
    if (decoded is! Map<String, dynamic>) {
      throw const GatewayException('The API returned an invalid response.');
    }
    return decoded;
  }

  void _expectSuccess(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return;
    }
    String? message;
    try {
      final body = _decode(response);
      final error = body['error'];
      message = error is Map<String, dynamic>
          ? error['message']?.toString()
          : null;
    } on Object {
      message = null;
    }
    throw GatewayException(message ?? 'The API request failed.');
  }

  AuthSession _sessionFromBody(Map<String, dynamic> body) {
    return AuthSession(
      accessToken: body['access_token'].toString(),
      sessionId: body['session_id'].toString(),
      refreshToken: body['refresh_token'].toString(),
    );
  }

  Future<void> _saveRefreshSession(AuthSession session) async {
    if (session.refreshToken.isEmpty) {
      return;
    }
    await _sessionStore.save(
      StoredSession(
        sessionId: session.sessionId,
        refreshToken: session.refreshToken,
      ),
    );
  }

  @override
  Future<AuthSession> signIn({
    required String email,
    required String password,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: _headers(),
      body: jsonEncode({
        'email': email.trim(),
        'password': password,
        'device_label': 'melanintruth-mobile',
      }),
    );
    _expectSuccess(response);
    final session = _sessionFromBody(_decode(response));
    await _saveRefreshSession(session);
    _telemetry.record(
      TelemetryRecord(TelemetryEvent.sessionEstablished, const {
        'outcome': 'success',
      }),
    );
    return session;
  }

  @override
  Future<AuthSession?> restoreSession() async {
    final stored = await _sessionStore.read();
    if (stored == null) {
      return null;
    }
    try {
      final response = await _client.post(
        Uri.parse('$baseUrl/auth/refresh'),
        headers: _headers(),
        body: jsonEncode({
          'session_id': stored.sessionId,
          'refresh_token': stored.refreshToken,
        }),
      );
      _expectSuccess(response);
      final session = _sessionFromBody(_decode(response));
      await _saveRefreshSession(session);
      _telemetry.record(
        TelemetryRecord(TelemetryEvent.sessionRestoreCompleted, const {
          'outcome': 'success',
        }),
      );
      return session;
    } on Object {
      await _sessionStore.clear();
      _telemetry.record(
        TelemetryRecord(TelemetryEvent.sessionRestoreCompleted, const {
          'outcome': 'failed',
        }),
      );
      return null;
    }
  }

  @override
  Future<ConsentSnapshot> consentSnapshot({
    required AuthSession session,
  }) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/consent'),
      headers: _headers(session),
    );
    _expectSuccess(response);
    final records = _decode(response)['consent'];
    final active = <String>{};
    if (records is List<dynamic>) {
      for (final item in records) {
        if (item is Map<String, dynamic> &&
            item['granted'] == true &&
            item['revoked'] != true) {
          active.add(item['purpose'].toString());
        }
      }
    }
    return ConsentSnapshot(
      imageProcessing: active.contains('image_processing'),
      cloudProcessing: active.contains('cloud_processing'),
      modelImprovement: active.contains('model_improvement'),
    );
  }

  @override
  Future<void> grantConsent({
    required AuthSession session,
    required bool imageProcessing,
    required bool cloudProcessing,
    required bool modelImprovement,
  }) async {
    final purposes = <String>[
      if (imageProcessing) 'image_processing',
      if (cloudProcessing) 'cloud_processing',
      if (modelImprovement) 'model_improvement',
    ];
    for (final purpose in purposes) {
      final response = await _client.post(
        Uri.parse('$baseUrl/consent'),
        headers: _headers(session),
        body: jsonEncode({'purpose': purpose, 'version': '2026-07'}),
      );
      _expectSuccess(response);
    }
  }

  @override
  Future<AnalysisResult> analyse({
    required AuthSession session,
    required CaptureAssessment assessment,
  }) async {
    if (!assessment.isAcceptable) {
      throw const GatewayException('Retake the capture before analysis.');
    }

    _telemetry.record(
      TelemetryRecord(TelemetryEvent.captureRequested, const {
        'stage': 'native_camera',
      }),
    );
    final capture = await _captureSource.capture();
    final metadata = {
      'content_type': capture.contentType,
      'size_bytes': capture.sizeBytes,
      'checksum_sha256': capture.checksumSha256,
    };

    final requestResponse = await _client.post(
      Uri.parse('$baseUrl/images/upload-request'),
      headers: _headers(session),
      body: jsonEncode(metadata),
    );
    _expectSuccess(requestResponse);
    final uploadUrl = _decode(requestResponse)['upload_url'].toString();
    final uploadUri = Uri.parse(uploadUrl);
    if (uploadUri.scheme != 'https') {
      throw const GatewayException('Signed image uploads must use HTTPS.');
    }

    final uploadResponse = await _uploadRetryPolicy.execute(
      () => _client.put(
        uploadUri,
        headers: {
          'Content-Type': capture.contentType,
          'X-Content-SHA256': capture.checksumSha256,
        },
        body: capture.bytes,
      ),
      onAttempt: (attempt) {
        _telemetry.record(
          TelemetryRecord(TelemetryEvent.uploadAttempted, {'attempt': attempt}),
        );
      },
    );
    _expectSuccess(uploadResponse);
    _telemetry.record(
      TelemetryRecord(TelemetryEvent.uploadCompleted, const {
        'status_class': 'success',
      }),
    );

    final completeResponse = await _client.post(
      Uri.parse('$baseUrl/images/upload-complete'),
      headers: _headers(session),
      body: jsonEncode(metadata),
    );
    _expectSuccess(completeResponse);
    final imageId = _decode(completeResponse)['image_id'].toString();

    final analysisResponse = await _client.post(
      Uri.parse('$baseUrl/analysis/jobs'),
      headers: _headers(session),
      body: jsonEncode({'image_id': imageId, 'cloud': true}),
    );
    _expectSuccess(analysisResponse);
    _telemetry.record(
      TelemetryRecord(TelemetryEvent.analysisCompleted, const {
        'outcome': 'success',
      }),
    );
    return _analysisResult(_decode(analysisResponse));
  }

  AnalysisResult _analysisResult(Map<String, dynamic> body) {
    final result = body['result'];
    final resultMap = result is Map<String, dynamic>
        ? result
        : <String, dynamic>{};
    double score(String key, [double fallback = 0]) {
      final value = body[key];
      return value is num ? value.toDouble() : fallback;
    }

    return AnalysisResult(
      confidence: score('confidence_score'),
      uncertainty: score('uncertainty_score'),
      lightingQuality: score('lighting_quality_score'),
      captureQuality: score('capture_quality_score'),
      explanation:
          resultMap['explanation']?.toString() ??
          'The governed service completed visible-appearance analysis without beautification or identity alteration.',
      limitationWarning:
          body['limitation_warning']?.toString() ??
          'This result is an estimate under standardised lighting assumptions.',
    );
  }

  @override
  Future<String> requestDataExport({required AuthSession session}) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/privacy/export'),
      headers: _headers(session),
    );
    _expectSuccess(response);
    return _decode(response)['request_id'].toString();
  }

  @override
  Future<void> requestDataDeletion({required AuthSession session}) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/privacy/delete'),
      headers: _headers(session),
    );
    _expectSuccess(response);
    await _sessionStore.clear();
    _telemetry.record(
      TelemetryRecord(TelemetryEvent.privacyDeletionCompleted, const {
        'outcome': 'success',
      }),
    );
  }
}
