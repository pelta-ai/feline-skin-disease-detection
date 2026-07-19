import 'package:flutter/foundation.dart' show Uint8List;

/// A single completed diagnosis (image + predicted label), held in memory.
class DiagnosisResult {
  final Uint8List imageBytes;
  final String? label;
  final DateTime timestamp;

  const DiagnosisResult({
    required this.imageBytes,
    required this.label,
    required this.timestamp,
  });
}

/// In-memory store for this session's diagnoses.
///
/// Scans are not persisted yet, so this holds the history only for the current
/// app session. It is cleared when the app restarts.
class DiagnosisStore {
  DiagnosisStore._();

  static final List<DiagnosisResult> _history = [];

  /// All diagnoses made this session, newest first.
  static List<DiagnosisResult> get history => List.unmodifiable(_history);

  /// The most recent diagnosis, or null if none has been made this session.
  static DiagnosisResult? get latest =>
      _history.isEmpty ? null : _history.first;

  /// Adds a new diagnosis to the front of the history (keeping older ones).
  static void save(DiagnosisResult result) {
    _history.insert(0, result);
  }
}
