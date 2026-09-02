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
import 'package:final_design/utils/constants.dart';
import 'package:final_design/utils/responsive.dart';
import 'package:google_fonts/google_fonts.dart';
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

/// Tracks the current route name so the global layout wrapper can decide
/// whether to show the wide "web" shell (Home) or a centered phone frame.
final ValueNotifier<String> currentRouteName = ValueNotifier<String>('/');

class _RouteNameObserver extends NavigatorObserver {
  void _update(Route<dynamic>? route) {
    final name = route?.settings.name;
    if (name != null) currentRouteName.value = name;
  }

  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    _update(route);
    super.didPush(route, previousRoute);
  }

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) {
    _update(previousRoute);
    super.didPop(route, previousRoute);
  }

  @override
  void didReplace({Route<dynamic>? newRoute, Route<dynamic>? oldRoute}) {
    _update(newRoute);
    super.didReplace(newRoute: newRoute, oldRoute: oldRoute);
  }

  @override
  void didRemove(Route<dynamic> route, Route<dynamic>? previousRoute) {
    _update(previousRoute);
    super.didRemove(route, previousRoute);
  }
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      initialRoute: '/',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: colorPrimary,
          brightness: Brightness.light,
        ).copyWith(primary: colorPrimary, surface: colorCream),
        scaffoldBackgroundColor: colorCream,
        textTheme: GoogleFonts.poppinsTextTheme(),
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.transparent,
          elevation: 0,
          scrolledUnderElevation: 0,
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: colorPrimary,
            foregroundColor: colorWhite,
            elevation: 0,
            padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            textStyle:
                GoogleFonts.poppins(fontWeight: FontWeight.w600, fontSize: 15),
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            backgroundColor: colorPrimary,
            foregroundColor: colorWhite,
            padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            textStyle:
                GoogleFonts.poppins(fontWeight: FontWeight.w600, fontSize: 15),
          ),
        ),
        snackBarTheme: SnackBarThemeData(
          behavior: SnackBarBehavior.floating,
          backgroundColor: colorBlack,
          contentTextStyle:
              GoogleFonts.poppins(color: colorWhite, fontSize: 13),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      navigatorObservers: [_RouteNameObserver()],
      // Global layout wrapper: on wide screens Home renders its own sidebar
      // "web" shell (full width); every other screen is centered in a phone
      // frame so it never stretches. On phones this is a no-op passthrough.
      builder: (context, child) {
        final content = child ?? const SizedBox.shrink();
        return ValueListenableBuilder<String>(
          valueListenable: currentRouteName,
          builder: (context, route, _) {
            final width = MediaQuery.of(context).size.width;
            // Screens that render their own wide "web" layout must NOT be
            // phone-framed (PhoneFrame clamps the reported width to 480, which
            // would make their own isWide() checks fail). At '/', AuthWrapper
            // shows login (logged out) or Home (verified) — both wide-capable;
            // only the unverified-email state stays phone-framed.
            final wideCapable = route == '/'
                ? !(auth.isLoggedIn && !auth.isEmailVerified)
                : const {
                    '/home',
                    '/login',
                    '/sign_up',
                    '/recent_diagnosis',
                    '/diagnosis_detail',
                    '/settings',
                  }.contains(route);
            if (width >= kWebBreakpoint && wideCapable) {
              return content; // screen builds its own wide layout
            }
            return PhoneFrame(child: content);
          },
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
