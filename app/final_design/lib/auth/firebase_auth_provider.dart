import 'package:firebase_auth/firebase_auth.dart';
import 'package:final_design/auth/auth_provider.dart';
import 'package:final_design/auth/auth_result.dart';

/// Firebase implementation of AppAuthProvider.
///
/// This is the production auth provider that uses Firebase Authentication.
class FirebaseAuthProvider implements AppAuthProvider {
  final FirebaseAuth _auth;

  /// Create a FirebaseAuthProvider.
  ///
  /// Optionally pass a FirebaseAuth instance for testing.
  FirebaseAuthProvider({FirebaseAuth? auth})
      : _auth = auth ?? FirebaseAuth.instance;

  // ============================================
  // Current User Properties
  // ============================================

  @override
  String? get currentUserId => _auth.currentUser?.uid;

  @override
  String? get currentUserEmail => _auth.currentUser?.email;

  @override
  String? get currentUserDisplayName => _auth.currentUser?.displayName;

  @override
  bool get isLoggedIn => _auth.currentUser != null;

  // ============================================
  // Authentication Actions
  // ============================================

  @override
  Future<AuthResult> signIn(String email, String password) async {
    try {
      final credential = await _auth.signInWithEmailAndPassword(
        email: email.trim(),
        password: password,
      );

      return AuthResult.success(userId: credential.user?.uid);
    } on FirebaseAuthException catch (e) {
      return AuthResult.failure(e.code, e.message);
    } catch (e) {
      return AuthResult.failure('unknown', e.toString());
    }
  }

  @override
  Future<AuthResult> signUp(
      String email, String password, String displayName) async {
    try {
      final credential = await _auth.createUserWithEmailAndPassword(
        email: email.trim(),
        password: password,
      );

      // Update display name after creation
      if (credential.user != null && displayName.isNotEmpty) {
        await credential.user!.updateDisplayName(displayName.trim());
      }

      return AuthResult.success(userId: credential.user?.uid);
    } on FirebaseAuthException catch (e) {
      return AuthResult.failure(e.code, e.message);
    } catch (e) {
      return AuthResult.failure('unknown', e.toString());
    }
  }

  @override
  Future<void> signOut() async {
    await _auth.signOut();
  }

  @override
  Future<AuthResult> sendPasswordResetEmail(String email) async {
    try {
      await _auth.sendPasswordResetEmail(email: email.trim());
      return AuthResult.success();
    } on FirebaseAuthException catch (e) {
      return AuthResult.failure(e.code, e.message);
    } catch (e) {
      return AuthResult.failure('unknown', e.toString());
    }
  }

  @override
  Future<AuthResult> updateDisplayName(String displayName) async {
    try {
      final user = _auth.currentUser;
      if (user == null) {
        return AuthResult.failure('not-logged-in', 'No user is logged in');
      }

      await user.updateDisplayName(displayName.trim());
      return AuthResult.success(userId: user.uid);
    } on FirebaseAuthException catch (e) {
      return AuthResult.failure(e.code, e.message);
    } catch (e) {
      return AuthResult.failure('unknown', e.toString());
    }
  }

  // ============================================
  // Email Verification
  // ============================================

  @override
  bool get isEmailVerified => _auth.currentUser?.emailVerified ?? false;

  @override
  Future<AuthResult> sendVerificationEmail() async {
    try {
      final user = _auth.currentUser;
      if (user == null) {
        return AuthResult.failure('not-logged-in', 'No user is logged in');
      }

      await user.sendEmailVerification();
      return AuthResult.success(userId: user.uid);
    } on FirebaseAuthException catch (e) {
      return AuthResult.failure(e.code, e.message);
    } catch (e) {
      return AuthResult.failure('unknown', e.toString());
    }
  }

  @override
  Future<AuthResult> completeEmailVerification(String? verificationData) async {
    // Firebase uses link-based verification
    // User clicks link in email, then call refreshUser() to update state
    // verificationData is ignored - just refresh and check status
    await refreshUser();

    if (isEmailVerified) {
      return AuthResult.success(userId: currentUserId);
    } else {
      return AuthResult.failure(
        'not-verified',
        'Email not yet verified. Please check your inbox and click the verification link.',
      );
    }
  }

  @override
  Future<void> refreshUser() async {
    await _auth.currentUser?.reload();
  }

  // ============================================
  // Auth State Stream
  // ============================================

  @override
  Stream<String?> get authStateChanges {
    return _auth.authStateChanges().map((user) => user?.uid);
  }
}
