import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:final_design/utils/constants.dart';

/// Full text of the medical disclaimer the user must acknowledge once.
///
/// Public so the settings screen can show it again on demand.
const String disclaimerBody =
    "Pelta is a screening tool, not a diagnosis. It uses AI to flag possible "
    "skin conditions in cats and can be wrong, including missing serious "
    "problems or flagging healthy skin. It does not replace an exam by a "
    "licensed veterinarian. Do not use it to start, stop, or delay treatment. "
    "If your cat seems unwell, in pain, or is getting worse, contact a vet. In "
    "an emergency, go to an emergency vet clinic right away.";

const String disclaimerConfirm =
    "By continuing you confirm you understand Pelta gives no guarantees and "
    "creates no veterinarian-client-patient relationship.";

/// Gates its [child] behind a one-time medical-disclaimer acknowledgement.
///
/// The acceptance flag is persisted with [SharedPreferences], so the disclaimer
/// is shown once and never again (unless the app data is cleared).
class DisclaimerGate extends StatefulWidget {
  final Widget child;

  const DisclaimerGate({super.key, required this.child});

  @override
  State<DisclaimerGate> createState() => _DisclaimerGateState();
}

class _DisclaimerGateState extends State<DisclaimerGate> {
  // Versioned key so the disclaimer can be re-shown if the wording changes.
  static const String _prefsKey = 'medical_disclaimer_accepted_v1';

  // null = still loading; false = not accepted; true = accepted.
  bool? _accepted;

  @override
  void initState() {
    super.initState();
    _loadAcceptance();
  }

  Future<void> _loadAcceptance() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;
    setState(() {
      _accepted = prefs.getBool(_prefsKey) ?? false;
    });
  }

  Future<void> _accept() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_prefsKey, true);
    if (!mounted) return;
    setState(() {
      _accepted = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_accepted == null) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator(color: colorMain)),
      );
    }
    if (_accepted == false) {
      return DisclaimerScreen(onAccept: _accept);
    }
    return widget.child;
  }
}

/// The consent screen shown by [DisclaimerGate] until the user acknowledges it.
///
/// With [onAccept] omitted the screen becomes a read-only re-read of the
/// disclaimer — used by the settings screen, where consent was already given.
class DisclaimerScreen extends StatelessWidget {
  final Future<void> Function()? onAccept;

  const DisclaimerScreen({super.key, this.onAccept});

  @override
  Widget build(BuildContext context) {
    final bodyStyle = textThemeColor.bodyLarge?.copyWith(
      fontWeight: FontWeight.w400,
      fontSize: 15,
      height: 1.5,
    );

    return Scaffold(
      backgroundColor: colorMainLight,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 24, 24, 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 8),
                      Center(
                        child: Icon(
                          Icons.health_and_safety_outlined,
                          size: 56,
                          color: colorPrimary,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        "Medical Disclaimer",
                        style: textThemeColor.displayMedium?.copyWith(
                          fontSize: 26,
                        ),
                      ),
                      const SizedBox(height: 20),
                      Text(disclaimerBody, style: bodyStyle),
                      const SizedBox(height: 20),
                      Text(
                        disclaimerConfirm,
                        style: bodyStyle?.copyWith(fontWeight: FontWeight.w600),
                      ),
                      const SizedBox(height: 8),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: onAccept ?? () => Navigator.of(context).pop(),
                style: TextButton.styleFrom(
                  backgroundColor: colorPrimary,
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: Text(
                  onAccept != null ? "I Understand & Continue" : "Close",
                  style: textThemeWhite.titleSmall?.copyWith(fontSize: 14),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}