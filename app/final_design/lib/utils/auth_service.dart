import 'package:firebase_auth/firebase_auth.dart';

class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;

  /// Create a new user (sign up)
  Future<User?> createUserWithEmailAndPassword({
    required String email,
    required String password,
  }) async {
    try {
      UserCredential result = await _auth.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );
      return result.user;
    } on FirebaseAuthException catch (e) {
      throw _getFriendlyError(e);
    } catch (e) {
      throw Exception("An unknown error occurred: $e");
    }
  }

  /// Sign in an existing user
  Future<User?> loginUserWithEmailAndPassword({
    required String email,
    required String password,
  }) async {
    try {
      UserCredential result = await _auth.signInWithEmailAndPassword(
        email: email,
        password: password,
      );
      return result.user;
    } on FirebaseAuthException catch (e) {
      throw _getFriendlyError(e);
    } catch (e) {
      throw Exception("An unknown error occurred: $e");
    }
  }

  /// Sign out the current user
  Future<void> signOut() async {
    await _auth.signOut();
  }

  /// Get the current logged-in user
  User? get currentUser => _auth.currentUser;

  /// Convert Firebase error codes into friendly messages
  Exception _getFriendlyError(FirebaseAuthException e) {
    switch (e.code) {
      case 'email-already-in-use':
        return Exception("This email is already registered. Try logging in.");
      case 'invalid-email':
        return Exception("Invalid email format. Please check and try again.");
      case 'weak-password':
        return Exception("Password is too weak. Please choose a stronger one.");
      case 'user-not-found':
        return Exception("No account found with this email.");
      case 'wrong-password':
        return Exception("Incorrect password. Please try again.");
      default:
        return Exception(e.message ?? "Authentication error occurred.");
    }
  }
}
