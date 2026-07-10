import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'constants.dart';
import 'controller.dart';
import 'gateway.dart';
import 'models.dart';

class MelaninTruthApp extends StatelessWidget {
  const MelaninTruthApp({
    super.key,
    this.gateway = const LocalPreviewGateway(),
  });

  final MelaninTruthGateway gateway;

  @override
  Widget build(BuildContext context) {
    return ProviderScope(
      overrides: [gatewayProvider.overrideWithValue(gateway)],
      child: const _AppView(),
    );
  }
}

class _AppView extends ConsumerWidget {
  const _AppView();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(mobileControllerProvider);
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: appTitle,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF5A3B2E),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
        inputDecorationTheme: const InputDecorationTheme(
          border: OutlineInputBorder(),
        ),
      ),
      home: switch (state.stage) {
        MobileStage.welcome => const _WelcomeScreen(),
        MobileStage.consent => const _ConsentScreen(),
        MobileStage.signIn => const _SignInScreen(),
        MobileStage.home => const _HomeScreen(),
        MobileStage.capture => const _CaptureScreen(),
        MobileStage.quality => const _QualityScreen(),
        MobileStage.result => const _ResultScreen(),
        MobileStage.privacy => const _PrivacyScreen(),
      },
    );
  }
}

class _Shell extends StatelessWidget {
  const _Shell({
    required this.title,
    required this.state,
    required this.children,
    this.leading,
  });

  final String title;
  final MobileState state;
  final List<Widget> children;
  final Widget? leading;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(leading: leading, title: Text(title)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            if (state.error != null) ...[
              _StatusPanel(
                icon: Icons.error_outline,
                message: state.error!,
                isError: true,
              ),
              const SizedBox(height: 16),
            ],
            if (state.notice != null) ...[
              _StatusPanel(icon: Icons.info_outline, message: state.notice!),
              const SizedBox(height: 16),
            ],
            ...children,
          ],
        ),
      ),
    );
  }
}

class _StatusPanel extends StatelessWidget {
  const _StatusPanel({
    required this.icon,
    required this.message,
    this.isError = false,
  });

  final IconData icon;
  final String message;
  final bool isError;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Semantics(
      liveRegion: true,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isError ? colors.errorContainer : colors.secondaryContainer,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon),
            const SizedBox(width: 10),
            Expanded(child: Text(message)),
          ],
        ),
      ),
    );
  }
}

class _SafetyCard extends StatelessWidget {
  const _SafetyCard();

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Safety promise',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            const Text(safetyPromise),
          ],
        ),
      ),
    );
  }
}

class _WelcomeScreen extends ConsumerWidget {
  const _WelcomeScreen();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(mobileControllerProvider);
    final controller = ref.read(mobileControllerProvider.notifier);
    return _Shell(
      title: appTitle,
      state: state,
      children: [
        const Icon(Icons.face_retouching_off, size: 72),
        const SizedBox(height: 20),
        Text(
          appTagline,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 18),
        const Text(scientificLimitation, textAlign: TextAlign.center),
        const SizedBox(height: 20),
        const _SafetyCard(),
        const SizedBox(height: 12),
        const Card(
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Text(privacyNotice),
          ),
        ),
        const SizedBox(height: 24),
        FilledButton.icon(
          key: const Key('welcome_continue'),
          onPressed: controller.continueFromWelcome,
          icon: const Icon(Icons.arrow_forward),
          label: const Text('Continue'),
        ),
      ],
    );
  }
}

