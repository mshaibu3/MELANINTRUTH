import 'dart:convert';
import 'dart:math' as math;

import 'package:http/http.dart' as http;

import 'constants.dart';
import 'models.dart';

abstract interface class MelaninTruthGateway {
  Future<AuthSession> signIn({
    required String email,
    required String password,
  });

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
      throw const GatewayException('Password must contain at least 12 characters.');
    }
    return const AuthSession(
      accessToken: 'memory-only-preview-token',
      sessionId: 'preview-session',
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
    final confidence = math.min(
      0.95,
      0.72 + (assessment.captureQuality * 0.15) +
          (assessment.lightingQuality * 0.08),
    );
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
  })  : baseUrl = baseUrl.replaceFirst(RegExp(r'/$'), ''),
        _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

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
    final body = _decode(response);
    final error = body['error'];
    final message = error is Map<String, dynamic>
        ? error['message']?.toString()
        : null;
    throw GatewayException(message ?? 'The API request failed.');
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
    final body = _decode(response);
    return AuthSession(
      accessToken: body['access_token'].toString(),
      sessionId: body['session_id'].toString(),
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
  }) {
    throw const GatewayException(
      'Secure camera-byte upload is not configured for this build. Capture telemetry is available, but the app will not fabricate an image upload.',
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
  }
}
