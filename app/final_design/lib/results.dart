import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/utils/responsive.dart';
import 'package:final_design/web_shell.dart';
import 'package:final_design/drawer.dart';
import 'package:final_design/diagnosis_detail.dart';
import 'package:final_design/diagnosis_info.dart';
import 'package:final_design/diagnosis_store.dart';

class RecentDiagnosisScreen extends StatelessWidget {
  const RecentDiagnosisScreen({super.key});

  @override
  Widget build(BuildContext context) {
    if (isWide(context)) {
      return const WebShell(
        active: '/recent_diagnosis',
        child: RecentDiagnosis(),
      );
    }
    return Scaffold(
        appBar: PreferredSize(
            preferredSize: Size.fromHeight(getScreenHeight(context) * 0.20),
            child: AppBar(
              backgroundColor: colorPrimary,
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

    if (isWide(context)) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("Recent Diagnosis", style: textThemeColor.displayMedium),
          const SizedBox(height: 6),
          Text("Your past scans and their results.",
              style: textThemeColor.bodyMedium),
          const SizedBox(height: 24),
          if (history.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 48),
              child: _emptyState(),
            )
          else
            Wrap(
              spacing: 20,
              runSpacing: 20,
              children: [
                for (final d in history)
                  SizedBox(width: 360, child: _DiagnosisCard(diagnosis: d)),
              ],
            ),
        ],
      );
    }

    if (history.isEmpty) return _emptyState();

    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
      itemCount: history.length,
      separatorBuilder: (_, __) => const SizedBox(height: 16),
      itemBuilder: (context, index) =>
          _DiagnosisCard(diagnosis: history[index]),
    );
  }

  Widget _emptyState() {
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
}

/// A single diagnosis rendered as a card: image thumbnail, headline label,
/// top-prediction confidence, and timestamp. Tapping opens the full breakdown.
class _DiagnosisCard extends StatelessWidget {
  final DiagnosisResult diagnosis;

  const _DiagnosisCard({required this.diagnosis});

  @override
  Widget build(BuildContext context) {
    final topConfidence = diagnosis.top?.confidence;

    return Material(
      color: colorMainLight,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute<void>(
            settings: const RouteSettings(name: '/diagnosis_detail'),
            builder: (_) => DiagnosisDetailScreen(diagnosis: diagnosis),
          ),
        ),
        child: Container(
          decoration: BoxDecoration(
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
                      diagnosis.headline,
                      style: textThemeColor.titleMedium,
                    ),
                    if (topConfidence != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        '${formatConfidence(topConfidence)} confidence',
                        style: textThemeColor.bodyMedium,
                      ),
                    ],
                    const SizedBox(height: 6),
                    Text(
                      DateFormat('MMM d, y · h:mm a')
                          .format(diagnosis.timestamp),
                      style: textThemeColor.bodySmall
                          ?.copyWith(color: colorGrayDark),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: colorGrayDark),
            ],
          ),
        ),
      ),
    );
  }
}
