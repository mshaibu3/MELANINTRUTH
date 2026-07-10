import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:melanintruth_mobile/main.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('native app preserves disclosure and consent gates',
      (tester) async {
    await tester.pumpWidget(const MelaninTruthApp());
    await tester.pumpAndSettle();

    expect(find.text('True skin. True tone. No filter.'), findsOneWidget);
    expect(
      find.textContaining('not an exact biological melanin measurement'),
      findsOneWidget,
    );

    await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));

    await tester.tap(find.byKey(const Key('welcome_continue')));
    await tester.pumpAndSettle();

    final continueButton = tester.widget<FilledButton>(
      find.byKey(const Key('consent_continue')),
    );
    expect(continueButton.onPressed, isNull);
    expect(find.textContaining('Model improvement'), findsWidgets);
  });
}
