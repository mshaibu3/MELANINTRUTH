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

class _CaptureSource implements CaptureSource {
  _CaptureSource(this.image);

  final CapturedImage image;

  @override
  Future<CapturedImage> capture() async => image;
}

void main() {
  test('refreshes an expired upload ticket before transmitting bytes', () async {
    final capture = CapturedImage(
      bytes: Uint8List.fromList(<int>[1, 2, 3]),
      contentType: 'image/jpeg',
      fileName: 'capture.jpg',
    );
    var ticketRequests = 0;
    var putRequests = 0;
    final client = MockClient((request) async {
      if (request.url.path == '/images/upload-request') {
        ticketRequests += 1;
        return http.Response(
          jsonEncode({
            'upload_id': 'upload-$ticketRequests',
            'upload_url': 'https://uploads.example.com/object-$ticketRequests',
            'checksum_sha256': capture.checksumSha256,
            'expires_at': ticketRequests == 1
                ? '2000-01-01T00:00:00Z'
                : '2099-01-01T00:00:00Z',
            'idempotency_key': 'server-key-$ticketRequests-abcdefghijklmnop',
          }),
          201,
        );
      }
      if (request.url.host == 'uploads.example.com') {
        putRequests += 1;
        expect(request.url.path, '/object-2');
        return http.Response('', 200);
      }
      if (request.url.path == '/images/upload-complete') {
        final body = jsonDecode(request.body) as Map<String, dynamic>;
        expect(body['upload_id'], 'upload-2');
        expect(
          body['idempotency_key'],
          'server-key-2-abcdefghijklmnop',
        );
        return http.Response(
          jsonEncode({'image_id': 'image-1', 'status': 'uploaded'}),
          201,
        );
      }
      if (request.url.path == '/analysis/jobs') {
        return http.Response(
          jsonEncode({
            'confidence_score': 0.8,
            'uncertainty_score': 0.2,
            'lighting_quality_score': 0.9,
            'capture_quality_score': 0.9,
            'result': {'explanation': 'Governed analysis completed.'},
          }),
          201,
        );
      }
      throw StateError('Unexpected request: ${request.method} ${request.url}');
    });
    final gateway = HttpMelaninTruthGateway(
      baseUrl: 'https://api.example.com',
      client: client,
      captureSource: _CaptureSource(capture),
      sessionStore: MemorySessionStore(),
      uploadRetryPolicy: RetryPolicy(maxAttempts: 1, delay: (_) async {}),
    );

    await gateway.analyse(
      session: const AuthSession(
        accessToken: 'access',
        sessionId: 'session',
        refreshToken: 'refresh',
      ),
      assessment: const CaptureAssessment(
        quality: CaptureQuality.acceptable,
        brightness: 0.5,
        stability: 0.9,
        lightingQuality: 0.9,
        captureQuality: 0.9,
        guidance: 'acceptable',
      ),
    );

    expect(ticketRequests, 2);
    expect(putRequests, 1);
  });
}
