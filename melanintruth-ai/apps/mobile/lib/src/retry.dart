import 'dart:async';
import 'dart:io';

import 'package:http/http.dart' as http;

typedef DelayFunction = Future<void> Function(Duration duration);

class RetryPolicy {
  RetryPolicy({
    this.maxAttempts = 3,
    this.baseDelay = const Duration(milliseconds: 250),
    DelayFunction? delay,
  }) : _delay = delay ?? Future<void>.delayed;

  final int maxAttempts;
  final Duration baseDelay;
  final DelayFunction _delay;

  Future<http.Response> execute(
    Future<http.Response> Function() operation,
  ) async {
    Object? lastError;
    for (var attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        final response = await operation();
        if (!_isRetryableStatus(response.statusCode) ||
            attempt == maxAttempts) {
          return response;
        }
      } on SocketException catch (error) {
        lastError = error;
        if (attempt == maxAttempts) {
          rethrow;
        }
      } on http.ClientException catch (error) {
        lastError = error;
        if (attempt == maxAttempts) {
          rethrow;
        }
      } on TimeoutException catch (error) {
        lastError = error;
        if (attempt == maxAttempts) {
          rethrow;
        }
      }
      await _delay(baseDelay * attempt);
    }
    throw StateError('Retry loop exhausted: $lastError');
  }

  bool _isRetryableStatus(int statusCode) =>
      statusCode == 408 || statusCode == 429 || statusCode >= 500;
}