class _ConsentScreen extends ConsumerWidget {
  const _ConsentScreen();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(mobileControllerProvider);
    final controller = ref.read(mobileControllerProvider.notifier);
    return _Shell(
      title: 'Consent setup',
      state: state,
      children: [
        Text(
          'Choose how your data may be processed',
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: 8),
        const Text(
          'Required purposes are separate from the optional model-improvement choice. You can withdraw consent later.',
        ),
        const SizedBox(height: 16),
        SwitchListTile(
          key: const Key('image_consent'),
          value: state.imageProcessingConsent,
          onChanged: controller.setImageProcessingConsent,
          title: const Text('Image processing'),
          subtitle: const Text(
            'Required to assess capture quality and visible skin appearance.',
          ),
        ),
        SwitchListTile(
          key: const Key('cloud_consent'),
          value: state.cloudProcessingConsent,
          onChanged: controller.setCloudProcessingConsent,
          title: const Text('Cloud processing'),
          subtitle: const Text(
            'Required for the current server-backed analysis workflow.',
          ),
        ),
        SwitchListTile(
          key: const Key('model_consent'),
          value: state.modelImprovementConsent,
          onChanged: controller.setModelImprovementConsent,
          title: const Text('Model improvement — optional'),
          subtitle: const Text(
            'Off by default. Analysis remains available without this consent.',
          ),
        ),
        const SizedBox(height: 16),
        const _SafetyCard(),
        const SizedBox(height: 24),
        FilledButton(
          key: const Key('consent_continue'),
          onPressed: state.requiredConsentGranted
              ? controller.continueToSignIn
              : null,
          child: const Text('Continue to sign in'),
        ),
      ],
    );
  }
}

class _SignInScreen extends ConsumerStatefulWidget {
  const _SignInScreen();

  @override
  ConsumerState<_SignInScreen> createState() => _SignInScreenState();
}

class _SignInScreenState extends ConsumerState<_SignInScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(mobileControllerProvider);
    final controller = ref.read(mobileControllerProvider.notifier);
    return _Shell(
      title: 'Secure sign in',
      state: state,
      children: [
        Text(
          'Access your governed analysis workspace',
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: 8),
        const Text(
          'Access credentials remain in memory. Refresh-session material is stored with platform secure storage and is never written to logs.',
        ),
        const SizedBox(height: 20),
        TextField(
          key: const Key('email_field'),
          controller: _emailController,
          keyboardType: TextInputType.emailAddress,
          autofillHints: const [AutofillHints.email],
          decoration: const InputDecoration(labelText: 'Email'),
        ),
        const SizedBox(height: 14),
        TextField(
          key: const Key('password_field'),
          controller: _passwordController,
          obscureText: true,
          autofillHints: const [AutofillHints.password],
          decoration: const InputDecoration(labelText: 'Password'),
        ),
        const SizedBox(height: 24),
        FilledButton.icon(
          key: const Key('sign_in_button'),
          onPressed: state.loading
              ? null
              : () => controller.signIn(
                  _emailController.text,
                  _passwordController.text,
                ),
          icon: state.loading
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.lock_outline),
          label: Text(state.loading ? 'Signing in…' : 'Sign in'),
        ),
      ],
    );
  }
}

class _HomeScreen extends ConsumerWidget {
  const _HomeScreen();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(mobileControllerProvider);
    final controller = ref.read(mobileControllerProvider.notifier);
    return _Shell(
      title: 'Home',
      state: state,
      children: [
        Text(
          'Governed visible-appearance analysis',
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: 8),
        const Text(scientificLimitation),
        const SizedBox(height: 18),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            const Chip(
              avatar: Icon(Icons.check_circle_outline),
              label: Text('Image consent active'),
            ),
            const Chip(
              avatar: Icon(Icons.check_circle_outline),
              label: Text('Cloud consent active'),
            ),
            Chip(
              avatar: Icon(
                state.modelImprovementConsent
                    ? Icons.check_circle_outline
                    : Icons.block,
              ),
              label: Text(
                state.modelImprovementConsent
                    ? 'Model improvement opted in'
                    : 'Model improvement off',
              ),
            ),
          ],
        ),
        const SizedBox(height: 24),
        FilledButton.icon(
          key: const Key('start_capture'),
          onPressed: controller.startCapture,
          icon: const Icon(Icons.camera_alt_outlined),
          label: const Text('Start guided capture'),
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          key: const Key('open_privacy'),
          onPressed: controller.openPrivacy,
          icon: const Icon(Icons.privacy_tip_outlined),
          label: const Text('Privacy and data controls'),
        ),
        const SizedBox(height: 20),
        const _SafetyCard(),
      ],
    );
  }
}

