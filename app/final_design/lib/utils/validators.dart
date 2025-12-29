import 'package:final_design/utils/app_config.dart';

/// Input validation utilities for forms
class Validators {
  // Pre-compiled RegExp patterns for better performance.
  // Note: VS Code may show a warning about RegExp becoming 'final' in future Dart.
  // This is safe to ignore - we're using RegExp, not subclassing it.
  static final RegExp _emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
  static final RegExp _uppercaseRegex = RegExp(r'[A-Z]');
  static final RegExp _lowercaseRegex = RegExp(r'[a-z]');
  static final RegExp _digitRegex = RegExp(r'[0-9]');
  static final RegExp _symbolRegex = RegExp(r'[!@#$%^&*(),.?":{}|<>]');

  /// Validates email format
  /// Returns null if valid, error message if invalid
  static String? validateEmail(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Email is required';
    }

    final email = value.trim();

    if (!_emailRegex.hasMatch(email)) {
      return 'Please enter a valid email address';
    }

    return null;
  }

  /// Validates password strength
  ///
  /// Requirements vary by mode:
  /// - Mock mode (USE_MOCKS=true): 1+ character (for fast testing)
  /// - Development: 6+ characters
  /// - Production: 8+ chars, uppercase, lowercase, number, symbol
  ///
  /// Returns null if valid, error message if invalid
  static String? validatePassword(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password is required';
    }

    // Mock mode: minimal validation for fast testing
    if (AppConfig.useMocks) {
      if (value.isEmpty) {
        return 'Password is required';
      }
      return null; // Any non-empty password is valid
    }

    // Development mode: relaxed validation
    if (AppConfig.isDevelopment) {
      if (value.length < 6) {
        return 'Password must be at least 6 characters';
      }
      return null;
    }

    // Production mode: strict password requirements
    if (value.length < 8) {
      return 'Password must be at least 8 characters';
    }

    if (!_uppercaseRegex.hasMatch(value)) {
      return 'Password must contain at least one uppercase letter';
    }

    if (!_lowercaseRegex.hasMatch(value)) {
      return 'Password must contain at least one lowercase letter';
    }

    if (!_digitRegex.hasMatch(value)) {
      return 'Password must contain at least one number';
    }

    if (!_symbolRegex.hasMatch(value)) {
      return 'Password must contain at least one symbol (!@#\$%^&* etc.)';
    }

    return null;
  }

  /// Validates that confirm password matches password
  /// Returns null if valid, error message if invalid
  static String? validateConfirmPassword(String? password, String? confirmPassword) {
    if (confirmPassword == null || confirmPassword.isEmpty) {
      return 'Please confirm your password';
    }

    if (password != confirmPassword) {
      return 'Passwords do not match';
    }

    return null;
  }

  /// Validates name field
  /// Returns null if valid, error message if invalid
  static String? validateName(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Name is required';
    }

    if (value.trim().length < 2) {
      return 'Name must be at least 2 characters';
    }

    return null;
  }

  /// Checks if email format is valid (for inline checking)
  static bool isValidEmail(String email) {
    return validateEmail(email) == null;
  }

  /// Checks if password meets requirements (for inline checking)
  static bool isValidPassword(String password) {
    return validatePassword(password) == null;
  }

  /// Returns password requirements as a list of strings (for UI display)
  static List<String> getPasswordRequirements() {
    if (AppConfig.useMocks) {
      return ['Any password (mock mode)'];
    }
    if (AppConfig.isDevelopment) {
      return ['At least 6 characters'];
    }
    return [
      'At least 8 characters',
      'One uppercase letter (A-Z)',
      'One lowercase letter (a-z)',
      'One number (0-9)',
      'One symbol (!@#\$%^&* etc.)',
    ];
  }
}
