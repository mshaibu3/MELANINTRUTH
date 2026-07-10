enum TelemetryEvent {
  sessionEstablished,
  sessionRestoreCompleted,
  captureRequested,
  uploadAttempted,
  uploadCompleted,
  analysisCompleted,
  privacyDeletionCompleted,
}

const _allowedFields = <String>{
  'attempt',
  'outcome',
  'status_class',
  'stage',
};

class TelemetryRecord {
  TelemetryRecord(this.event, [Map<String, Object> fields = const {}])
      : fields = Map.unmodifiable(fields) {
    for (final entry in fields.entries) {
      if (!_allowedFields.contains(entry.key)) {
        throw ArgumentError.value(
          entry.key,
          'fields',
          'Telemetry field is not allow-listed.',
        );
      }
      final value = entry.value;
      if (value is int) {
        if (entry.key != 'attempt' || value < 1 || value > 10) {
          throw ArgumentError.value(value, entry.key, 'Invalid telemetry value.');
        }
        continue;
      }
      if (value is! String ||
          value.length > 32 ||
          !RegExp(r'^[a-z0-9_-]+$').hasMatch(value)) {
        throw ArgumentError.value(value, entry.key, 'Invalid telemetry value.');
      }
    }
  }

  final TelemetryEvent event;
  final Map<String, Object> fields;
}

abstract interface class TelemetrySink {
  void record(TelemetryRecord record);
}

class NoopTelemetrySink implements TelemetrySink {
  const NoopTelemetrySink();

  @override
  void record(TelemetryRecord record) {}
}

class MemoryTelemetrySink implements TelemetrySink {
  final records = <TelemetryRecord>[];

  @override
  void record(TelemetryRecord record) => records.add(record);
}
