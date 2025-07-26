import 'package:flutter/material.dart';
import 'package:design_1/login.dart';
import 'package:design_1/home.dart';
import 'package:design_1/sign_up.dart';
import 'package:design_1/streak.dart';
import 'package:firebase_core/firebase_core.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await Firebase.initializeApp();

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
      },
    );
  }
}

