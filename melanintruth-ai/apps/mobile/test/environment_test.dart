import 'package:flutter_test/flutter_test.dart';
import 'package:melanintruth_mobile/src/environment.dart';
import 'package:melanintruth_mobile/src/gateway.dart';

void main() {
  test('development without an API URL uses the local preview gateway', () {
    const environment = MobileEnvironment(apiBaseUrl: '', releaseMode: false);

    expect(environment.createGateway(), isA<LocalPreviewGateway>());
  });

  test('release without an API URL fails closed', () {
    const environment = MobileEnvironment(apiBaseUrl: '', releaseMode: true);

    expect(environment.createGateway, throwsA(isA<ConfigurationException>()));
  });

  test('release requires an HTTPS API URL', () {
    const environment = MobileEnvironment(
      apiBaseUrl: 'http://api.example.com',
      releaseMode: true,
    );

    expect(environment.createGateway, throwsA(isA<ConfigurationException>()));
  });

  test('release accepts a configured HTTPS gateway', () {
    const environment = MobileEnvironment(
      apiBaseUrl: 'https://api.example.com',
      releaseMode: true,
    );

    expect(environment.createGateway(), isA<HttpMelaninTruthGateway>());
  });
}
