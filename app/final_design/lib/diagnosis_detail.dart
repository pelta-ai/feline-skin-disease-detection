import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import 'package:final_design/diagnosis_info.dart';
import 'package:final_design/diagnosis_store.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/utils/custom_app_bar.dart';
import 'package:final_design/utils/responsive.dart';
import 'package:final_design/web_shell.dart';

/// Full breakdown of a single diagnosis: the image, the top predictions with
/// their confidences, and a reference description for each.
class DiagnosisDetailScreen extends StatelessWidget {
  final DiagnosisResult diagnosis;

  const DiagnosisDetailScreen({super.key, required this.diagnosis});

  @override
  Widget build(BuildContext context) {
    if (isWide(context)) return _buildWide(context);
    return _buildMobile(context);
  }

  Widget _buildWide(BuildContext context) {
    final predictions = diagnosis.predictions;
    return WebShell(
      active: '/recent_diagnosis',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Align(
            alignment: Alignment.centerLeft,
            child: TextButton.icon(
              onPressed: () => Navigator.of(context).pop(),
              icon: const Icon(Icons.arrow_back, size: 18, color: colorPrimary),
              label: Text("Back to Recent Diagnosis",
                  style:
                      textThemeColor.bodyLarge?.copyWith(color: colorPrimary)),
              style: TextButton.styleFrom(padding: EdgeInsets.zero),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(20),
                child: Image.memory(
                  diagnosis.imageBytes,
                  width: 380,
                  height: 380,
                  fit: BoxFit.cover,
                ),
              ),
              const SizedBox(width: 32),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _Headline(diagnosis: diagnosis),
                    const SizedBox(height: 24),
                    Text(
                      predictions.length > 1 ? 'Top matches' : 'Result',
                      style: textThemeColor.titleMedium,
                    ),
                    const SizedBox(height: 12),
                    for (var i = 0; i < predictions.length; i++)
                      _PredictionCard(
                        prediction: predictions[i],
                        rank: i + 1,
                        isTop: i == 0,
                      ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMobile(BuildContext context) {
    final predictions = diagnosis.predictions;

    return Scaffold(
      backgroundColor: colorMainLight,
      appBar: CustomAppBar(
        title: "Diagnosis",
        height: 120,
        action: IconButton(
          icon: const Icon(Icons.close, color: colorWhite),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: Image.memory(
              diagnosis.imageBytes,
              height: 220,
              width: double.infinity,
              fit: BoxFit.cover,
            ),
          ),
          const SizedBox(height: 20),
          _Headline(diagnosis: diagnosis),
          const SizedBox(height: 24),
          Text(
            predictions.length > 1 ? 'Top matches' : 'Result',
            style: textThemeColor.titleMedium,
          ),
          const SizedBox(height: 12),
          for (var i = 0; i < predictions.length; i++)
            _PredictionCard(
              prediction: predictions[i],
              rank: i + 1,
              isTop: i == 0,
            ),
        ],
      ),
    );
  }
}

/// The big header: condition name (or "Uncertain Result") plus the timestamp.
class _Headline extends StatelessWidget {
  final DiagnosisResult diagnosis;

  const _Headline({required this.diagnosis});

  @override
  Widget build(BuildContext context) {
    final uncertain = diagnosis.isUncertain;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(
              uncertain ? Icons.help_outline : Icons.pets,
              color: uncertain ? colorGrayDark : colorPrimary,
              size: 26,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                diagnosis.headline,
                style: textThemeColor.displayMedium?.copyWith(fontSize: 26),
              ),
            ),
          ],
        ),
        if (uncertain) ...[
          const SizedBox(height: 8),
          Text(
            "Pelta isn't confident about this scan. Treat the matches below as "
            "possibilities only, and see a vet if you have concerns.",
            style: textThemeColor.bodyMedium,
          ),
        ],
        const SizedBox(height: 8),
        Text(
          DateFormat('MMM d, y · h:mm a').format(diagnosis.timestamp),
          style: textThemeColor.bodySmall?.copyWith(color: colorGrayDark),
        ),
      ],
    );
  }
}

/// One ranked prediction: label, confidence bar, and description.
class _PredictionCard extends StatelessWidget {
  final Prediction prediction;
  final int rank;
  final bool isTop;

  const _PredictionCard({
    required this.prediction,
    required this.rank,
    required this.isTop,
  });

  @override
  Widget build(BuildContext context) {
    final description = descriptionFor(prediction.label);
    // Clamp guards against any out-of-range confidence reaching the bar.
    final fraction = prediction.confidence.clamp(0.0, 1.0);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colorWhite,
        borderRadius: BorderRadius.circular(16),
        border: isTop ? Border.all(color: colorPrimary, width: 2) : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 26,
                height: 26,
                alignment: Alignment.center,
                decoration: const BoxDecoration(
                  color: colorMainLight,
                  shape: BoxShape.circle,
                ),
                child: Text('$rank', style: textThemeColor.bodyLarge),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  displayLabel(prediction.label),
                  style: textThemeColor.titleMedium,
                ),
              ),
              Text(
                formatConfidence(prediction.confidence),
                style: textThemeColor.bodyLarge,
              ),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: fraction,
              minHeight: 8,
              backgroundColor: colorMainLight,
              valueColor: const AlwaysStoppedAnimation<Color>(colorPrimary),
            ),
          ),
          if (description != null) ...[
            const SizedBox(height: 12),
            Text(
              description,
              style: textThemeColor.bodyMedium?.copyWith(height: 1.5),
            ),
          ],
        ],
      ),
    );
  }
}