class _CaptureScreen extends ConsumerWidget {
  const _CaptureScreen();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(mobileControllerProvider);
    final controller = ref.read(mobileControllerProvider.notifier);
    return _Shell(
      title: 'Guided capture',
      state: state,
      leading: IconButton(
        onPressed: controller.goHome,
        icon: const Icon(Icons.arrow_back),
        tooltip: 'Back to home',
      ),
      children: [
        Container(
          height: 220,
          decoration: BoxDecoration(
            border: Border.all(
              color: Theme.of(context).colorScheme.outline,
              width: 2,
            ),
            borderRadius: BorderRadius.circular(24),
          ),
          child: const Center(child: Icon(Icons.face_6_outlined, size: 110)),
        ),
        const SizedBox(height: 18),
        Text('Capture guidance', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 8),
        const Text(
          '• Use even indirect light; avoid direct sun and deep shade.',
        ),
        const Text('• Remove beauty filters and automatic skin smoothing.'),
        const Text('• Hold the device steady and keep the face centred.'),
        const Text('• Do not capture another person without their consent.'),
        const SizedBox(height: 18),
        const _StatusPanel(
          icon: Icons.science_outlined,
          message:
              'The sliders provide capture guidance. Production analysis requests native camera permission and uploads only the selected image bytes.',
        ),
        const SizedBox(height: 18),
        Text('Lighting level: ${(state.brightness * 100).round()}%'),
        Slider(
          key: const Key('brightness_slider'),
          value: state.brightness,
          onChanged: controller.updateBrightness,
          divisions: 20,
          label: '${(state.brightness * 100).round()}%',
        ),
        Text('Device stability: ${(state.stability * 100).round()}%'),
        Slider(
          key: const Key('stability_slider'),
          value: state.stability,
          onChanged: controller.updateStability,
          divisions: 20,
          label: '${(state.stability * 100).round()}%',
        ),
        const SizedBox(height: 16),
        FilledButton.icon(
          key: const Key('assess_capture'),
          onPressed: controller.assessCapture,
          icon: const Icon(Icons.fact_check_outlined),
          label: const Text('Check capture quality'),
        ),
      ],
    );
  }
}

class _QualityScreen extends ConsumerWidget {
  const _QualityScreen();

  String _qualityLabel(CaptureQuality quality) => switch (quality) {
    CaptureQuality.acceptable => 'Acceptable',
    CaptureQuality.tooDark => 'Too dark',
    CaptureQuality.tooBright => 'Too bright',
    CaptureQuality.unstable => 'Unstable',
    CaptureQuality.unknown => 'Unknown',
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(mobileControllerProvider);
    final controller = ref.read(mobileControllerProvider.notifier);
    final assessment = state.assessment;
    if (assessment == null) {
      return _Shell(
        title: 'Capture quality',
        state: state,
        children: [
          const Text('No capture assessment is available.'),
          FilledButton(
            onPressed: controller.retakeCapture,
            child: const Text('Return to capture'),
          ),
        ],
      );
    }
    return _Shell(
      title: 'Capture quality',
      state: state,
      leading: IconButton(
        onPressed: controller.retakeCapture,
        icon: const Icon(Icons.arrow_back),
        tooltip: 'Retake capture',
      ),
      children: [
        Icon(
          assessment.isAcceptable
              ? Icons.check_circle_outline
              : Icons.warning_amber_outlined,
          size: 72,
        ),
        const SizedBox(height: 12),
        Text(
          _qualityLabel(assessment.quality),
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 10),
        Text(assessment.guidance, textAlign: TextAlign.center),
        const SizedBox(height: 22),
        _ScoreRow(label: 'Lighting quality', value: assessment.lightingQuality),
        _ScoreRow(label: 'Capture quality', value: assessment.captureQuality),
        _ScoreRow(label: 'Stability', value: assessment.stability),
        const SizedBox(height: 24),
        if (assessment.isAcceptable)
          FilledButton.icon(
            key: const Key('analyse_capture'),
            onPressed: state.loading ? null : controller.analyseCapture,
            icon: state.loading
                ? const SizedBox.square(
                    dimension: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.analytics_outlined),
            label: Text(state.loading ? 'Analysing…' : 'Run governed analysis'),
          ),
        const SizedBox(height: 10),
        OutlinedButton(
          key: const Key('retake_capture'),
          onPressed: controller.retakeCapture,
          child: const Text('Retake'),
        ),
      ],
    );
  }
}

