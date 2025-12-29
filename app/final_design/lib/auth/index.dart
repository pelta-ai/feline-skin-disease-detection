/// Authentication Module
///
/// Provides a clean abstraction for authentication operations.
/// Use the singleton instance or factory function to get the appropriate provider.
///
/// Usage:
///   import 'package:final_design/auth/index.dart';
///
///   // Use the global auth instance
///   if (auth.isLoggedIn) {
///     print('Welcome ${auth.currentUserDisplayName}');
///   }
///
///   // Or get a new instance
///   final authProvider = getAuthProvider();
///
///   // For testing, use mock provider
///   final mockAuth = MockAuthProvider();
library;

export 'auth_provider.dart';
export 'auth_result.dart';
export 'firebase_auth_provider.dart';
export 'mock_auth_provider.dart';

import 'package:final_design/auth/auth_provider.dart';
import 'package:final_design/auth/firebase_auth_provider.dart';
import 'package:final_design/auth/mock_auth_provider.dart';
import 'package:final_design/utils/app_config.dart';

/// Global auth provider instance.
///
/// Automatically selects provider based on build flags:
/// - USE_MOCKS=true → MockAuthProvider (in-memory, pre-seeded users)
/// - USE_MOCKS=false → FirebaseAuthProvider (real Firebase)
///
/// For manual override in tests, use [setAuthProvider].
AppAuthProvider _authProvider = AppConfig.useMocks
    ? MockAuthProvider()
    : FirebaseAuthProvider();

/// Get the current auth provider instance.
AppAuthProvider get auth => _authProvider;

/// Set the auth provider (useful for testing).
///
/// Example:
///   void main() {
///     setAuthProvider(MockAuthProvider());
///     runApp(MyApp());
///   }
void setAuthProvider(AppAuthProvider provider) {
  _authProvider = provider;
}

/// Factory function to create a new auth provider.
///
/// Args:
///   providerType: 'firebase' or 'mock'
///
/// Example:
///   final auth = getAuthProvider('mock');
AppAuthProvider getAuthProvider([String providerType = 'firebase']) {
  switch (providerType.toLowerCase()) {
    case 'mock':
      return MockAuthProvider();
    case 'firebase':
    default:
      return FirebaseAuthProvider();
  }
}
