import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/drawer.dart';
import 'package:final_design/diagnosis_store.dart';

/// Turns a raw model label like "feline_acne" into "Feline Acne".
String _prettifyLabel(String? label) {
  if (label == null || label.isEmpty) return 'Unknown';
  return label
      .split('_')
      .where((w) => w.isNotEmpty)
      .map((w) => '${w[0].toUpperCase()}${w.substring(1)}')
      .join(' ');
}

class RecentDiagnosisScreen extends StatelessWidget {
  const RecentDiagnosisScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
        appBar: PreferredSize(
            preferredSize: Size.fromHeight(getScreenHeight(context) * 0.20),
            child: AppBar(
              backgroundColor: colorMain,
              automaticallyImplyLeading: true,
              iconTheme: IconThemeData(color: colorWhite),
              flexibleSpace: Stack(
                children: [
                  Column(
                    children: [
                      Padding(
                        padding: const EdgeInsets.only(top: 60),
                      ),
                      Center(
                        child: Text(
                          "Recent Diagnosis",
                          style: textThemeWhite.displaySmall,
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.only(top: 20),
                      ),
                      Center(
                        child: Text(
                          DateTime.now().toLocal().toString().split(' ')[0],
                          style: textThemeWhite.displaySmall,
                        ),
                      )
                    ],
                  )
                ],
              ),
              shape: const RoundedRectangleBorder(
                borderRadius:
                    BorderRadius.vertical(bottom: Radius.circular(20)),
              ),
            )),
        drawer: createDrawer(context, "Home"),
        body: RecentDiagnosis());
  }
}

class RecentDiagnosis extends StatelessWidget {
  const RecentDiagnosis({super.key});

  @override
  Widget build(BuildContext context) {
    final history = DiagnosisStore.history;

    if (history.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.image_search, size: 56, color: colorGrayDark),
              const SizedBox(height: 12),
              Text(
                "No recent diagnoses to show.",
                style: textThemeColor.bodyLarge,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 6),
              Text(
                "Run a scan from the home screen to see results here.",
                style: textThemeColor.bodyMedium,
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
      itemCount: history.length,
      separatorBuilder: (_, __) => const SizedBox(height: 16),
      itemBuilder: (context, index) =>
          _DiagnosisCard(diagnosis: history[index]),
    );
  }
}

/// A single diagnosis rendered as a card: image thumbnail, label, timestamp.
class _DiagnosisCard extends StatelessWidget {
  final DiagnosisResult diagnosis;

  const _DiagnosisCard({required this.diagnosis});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: colorMainLight,
        borderRadius: BorderRadius.circular(16),
        boxShadow: const [
          BoxShadow(
            color: Color.fromRGBO(0, 0, 0, 0.06),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      padding: const EdgeInsets.all(12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Image.memory(
              diagnosis.imageBytes,
              width: 84,
              height: 84,
              fit: BoxFit.cover,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  _prettifyLabel(diagnosis.label),
                  style: textThemeColor.titleMedium,
                ),
                const SizedBox(height: 6),
                Text(
                  DateFormat('MMM d, y · h:mm a').format(diagnosis.timestamp),
                  style: textThemeColor.bodyMedium,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
