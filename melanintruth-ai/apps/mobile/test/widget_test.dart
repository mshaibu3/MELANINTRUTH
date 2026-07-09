import 'package:flutter_test/flutter_test.dart';
import 'package:melanintruth_mobile/main.dart';
void main(){testWidgets('renders safe tagline',(tester) async{await tester.pumpWidget(const MelaninTruthApp()); expect(find.text('True skin. True tone. No filter.'), findsOneWidget);});}
