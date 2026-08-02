import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:final_design/login.dart';
import 'package:final_design/home.dart';
import 'package:final_design/sign_up.dart';
import 'package:final_design/streak.dart';
import 'package:final_design/results.dart';
import 'package:final_design/email_verification.dart';
import 'package:final_design/disclaimer.dart';
import 'package:final_design/settings.dart';
import 'package:final_design/auth/index.dart';
import 'package:final_design/utils/app_config.dart';
import 'package:final_design/utils/profile_picture.dart';
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

  // Load the locally saved profile picture so the drawer avatar is correct on
  // the first frame rather than popping in afterwards.
  await ProfilePicture.load();

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      initialRoute: '/',
      // On wide screens (web/desktop) the mobile-first UI would otherwise
      // stretch full-width and look broken. Center it in a phone-width frame on
      // a neutral backdrop, and tell the subtree it's 480px wide so any
      // MediaQuery-based sizing behaves like a phone (no overflow). On actual
      // phones (<=480 logical px) this is a no-op.
      builder: (context, child) {
        final content = child ?? const SizedBox.shrink();
        final mq = MediaQuery.of(context);
        const maxWidth = 480.0;
        if (mq.size.width <= maxWidth) return content;
        return ColoredBox(
          color: const Color.fromRGBO(28, 33, 32, 1.0), // matches app's dark chrome
          child: Center(
            child: ClipRect(
              child: SizedBox(
                width: maxWidth,
                child: MediaQuery(
                  data: mq.copyWith(size: Size(maxWidth, mq.size.height)),
                  child: content,
                ),
              ),
            ),
          ),
        );
      },
      routes: {
        '/': (context) => const AuthWrapper(),
        '/login': (context) => const LoginScreen(),
        // Gated at the route, not just in AuthWrapper: the login and email
        // verification screens push '/home' directly, so a gate that lived only
        // in AuthWrapper would be skipped on every fresh sign-in.
        '/home': (context) => const DisclaimerGate(child: HomeScreen()),
        '/sign_up': (context) => const SignUpScreen(),
        '/verify_email': (context) => const EmailVerificationScreen(),
        '/streak': (context) => const StreakScreen(),
        '/recent_diagnosis': (context) => const RecentDiagnosisScreen(),
        '/settings': (context) => const SettingsScreen(),
      },
    );
  }
}

/// Wrapper that checks auth state on app launch
///
/// - Not logged in → Login screen
/// - Logged in but unverified → Verification screen
/// - Logged in and verified → Medical disclaimer (once) → Home screen
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

    // User is logged in and verified — require one-time disclaimer acceptance
    // before showing the home screen.
    return const DisclaimerGate(child: HomeScreen());
  }
}