class _ResultScreen extends ConsumerWidget {
  const _ResultScreen();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(mobileControllerProvider);
    final controller = ref.read(mobileControllerProvider.notifier);
    final result = state.result;
    if (result == null) {
      return _Shell(
        title: 'Analysis result',
        state: state,
        children: [
          const Text('No governed analysis result is available.'),
          FilledButton(
            onPressed: controller.goHome,
            child: const Text('Return home'),
          ),
        ],
      );
    }
    return _Shell(
      title: 'Analysis result',
      state: state,
      leading: IconButton(
        onPressed: controller.goHome,
        icon: const Icon(Icons.close),
        tooltip: 'Close result',
      ),
      children: [
        const Icon(Icons.verified_outlined, size: 72),
        const SizedBox(height: 12),
        Text(
          'Visible appearance estimate ready',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: 16),
        const _StatusPanel(
          icon: Icons.no_photography_outlined,
          message:
              'No filter applied. Identity and skin texture are preserved.',
        ),
        const SizedBox(height: 18),
        _ScoreRow(label: 'Confidence', value: result.confidence),
        _ScoreRow(label: 'Uncertainty', value: result.uncertainty),
        _ScoreRow(label: 'Lighting quality', value: result.lightingQuality),
        _ScoreRow(label: 'Capture quality', value: result.captureQuality),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Explanation',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text(result.explanation),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Text(result.limitationWarning),
          ),
        ),
        const SizedBox(height: 22),
        FilledButton(
          key: const Key('result_home'),
          onPressed: controller.goHome,
          child: const Text('Return home'),
        ),
        const SizedBox(height: 10),
        OutlinedButton(
          onPressed: controller.openPrivacy,
          child: const Text('Open privacy controls'),
        ),
      ],
    );
  }
}

class _ScoreRow extends StatelessWidget {
  const _ScoreRow({required this.label, required this.value});

  final String label;
  final double value;

  @override
  Widget build(BuildContext context) {
    final normalised = value.clamp(0.0, 1.0).toDouble();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [Text(label), Text('${(normalised * 100).round()}%')],
          ),
          const SizedBox(height: 6),
          LinearProgressIndicator(value: normalised),
        ],
      ),
    );
  }
}

class _PrivacyScreen extends ConsumerWidget {
  const _PrivacyScreen();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(mobileControllerProvider);
    final controller = ref.read(mobileControllerProvider.notifier);
    return _Shell(
      title: 'Privacy and data',
      state: state,
      leading: IconButton(
        onPressed: controller.goHome,
        icon: const Icon(Icons.arrow_back),
        tooltip: 'Back to home',
      ),
      children: [
        Text(
          'Your data rights',
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: 8),
        const Text(privacyNotice),
        const SizedBox(height: 18),
        const ListTile(
          leading: Icon(Icons.visibility_off_outlined),
          title: Text('No raw-image logging'),
          subtitle: Text(
            'Tokens, passwords, and raw image paths are excluded from logs.',
          ),
        ),
        const ListTile(
          leading: Icon(Icons.model_training_outlined),
          title: Text('Separate training consent'),
          subtitle: Text(
            'Model-improvement consent is optional and off by default.',
          ),
        ),
        const SizedBox(height: 18),
        FilledButton.icon(
          key: const Key('request_export'),
          onPressed: state.loading ? null : controller.requestDataExport,
          icon: const Icon(Icons.download_outlined),
          label: const Text('Request data export'),
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          key: const Key('request_deletion'),
          onPressed: state.loading
              ? null
              : () async {
                  final confirmed = await showDialog<bool>(
                    context: context,
                    builder: (context) => AlertDialog(
                      title: const Text('Request data deletion?'),
                      content: const Text(
                        'This revokes processing consent, clears the local session, and requests deletion through the privacy API.',
                      ),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(context, false),
                          child: const Text('Cancel'),
                        ),
                        FilledButton(
                          key: const Key('confirm_deletion'),
                          onPressed: () => Navigator.pop(context, true),
                          child: const Text('Request deletion'),
                        ),
                      ],
                    ),
                  );
                  if (confirmed == true) {
                    await controller.requestDataDeletion();
                  }
                },
          icon: const Icon(Icons.delete_outline),
          label: const Text('Request data deletion'),
        ),
      ],
    );
  }
}
