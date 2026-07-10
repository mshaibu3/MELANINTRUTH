import 'package:flutter/material.dart';

import 'src/app.dart';
import 'src/gateway.dart';

export 'src/app.dart' show MelaninTruthApp;
export 'src/gateway.dart' show LocalPreviewGateway, MelaninTruthGateway;

const _apiBaseUrl = String.fromEnvironment('MELANINTRUTH_API_BASE_URL');

void main() {
  final gateway = _apiBaseUrl.isEmpty
      ? const LocalPreviewGateway()
      : HttpMelaninTruthGateway(baseUrl: _apiBaseUrl);
  runApp(MelaninTruthApp(gateway: gateway));
}
