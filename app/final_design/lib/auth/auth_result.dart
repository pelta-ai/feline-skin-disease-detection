/// Result of an authentication operation.
///
/// Contains success/failure status and relevant details.
class AuthResult {
  /// Whether the operation succeeded
  final bool success;

  /// The user's ID (only set on successful login/signup)
  final String? userId;

  /// Error code for failures (e.g., 'wrong-password', 'user-not-found')
  final String? errorCode;

  /// Human-readable error message
  final String? errorMessage;

  const AuthResult._({
    required this.success,
    this.userId,
    this.errorCode,
    this.errorMessage,
  });

  /// Create a successful result
  factory AuthResult.success({String? userId}) {
    return AuthResult._(
      success: true,
      userId: userId,
    );
  }

  /// Create a failure result
  factory AuthResult.failure(String errorCode, [String? errorMessage]) {
    return AuthResult._(
      success: false,
      errorCode: errorCode,
      errorMessage: errorMessage ?? _getDefaultMessage(errorCode),
    );
  }

  /// Get a user-friendly message for common error codes
  static String _getDefaultMessage(String errorCode) {
    switch (errorCode) {
      case 'user-not-found':
        return 'No account found with this email';
      case 'wrong-password':
        return 'Invalid password';
      case 'invalid-email':
        return 'Invalid email address';
      case 'email-already-in-use':
        return 'An account already exists with this email';
      case 'weak-password':
        return 'Password is too weak';
      case 'network-error':
        return 'Network error. Please check your connection.';
      case 'too-many-requests':
        return 'Too many attempts. Please try again later.';
      case 'user-disabled':
        return 'This account has been disabled';
      default:
        return 'An error occurred. Please try again.';
    }
  }

  @override
  String toString() {
    if (success) {
      return 'AuthResult.success(userId: $userId)';
    } else {
      return 'AuthResult.failure($errorCode: $errorMessage)';
    }
  }
}
