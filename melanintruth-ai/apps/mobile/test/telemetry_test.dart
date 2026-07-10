import 'package:flutter_test/flutter_test.dart';
import 'package:melanintruth_mobile/src/telemetry.dart';

void main() {
  test('accepts only bounded non-identifying telemetry fields', () {
    final record = TelemetryRecord(
      TelemetryEvent.uploadAttempted,
      const {'attempt': 2, 'stage': 'signed_put'},
    );

    expect(record.fields['attempt'], 2);
    expect(record.fields['stage'], 'signed_put');
  });

  test('rejects token, URL, checksum, and user identifier fields', () {
    for (final field in const [
      'access_token',
      'refresh_token',
      'signed_url',
      'checksum_sha256',
      'user_id',
    ]) {
      expect(
        () => TelemetryRecord(
          TelemetryEvent.analysisCompleted,
          {field: 'secret'},
        ),
        throwsArgumentError,
      );
    }
  });

  test('rejects arbitrary URL-like telemetry values', () {
    expect(
      () => TelemetryRecord(
        TelemetryEvent.uploadCompleted,
        const {'outcome': 'https://uploads.example.com/object'},
      ),
      throwsArgumentError,
    );
  });

  test('memory sink stores validated records only', () {
    final sink = MemoryTelemetrySink();
    sink.record(
      TelemetryRecord(
        TelemetryEvent.sessionRestoreCompleted,
        const {'outcome': 'success'},
      ),
    );

    expect(sink.records, hasLength(1));
    expect(sink.records.single.event, TelemetryEvent.sessionRestoreCompleted);
  });
}
