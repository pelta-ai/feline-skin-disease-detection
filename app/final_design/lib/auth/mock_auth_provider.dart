import 'dart:async';
import 'package:final_design/auth/auth_provider.dart';
import 'package:final_design/auth/auth_result.dart';

/// Mock implementation of AppAuthProvider for unit testing and development.
///
/// Allows you to simulate authentication scenarios without hitting Firebase.
/// All data is stored in-memory and lost when the app restarts.
///
/// PRE-SEEDED TEST USERS (ready to use):
///   - user1@test.com / 1  (regular user for testing)
///
/// FUTURE: Add more test users as needed:
///   - admin1@test.com / 1  (for admin features)
///   - premium1@test.com / 1  (for subscription features)
///
/// Usage:
///   final mockAuth = MockAuthProvider();
///
///   // Login with pre-seeded user
///   await mockAuth.signIn('user1@test.com', '1');
///
///   // Simulate a failed login
///   mockAuth.nextSignInResult = AuthResult.failure('wrong-password');
///
///   // Check if methods were called
///   expect(mockAuth.signInCallCount, 1);
class MockAuthProvider implements AppAuthProvider {
  // ============================================
  // Mock User State
  // ============================================

  String? _currentUserId;
  String? _currentUserEmail;
  String? _currentUserDisplayName;
  bool _isEmailVerified = false;

  /// Mock verification code - enter "123" to verify email
  static const String mockVerificationCode = '123';

  final StreamController<String?> _authStateController =
      StreamController<String?>.broadcast();

  // ============================================
  // Pre-seeded Users (email -> {password, userId, displayName, verified})
  // ============================================
  final Map<String, Map<String, dynamic>> _preSeededUsers = {
    'user1@test.com': {
      'password': '1',
      'userId': 'mock-user-1',
      'displayName': 'Test User 1',
      'verified': true, // Pre-seeded users are already verified
    },
    // FUTURE: Add more test users as needed
    // 'admin1@test.com': {
    //   'password': '1',
    //   'userId': 'mock-admin-1',
    //   'displayName': 'Admin User',
    // },
    // 'premium1@test.com': {
    //   'password': '1',
    //   'userId': 'mock-premium-1',
    //   'displayName': 'Premium User',
    // },
  };

  // Runtime registered users (from sign-up)
  // Note: New users start with verified: false
  final Map<String, Map<String, dynamic>> _registeredUsers = {};

  // ============================================
  // Configurable Results (set these in tests)
  // ============================================

  /// The result to return from the next signIn() call
  AuthResult? nextSignInResult;

  /// The result to return from the next signUp() call
  AuthResult? nextSignUpResult;

  /// The result to return from the next sendPasswordResetEmail() call
  AuthResult? nextPasswordResetResult;

  /// The result to return from the next updateDisplayName() call
  AuthResult? nextUpdateDisplayNameResult;

  // ============================================
  // Call Tracking (for test assertions)
  // ============================================

  int signInCallCount = 0;
  int signUpCallCount = 0;
  int signOutCallCount = 0;
  int passwordResetCallCount = 0;
  int updateDisplayNameCallCount = 0;

  /// Last email passed to signIn()
  String? lastSignInEmail;

  /// Last password passed to signIn()
  String? lastSignInPassword;

  /// Last email passed to signUp()
  String? lastSignUpEmail;

  /// Last display name passed to signUp()
  String? lastSignUpDisplayName;

  /// Last email passed to sendPasswordResetEmail()
  String? lastPasswordResetEmail;

  // ============================================
  // Test Helper Methods
  // ============================================

  /// Set the current user state (simulates logged-in user)
  void setCurrentUser({
    required String userId,
    String? email,
    String? displayName,
  }) {
    _currentUserId = userId;
    _currentUserEmail = email;
    _currentUserDisplayName = displayName;
    _authStateController.add(userId);
  }

  /// Clear the current user (simulates logged-out state)
  void clearCurrentUser() {
    _currentUserId = null;
    _currentUserEmail = null;
    _currentUserDisplayName = null;
    _authStateController.add(null);
  }

  /// Reset all mock state and call counts
  void reset() {
    clearCurrentUser();
    nextSignInResult = null;
    nextSignUpResult = null;
    nextPasswordResetResult = null;
    nextUpdateDisplayNameResult = null;
    signInCallCount = 0;
    signUpCallCount = 0;
    signOutCallCount = 0;
    passwordResetCallCount = 0;
    updateDisplayNameCallCount = 0;
    lastSignInEmail = null;
    lastSignInPassword = null;
    lastSignUpEmail = null;
    lastSignUpDisplayName = null;
    lastPasswordResetEmail = null;
  }

  /// Dispose the stream controller
  void dispose() {
    _authStateController.close();
  }

  // ============================================
  // AuthProvider Implementation
  // ============================================

  @override
  String? get currentUserId => _currentUserId;

  @override
  String? get currentUserEmail => _currentUserEmail;

  @override
  String? get currentUserDisplayName => _currentUserDisplayName;

  @override
  bool get isLoggedIn => _currentUserId != null;

