import 'package:final_design/auth/auth_result.dart';

/// Abstract interface for authentication providers.
///
/// Implementations can be created for Firebase, AWS Cognito, Auth0, etc.
/// Use MockAuthProvider for unit testing.
///
/// Usage:
///   final auth = getAuthProvider();
///   final result = await auth.signIn('user@example.com', 'password');
///   if (result.success) {
///     print('Logged in as ${auth.currentUserEmail}');
///   }
abstract class AppAuthProvider {
  // ============================================
  // Current User Properties
  // ============================================

  /// The current user's unique ID, or null if not logged in
  String? get currentUserId;

  /// The current user's email address, or null if not logged in
  String? get currentUserEmail;

  /// The current user's display name, or null if not set
  String? get currentUserDisplayName;

  /// Whether a user is currently logged in
  bool get isLoggedIn;

  // ============================================
  // Authentication Actions
  // ============================================

  /// Sign in with email and password
  ///
  /// Returns [AuthResult] with success/failure info
  Future<AuthResult> signIn(String email, String password);

  /// Create a new account with email, password, and display name
  ///
  /// Returns [AuthResult] with success/failure info
  Future<AuthResult> signUp(String email, String password, String displayName);

  /// Sign out the current user
  Future<void> signOut();

  /// Send a password reset email
  ///
  /// Returns [AuthResult] indicating success/failure
  Future<AuthResult> sendPasswordResetEmail(String email);

  /// Update the current user's display name
  Future<AuthResult> updateDisplayName(String displayName);

  // ============================================
  // Email Verification
  // ============================================

  /// Whether the current user's email is verified
  bool get isEmailVerified;

  /// Send a verification email to the current user
  ///
  /// For Firebase: Sends a link-based verification email
  /// For Mock: No-op (verification done via code)
  Future<AuthResult> sendVerificationEmail();

  /// Complete email verification with provider-specific data.
  ///
  /// - Mock: pass the verification code (e.g., "123")
  /// - Firebase: pass null (link-based, just call refreshUser after)
  /// - OTP providers: pass the OTP code
  Future<AuthResult> completeEmailVerification(String? verificationData);

  /// Refresh the current user's auth state
  ///
  /// Call this after user clicks verification link to update isEmailVerified
  Future<void> refreshUser();

  // ============================================
  // Auth State Stream
  // ============================================

  /// Stream that emits when auth state changes (login/logout)
  ///
  /// Emits the user ID when logged in, null when logged out
  Stream<String?> get authStateChanges;
}
