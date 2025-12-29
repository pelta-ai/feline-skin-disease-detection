import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:final_design/login.dart';
import 'package:final_design/home.dart';
import 'package:final_design/sign_up.dart';
import 'package:final_design/streak.dart';
import 'package:final_design/results.dart';
import 'package:final_design/email_verification.dart';
import 'package:final_design/auth/index.dart';
import 'package:final_design/utils/app_config.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:firebase_analytics/firebase_analytics.dart';
import 'package:final_design/utils/firebase_options.dart';

/// Global analytics instance for tracking events throughout the app
late final FirebaseAnalytics analytics;

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Only initialize Firebase if not in mock mode
  if (!AppConfig.useMocks) {
    await Firebase.initializeApp(
      options: DefaultFirebaseOptions.currentPlatform,
    );

    // Initialize Analytics
    analytics = FirebaseAnalytics.instance;
    await analytics.setAnalyticsCollectionEnabled(true);

    // Initialize Crashlytics
    // Pass all uncaught "fatal" errors from the framework to Crashlytics
    FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterFatalError;

    // Pass all uncaught asynchronous errors to Crashlytics
    PlatformDispatcher.instance.onError = (error, stack) {
      FirebaseCrashlytics.instance.recordError(error, stack, fatal: true);
      return true;
    };

    // Log app start event
    await analytics.logAppOpen();
  }

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      initialRoute: '/',
      routes: {
        '/': (context) => const AuthWrapper(),
        '/login': (context) => const LoginScreen(),
        '/home': (context) => const HomeScreen(),
        '/sign_up': (context) => const SignUpScreen(),
        '/verify_email': (context) => const EmailVerificationScreen(),
        '/streak': (context) => const StreakScreen(),
        '/recent_diagnosis': (context) => const RecentDiagnosisScreen(),
      },
    );
  }
}

/// Wrapper that checks auth state on app launch
///
/// - Not logged in → Login screen
/// - Logged in but unverified → Verification screen
/// - Logged in and verified → Home screen
class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    // Check if user is logged in
    if (!auth.isLoggedIn) {
      return const LoginScreen();
    }

    // Check if email is verified
    if (!auth.isEmailVerified) {
      return const EmailVerificationScreen();
    }

    // User is logged in and verified
    return const HomeScreen();
  }
}