  /// Helper to find a user by email (checks pre-seeded and registered)
  Map<String, dynamic>? _findUser(String email) {
    final normalizedEmail = email.trim().toLowerCase();
    // Check pre-seeded users first
    for (final entry in _preSeededUsers.entries) {
      if (entry.key.toLowerCase() == normalizedEmail) {
        return entry.value;
      }
    }
    // Check registered users
    for (final entry in _registeredUsers.entries) {
      if (entry.key.toLowerCase() == normalizedEmail) {
        return entry.value;
      }
    }
    return null;
  }

  @override
  Future<AuthResult> signIn(String email, String password) async {
    signInCallCount++;
    lastSignInEmail = email;
    lastSignInPassword = password;

    // If a result was configured (for testing), return it
    if (nextSignInResult != null) {
      final result = nextSignInResult!;
      nextSignInResult = null; // Clear for next call
      if (result.success) {
        setCurrentUser(userId: result.userId ?? 'mock-user-id', email: email);
      }
      return result;
    }

    // Check if user exists
    final user = _findUser(email);
    if (user == null) {
      return AuthResult.failure('user-not-found', 'No user found with this email');
    }

    // Check password
    if (user['password'] != password) {
      return AuthResult.failure('wrong-password', 'Incorrect password');
    }

    // Success - set current user
    setCurrentUser(
      userId: user['userId'] as String,
      email: email,
      displayName: user['displayName'] as String?,
    );
    _isEmailVerified = user['verified'] as bool? ?? false;
    return AuthResult.success(userId: user['userId'] as String);
  }

  @override
  Future<AuthResult> signUp(
      String email, String password, String displayName) async {
    signUpCallCount++;
    lastSignUpEmail = email;
    lastSignUpDisplayName = displayName;

    // If a result was configured (for testing), return it
    if (nextSignUpResult != null) {
      final result = nextSignUpResult!;
      nextSignUpResult = null;
      if (result.success) {
        setCurrentUser(
          userId: result.userId ?? 'mock-user-id',
          email: email,
          displayName: displayName,
        );
      }
      return result;
    }

    // Check if user already exists
    if (_findUser(email) != null) {
      return AuthResult.failure('email-already-in-use', 'Email already registered');
    }

    // Register new user (unverified by default)
    final userId = 'mock-user-${DateTime.now().millisecondsSinceEpoch}';
    _registeredUsers[email.trim().toLowerCase()] = {
      'password': password,
      'userId': userId,
      'displayName': displayName,
      'verified': false, // New users must verify email
    };

    // Set as current user (unverified)
    setCurrentUser(userId: userId, email: email, displayName: displayName);
    _isEmailVerified = false;
    return AuthResult.success(userId: userId);
  }

  @override
  Future<void> signOut() async {
    signOutCallCount++;
    clearCurrentUser();
  }

  @override
  Future<AuthResult> sendPasswordResetEmail(String email) async {
    passwordResetCallCount++;
    lastPasswordResetEmail = email;

    // If a result was configured, return it
    if (nextPasswordResetResult != null) {
      final result = nextPasswordResetResult!;
      nextPasswordResetResult = null;
      return result;
    }

    // Default: success
    return AuthResult.success();
  }

  @override
  Future<AuthResult> updateDisplayName(String displayName) async {
    updateDisplayNameCallCount++;

    if (!isLoggedIn) {
      return AuthResult.failure('not-logged-in');
    }

    // If a result was configured, return it
    if (nextUpdateDisplayNameResult != null) {
      final result = nextUpdateDisplayNameResult!;
      nextUpdateDisplayNameResult = null;
      if (result.success) {
        _currentUserDisplayName = displayName;
      }
      return result;
    }

    // Default: success
    _currentUserDisplayName = displayName;
    return AuthResult.success(userId: _currentUserId);
  }

  // ============================================
  // Email Verification
  // ============================================

  @override
  bool get isEmailVerified => _isEmailVerified;

  @override
  Future<AuthResult> sendVerificationEmail() async {
    if (!isLoggedIn) {
      return AuthResult.failure('not-logged-in', 'No user is logged in');
    }

    // In mock mode, we don't actually send an email
    // User just needs to enter code "123"
    return AuthResult.success(userId: _currentUserId);
  }

  @override
  Future<AuthResult> completeEmailVerification(String? verificationData) async {
    if (!isLoggedIn) {
      return AuthResult.failure('not-logged-in', 'No user is logged in');
    }

    // Mock mode expects the verification code as verificationData
    if (verificationData == mockVerificationCode) {
      // Mark user as verified
      _isEmailVerified = true;

      // Update the stored user data
      if (_currentUserEmail != null) {
        final normalizedEmail = _currentUserEmail!.trim().toLowerCase();
        if (_registeredUsers.containsKey(normalizedEmail)) {
          _registeredUsers[normalizedEmail]!['verified'] = true;
        }
      }

      return AuthResult.success(userId: _currentUserId);
    } else {
      return AuthResult.failure(
        'invalid-verification-data',
        'Invalid verification code. Use "$mockVerificationCode" for mock mode.',
      );
    }
  }

  @override
  Future<void> refreshUser() async {
    // No-op in mock mode - state is already in memory
  }

  @override
  Stream<String?> get authStateChanges => _authStateController.stream;
}
