/// Display names and reference descriptions for the model's output classes.
///
/// The model emits raw class names (`feline_acne`, `other`, …) matching the
/// folders under `final_data/train`. Everything user-facing goes through here.
library;

/// Below this top-line confidence a result is presented as inconclusive rather
/// than as a named condition.
const double uncertaintyThreshold = 0.20;

/// Header shown in place of a condition name when the model is not confident
/// enough for the top prediction to mean much.
const String uncertainResultLabel = 'Uncertain Result';

/// The model's catch-all class, shown to users as [_noClearMatchLabel].
const String otherClassKey = 'other';

const String _noClearMatchLabel = 'No Clear Match';

/// Reference text for each condition, keyed by raw model class name.
const Map<String, String> _descriptions = <String, String>{
  'allergic_dermatitis':
      "A skin condition caused by an allergic reaction, often to fleas, food, "
          "pollen, dust, or other environmental allergens. Allergic dermatitis "
          "can cause severe itching and irritation, leading to constant "
          "scratching, licking, or chewing. Felines will often experience hair "
          "loss, scabs, redness, and open sores as a result of this.",
  'ear_mites':
      "An extremely contagious skin condition caused by tiny parasites located "
          "in a feline's ear. Common symptoms include frequent head shaking, "
          "ear scratching, dark coffee ground-like substances expelled from the "
          "ear, and irritation. Ear mites can lead to future infections, aural "
          "hematomas (blood vessels in the ear flap that break, forming a large "
          "blood blister), and ruptured eardrums.",
  'eosinophilic_granuloma':
      "A group of inflammatory skin conditions often linked to allergies or an "
          "overactive immune system response. Symptoms include ulcers on the "
          "lips, raised plaques on the skin, or swollen, irritated areas that "
          "may not always be itchy. It is often the result of an undetected "
          "allergy.",
  'feline_acne':
      "A skin disorder commonly located on the chin and lips. They often take "
          "the appearance of blackheads, pimples, or large, swollen bumps. The "
          "exact cause is unidentifiable, but poor grooming, stress, or plastic "
          "food bowls can contribute to the growth of feline acne. If left "
          "untreated it can lead to future infections.",
  'fungal':
      "A fungal skin infection, most commonly ringworm, is caused by "
          "dermatophyte fungi (a group of specialized, mold-like fungi). It "
          "causes circular patches of hair loss, scaly textured skin, redness, "
          "and broken hairs. This fungal infection can spread quickly between "
          "both pets and humans.",
  'mange':
      "A skin disease caused by microscopic mites living on or within the skin. "
          "Symptoms include severe itching, hair loss, redness, crusty skin, "
          "and sores. Some forms of this skin disease are contagious, most "
          "likely contracted from other animals. However, some forms occur when "
          "the feline's immune system is weak.",
  // Deliberately describes what the result means about the scan rather than
  // about the cat — this class is the absence of a match, not a condition.
  otherClassKey:
      "The scan did not match any condition Pelta recognises closely enough to "
          "name one. This does not mean the skin is healthy — the photo may be "
          "unclear, or the condition may be outside what Pelta was trained on. "
          "If you have any concerns, contact a veterinarian.",
};

/// Turns a raw model label like `feline_acne` into `Feline Acne`.
///
/// The catch-all `other` class becomes [_noClearMatchLabel], which reads as a
/// result rather than as a category name.
String displayLabel(String? rawLabel) {
  if (rawLabel == null || rawLabel.isEmpty) return 'Unknown';
  if (rawLabel.toLowerCase() == otherClassKey) return _noClearMatchLabel;

  return rawLabel
      .split('_')
      .where((word) => word.isNotEmpty)
      .map((word) => '${word[0].toUpperCase()}${word.substring(1)}')
      .join(' ');
}

/// Reference text for [rawLabel], or null when the class has none.
String? descriptionFor(String? rawLabel) {
  if (rawLabel == null) return null;
  return _descriptions[rawLabel.toLowerCase()];
}

/// Formats a 0..1 confidence as a percentage, e.g. `87.3%`.
String formatConfidence(double confidence) =>
    '${(confidence * 100).toStringAsFixed(1)}%';
