import 'package:final_design/diagnosis_store.dart';
import 'package:final_design/streak_data.dart';

/// Clears all in-memory, per-user state held for the current session.
///
/// [DiagnosisStore] and [StreakData] keep their data in static fields that live
/// for the whole app process, so without an explicit reset one account's data
/// (scan history, streak calendar) would leak into the next account signed in
/// on the same device. Call this on every sign-out, and again right after a
/// successful sign-in/sign-up as a safeguard against any path that skipped it.
void clearUserSession() {
  DiagnosisStore.clear();
  StreakData.clear();
}
