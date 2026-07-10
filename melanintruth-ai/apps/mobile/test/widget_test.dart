import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melanintruth_mobile/main.dart';

Future<void> _tapKey(WidgetTester tester, String key) async {
  final finder = find.byKey(Key(key));
  if (finder.evaluate().isEmpty) {
    await tester.scrollUntilVisible(
      finder,
      240,
      scrollable: find.byType(Scrollable).first,
    );
  }
  expect(finder, findsOneWidget, reason: 'Expected keyed control: $key');
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('renders the safety promise and scientific limitation',
      (tester) async {
    await tester.pumpWidget(const MelaninTruthApp());

    expect(find.text('True skin. True tone. No filter.'), findsOneWidget);
    expect(
      find.textContaining('not an exact biological melanin measurement'),
      findsOneWidget,
    );
    expect(find.textContaining('never whitens'), findsOneWidget);
  });

  testWidgets('completes consent-first governed analysis flow',
      (tester) async {
    await tester.pumpWidget(const MelaninTruthApp());
    await tester.pumpAndSettle();

    await _tapKey(tester, 'welcome_continue');

    final disabledContinue = tester.widget<FilledButton>(
      find.byKey(const Key('consent_continue')),
    );
    expect(disabledContinue.onPressed, isNull);

    await _tapKey(tester, 'image_consent');
    await _tapKey(tester, 'cloud_consent');
    await _tapKey(tester, 'consent_continue');

    await tester.enterText(
      find.byKey(const Key('email_field')),
      'mobile@example.com',
    );
    await tester.enterText(
      find.byKey(const Key('password_field')),
      'CorrectHorseBatteryStaple123!',
    );
    await _tapKey(tester, 'sign_in_button');

    expect(find.text('Governed visible-appearance analysis'), findsOneWidget);
    expect(find.text('Model improvement off'), findsOneWidget);

    await _tapKey(tester, 'start_capture');
    expect(find.text('Capture guidance'), findsOneWidget);

    await _tapKey(tester, 'assess_capture');
    expect(find.text('Acceptable'), findsOneWidget);

    await _tapKey(tester, 'analyse_capture');
    expect(find.text('Visible appearance estimate ready'), findsOneWidget);
    expect(find.text('Confidence'), findsOneWidget);
    expect(find.text('Uncertainty'), findsOneWidget);
    expect(
      find.text('No filter applied. Identity and skin texture are preserved.'),
      findsOneWidget,
    );
    expect(
      find.textContaining('not an exact biological melanin measurement'),
      findsOneWidget,
    );
  });
}
