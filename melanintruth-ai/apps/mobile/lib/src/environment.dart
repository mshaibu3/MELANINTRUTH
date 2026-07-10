import 'package:flutter/foundation.dart';

import 'gateway.dart';

class ConfigurationException implements Exception {
  const ConfigurationException(this.message);

  final String message;

  @override
  String toString() => message;
}

class MobileEnvironment {
  const MobileEnvironment({
    required this.apiBaseUrl,
    required this.releaseMode,
  });

  factory MobileEnvironment.fromCompileTime({bool? releaseMode}) {
    return MobileEnvironment(
      apiBaseUrl: const String.fromEnvironment('MELANINTRUTH_API_BASE_URL'),
      releaseMode: releaseMode ?? kReleaseMode,
    );
  }

  final String apiBaseUrl;
  final bool releaseMode;

  MelaninTruthGateway createGateway() {
    final baseUrl = apiBaseUrl.trim();
    if (baseUrl.isEmpty) {
      if (releaseMode) {
        throw const ConfigurationException(
          'This release build is missing MELANINTRUTH_API_BASE_URL and cannot start analysis safely.',
        );
      }
      return const LocalPreviewGateway();
    }

    final uri = Uri.tryParse(baseUrl);
    if (uri == null || !uri.hasScheme || uri.host.isEmpty) {
      throw const ConfigurationException(
        'MELANINTRUTH_API_BASE_URL must be a valid absolute URL.',
      );
    }
    if (releaseMode && uri.scheme != 'https') {
      throw const ConfigurationException(
        'Release builds require an HTTPS MELANINTRUTH_API_BASE_URL.',
      );
    }

    return HttpMelaninTruthGateway(baseUrl: baseUrl);
  }
}
