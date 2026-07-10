import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:melanintruth_mobile/src/capture.dart';
import 'package:melanintruth_mobile/src/gateway.dart';
import 'package:melanintruth_mobile/src/models.dart';
import 'package:melanintruth_mobile/src/retry.dart';
import 'package:melanintruth_mobile/src/session_store.dart';

class _FakeCaptureSource implements CaptureSource {
  _FakeCaptureSource(this.capture);

  final CapturedImage capture;

  @override
  Future<CapturedImage> capture() async => capture;
}

const _session = AuthSession(
  accessToken: 'access-token',
  sessionId: 'session-1',
  refreshToken: 'refresh-token',
);

const _assessment = CaptureAssessment(
  quality: CaptureQuality.acceptable,
  brightness: 0.55,
  stability: 0.9,
  lightingQuality: 1,
  captureQuality: 0.9,
  guidance: 'acceptable',
);

void main() {
  test('runs signed upload and governed analysis with bounded PUT retry',
      () async {
    final bytes = Uint8List.fromList(<int>[1, 2, 3, 4, 5]);
    final capture = CapturedImage(
      bytes: bytes,
      contentType: 'image/jpeg',
      fileName: 'capture.jpg',
    );
    var uploadAttempts = 0;
    final paths = <String>[];

    final client = MockClient((request) async {
      paths.add('${request.method} ${request.url.path}');
      if (request.url.host == 'uploads.example.com') {
        uploadAttempts += 1;
        expect(request.method, 'PUT');
        expect(request.headers['content-type'], 'image/jpeg');
        expect(request.headers['x-content-sha256'], capture.checksumSha256);
        expect(request.bodyBytes, bytes);
        return http.Response('', uploadAttempts == 1 ? 503 : 200);
      }
      if (request.url.path == '/images/upload-request') {
        final body = jsonDecode(request.body) as Map<String, dynamic>;
        expect(body['checksum_sha256'], capture.checksumSha256);
        expect(body['size_bytes'], bytes.length);
        return http.Response(
          jsonEncode({'upload_url': 'https://uploads.example.com/object'}),
          201,
        );
      }
      if (request.url.path == '/images/upload-complete') {
        return http.Response(
          jsonEncode({'image_id': 'image-1', 'status': 'uploaded'}),
          201,
        );
      }
      if (request.url.path == '/analysis/jobs') {
        final body = jsonDecode(request.body) as Map<String, dynamic>;
        expect(body, {'image_id': 'image-1', 'cloud': true});
        return http.Response(
          jsonEncode({
            'confidence_score': 0.88,
            'uncertainty_score': 0.12,
            'lighting_quality_score': 0.91,
            'capture_quality_score': 0.89,
            'result': {'explanation': 'Governed analysis completed.'},
            'limitation_warning': 'Scientific limitation.',
          }),
          201,
        );
      }
      throw StateError('Unexpected request: ${request.method} ${request.url}');
    });

    final gateway = HttpMelaninTruthGateway(
      baseUrl: 'https://api.example.com',
      client: client,
      captureSource: _FakeCaptureSource(capture),
      sessionStore: MemorySessionStore(),
      uploadRetryPolicy: RetryPolicy(
        maxAttempts: 3,
        delay: (_) async {},
      ),
    );

    final result = await gateway.analyse(
      session: _session,
      assessment: _assessment,
    );

    expect(uploadAttempts, 2);
    expect(result.confidence, 0.88);
    expect(result.uncertainty, 0.12);
    expect(result.explanation, 'Governed analysis completed.');
    expect(paths, [
      'POST /images/upload-request',
      'PUT /object',
      'PUT /object',
      'POST /images/upload-complete',
      'POST /analysis/jobs',
    ]);
  });

  test('rotates a stored refresh session and revalidates consent', () async {
    final store = MemorySessionStore();
    await store.save(
      const StoredSession(
        sessionId: 'stored-session',
        refreshToken: 'stored-refresh',
      ),
    );
    final client = MockClient((request) async {
      if (request.url.path == '/auth/refresh') {
        final body = jsonDecode(request.body) as Map<String, dynamic>;
        expect(body['session_id'], 'stored-session');
        expect(body['refresh_token'], 'stored-refresh');
        return http.Response(
          jsonEncode({
            'access_token': 'new-access',
            'refresh_token': 'new-refresh',
            'session_id': 'new-session',
          }),
          200,
        );
      }
      if (request.url.path == '/consent') {
        expect(request.headers['authorization'], 'Bearer new-access');
        return http.Response(
          jsonEncode({
            'consent': [
              {
                'purpose': 'image_processing',
                'granted': true,
                'revoked': false,
              },
              {
                'purpose': 'cloud_processing',
                'granted': true,
                'revoked': false,
              },
            ],
          }),
          200,
        );
      }
      throw StateError('Unexpected request: ${request.url}');
    });
    final gateway = HttpMelaninTruthGateway(
      baseUrl: 'https://api.example.com',
      client: client,
      captureSource: _FakeCaptureSource(
        CapturedImage(
          bytes: Uint8List.fromList(<int>[1]),
          contentType: 'image/jpeg',
          fileName: 'capture.jpg',
        ),
      ),
      sessionStore: store,
    );

    final restored = await gateway.restoreSession();
    expect(restored?.accessToken, 'new-access');
    expect(restored?.refreshToken, 'new-refresh');
    final consent = await gateway.consentSnapshot(session: restored!);
    expect(consent.requiredConsentGranted, isTrue);

    final rotated = await store.read();
    expect(rotated?.sessionId, 'new-session');
    expect(rotated?.refreshToken, 'new-refresh');
  });

  test('deletion clears secure refresh-session material', () async {
    final store = MemorySessionStore();
    await store.save(
      const StoredSession(
          sessionId: 'session-1', refreshToken: 'refresh-token'),
    );
    final gateway = HttpMelaninTruthGateway(
      baseUrl: 'https://api.example.com',
      client: MockClient(
        (_) async => http.Response(jsonEncode({'status': 'completed'}), 202),
      ),
      captureSource: _FakeCaptureSource(
        CapturedImage(
          bytes: Uint8List.fromList(<int>[1]),
          contentType: 'image/jpeg',
          fileName: 'capture.jpg',
        ),
      ),
      sessionStore: store,
    );

    await gateway.requestDataDeletion(session: _session);
    expect(await store.read(), isNull);
  });

  test('rejects non-HTTPS production API URLs', () {
    expect(
      () => HttpMelaninTruthGateway(baseUrl: 'http://api.example.com'),
      throwsA(isA<GatewayException>()),
    );
  });
}
