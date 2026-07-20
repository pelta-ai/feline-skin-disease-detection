import 'package:flutter/foundation.dart' show Uint8List;

import 'package:final_design/diagnosis_info.dart';

/// One ranked prediction from the model: a raw class name and its confidence.
class Prediction {
  /// Raw model class name, e.g. `feline_acne`. Use [displayLabel] to show it.
  final String label;

  /// Confidence in the range 0..1.
  final double confidence;

  const Prediction({required this.label, required this.confidence});
}

/// A single completed diagnosis (image + ranked predictions), held in memory.
class DiagnosisResult {
  final Uint8List imageBytes;

  /// Predictions ordered by confidence, highest first. The backend returns the
  /// top three; mock mode returns one.
  final List<Prediction> predictions;

  final DateTime timestamp;

  const DiagnosisResult({
    required this.imageBytes,
    required this.predictions,
    required this.timestamp,
  });

  /// The highest-ranked prediction, or null if the model returned nothing.
  Prediction? get top => predictions.isEmpty ? null : predictions.first;

  /// Raw label of the top prediction.
  String? get label => top?.label;

  /// Whether the top prediction is too weak to present as a named condition.
  bool get isUncertain {
    final confidence = top?.confidence;
    return confidence == null || confidence < uncertaintyThreshold;
  }

  /// Headline for this diagnosis: the condition name, or [uncertainResultLabel]
  /// when the model is not confident enough to name one.
  String get headline =>
      isUncertain ? uncertainResultLabel : displayLabel(label);

  /// Builds a result from a backend prediction response.
  ///
  /// Tolerates both shapes in use: the Flask backend returns `labels` as a list
  /// of three class names with `confidence` as a parallel list of floats, while
  /// the mock provider returns a single label with one confidence number.
  factory DiagnosisResult.fromResponse({
    required Uint8List imageBytes,
    required Map<String, dynamic> response,
    required DateTime timestamp,
  }) {
    final labels = _labelsFrom(response);
    final confidences = _confidencesFrom(response);

    final predictions = <Prediction>[
      for (var i = 0; i < labels.length; i++)
        Prediction(
          label: labels[i],
          // A missing confidence is reported as 0 rather than dropped, so the
          // label is still shown instead of vanishing from the ranking.
          confidence: i < confidences.length ? confidences[i] : 0,
        ),
    ];

    return DiagnosisResult(
      imageBytes: imageBytes,
      predictions: predictions,
      timestamp: timestamp,
    );
  }

  static List<String> _labelsFrom(Map<String, dynamic> response) {
    final raw = response['labels'];
    if (raw is List) {
      return raw.whereType<String>().toList();
    }

    final single = response['label'];
    return single is String ? <String>[single] : <String>[];
  }

  static List<double> _confidencesFrom(Map<String, dynamic> response) {
    final raw = response['confidence'];
    if (raw is List) {
      return raw.whereType<num>().map((n) => n.toDouble()).toList();
    }
    return raw is num ? <double>[raw.toDouble()] : <double>[];
  }
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
