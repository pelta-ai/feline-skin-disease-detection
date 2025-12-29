import 'package:uuid/uuid.dart';

/// Utility class for generating unique request IDs.
///
/// Request IDs are used for correlating frontend requests
/// with backend logs and traces for debugging.
class RequestId {
  static const Uuid _uuid = Uuid();

  /// Generate a new unique request ID (UUID v4)
  static String generate() => _uuid.v4();
}
