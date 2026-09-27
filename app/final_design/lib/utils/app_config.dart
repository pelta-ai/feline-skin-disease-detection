// App configuration for different environments
//
// BUILD-TIME FLAGS (via --dart-define):
//
//   Development (default):
//     flutter run
//
//   Development with mocks (no Supabase/S3 - fast testing):
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
// - Point `_defaultBackendUrl` at your Space URL, or pass
//   --dart-define=BACKEND_URL=... at build time
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

  /// Use mock providers (no Supabase/S3 calls)
  /// Usage: --dart-define=USE_MOCKS=true
  static const bool useMocks = bool.fromEnvironment(
    'USE_MOCKS',
    defaultValue: false,
  );

  // Note: Storage provider is controlled by the BACKEND, not Flutter.
  // The backend uses STORAGE_PROVIDER env var to choose Supabase/S3/Mock.
  // Flutter just calls the backend API - it doesn't need to know which
  // storage the backend uses.

  static Environment get currentEnvironment {
    return _envString == 'production'
        ? Environment.production
        : Environment.development;
  }

  // ============================================
  // BACKEND URLs
  // ============================================

  /// Development backend URL
  /// For local testing: http://localhost:5000
  /// For mobile device testing: use ngrok URL (e.g., "https://abc123.ngrok-free.app")
  static const String _devBackendUrl = "http://localhost:5000";

  /// Production backend URL (Hugging Face Space).
  ///
  /// Named explicitly for every platform rather than inferred from the page
  /// origin. The web build is served from a CDN (Cloudflare Pages) and is no
  /// longer same-origin with the API, so `Uri.base.origin` would resolve to the
  /// CDN host and every API call would 404.
  ///
  /// Override per build without touching this file:
  ///   flutter build web --dart-define=BACKEND_URL=https://staging.example.com
  static const String _defaultBackendUrl = "https://anishanup-pelta.hf.space";
  static const String _backendUrlOverride =
      String.fromEnvironment("BACKEND_URL");
  static String get _productionBackendUrl =>
      _backendUrlOverride.isEmpty ? _defaultBackendUrl : _backendUrlOverride;

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
