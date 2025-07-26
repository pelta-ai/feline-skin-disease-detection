import 'package:flutter/material.dart';
import 'package:final_design/login.dart';
import 'package:final_design/home.dart';
import 'package:final_design/sign_up.dart';
import 'package:final_design/streak.dart';
import 'package:final_design/results.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:final_design/utils/firebase_options.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      //home: LoginScreen(),
      initialRoute: '/',
      routes: {
        '/': (context) => LoginScreen(),
        '/home': (context) => HomeScreen(),
        '/sign_up': (context) => SignUpScreen(),
        '/streak': (context) => StreakScreen(),
        '/recent_diagnosis': (context) => RecentDiagnosisScreen(),
      },
    );
  }
}
