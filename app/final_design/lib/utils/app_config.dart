// App configuration for different environments
//
// BUILD-TIME FLAGS (via --dart-define):
//
//   Development (default):
//     flutter run
//
//   Development with mocks (no Firebase/S3 - fast testing):
//     flutter run --dart-define=USE_MOCKS=true
//
//   Production:
//     flutter build apk --dart-define=ENVIRONMENT=production
//
// MOCK MODE:
//   When USE_MOCKS=true:
//   - Uses MockAuthProvider (in-memory, pre-seeded users)
//   - Uses MockStorageProvider (local file storage)
//   - Password requirement: 1+ character
//   - Pre-seeded user: user1@test.com / 1
//
// For production deployment:
// - Deploy Flask backend to Hugging Face Spaces
// - Update `_productionBackendUrl` with your Space URL
// - Build with: flutter build apk --dart-define=ENVIRONMENT=production

enum Environment {
  development,
  production,
}

class AppConfig {
  // ============================================
  // BUILD-TIME FLAGS (via --dart-define)
  // ============================================

  /// Environment: 'development' or 'production'
  /// Usage: --dart-define=ENVIRONMENT=production
  static const String _envString = String.fromEnvironment(
    'ENVIRONMENT',
    defaultValue: 'development',
  );

  /// Use mock providers (no Firebase/S3 calls)
  /// Usage: --dart-define=USE_MOCKS=true
  static const bool useMocks = bool.fromEnvironment(
    'USE_MOCKS',
    defaultValue: false,
  );

  static Environment get currentEnvironment {
    return _envString == 'production'
        ? Environment.production
        : Environment.development;
  }

  // ============================================
  // BACKEND URLs
  // ============================================

  /// Development backend URL (ngrok tunnel for local testing)
  /// Update this when you restart ngrok
  /// IMPORTANT: Replace this with your actual ngrok URL (e.g., "https://abc123.ngrok-free.app")
  static const String _devBackendUrl = "";

  /// Production backend URL (Hugging Face Spaces or other hosting)
  /// TODO: Update this URL after deploying to Hugging Face Spaces
  static const String _productionBackendUrl =
      "https://YOUR_USERNAME-feline-skin-detection.hf.space";

  /// Returns the backend URL based on current environment
  static String get backendUrl {
    switch (currentEnvironment) {
      case Environment.development:
        return _devBackendUrl;
      case Environment.production:
        return _productionBackendUrl;
    }
  }

  /// Returns true if running in development mode
  static bool get isDevelopment =>
      currentEnvironment == Environment.development;

  /// Returns true if running in production mode
  static bool get isProduction => currentEnvironment == Environment.production;

  // ============================================
  // APP INFO
  // ============================================
  static const String appName = "Pelta AI";
  static const String appVersion = "1.0.0";
  static const int appBuildNumber = 1;

  // ============================================
  // FEATURE FLAGS (for future subscription model)
  // ============================================
  static const int freeTierScansPerMonth = 5;
  static const bool enableSubscriptions = false; // Enable when ready
}
