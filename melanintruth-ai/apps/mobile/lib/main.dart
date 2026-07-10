import 'package:flutter/material.dart';

import 'src/app.dart';
import 'src/environment.dart';
import 'src/gateway.dart';

export 'src/app.dart' show MelaninTruthApp;
export 'src/gateway.dart' show LocalPreviewGateway, MelaninTruthGateway;

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    final gateway = MobileEnvironment.fromCompileTime().createGateway();
    runApp(MelaninTruthApp(gateway: gateway));
  } on ConfigurationException catch (error) {
    runApp(_ConfigurationFailureApp(message: error.message));
  }
}

class _ConfigurationFailureApp extends StatelessWidget {
  const _ConfigurationFailureApp({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: Scaffold(
        body: SafeArea(
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.security_outlined, size: 48),
                  const SizedBox(height: 16),
                  const Text(
                    'Secure configuration required',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 12),
                  Text(message, textAlign: TextAlign.center),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
