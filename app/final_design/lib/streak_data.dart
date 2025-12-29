import 'package:final_design/utils/constants.dart';
import 'package:flutter/material.dart';

class StreakData {
  static final Map<DateTime, String> _statusByDay = {};

  Map<DateTime, String> get status => _statusByDay;

  void setStatus(DateTime date, String status) {
    final normalizedDate = DateTime.utc(date.year, date.month, date.day);
    _statusByDay[normalizedDate] = status;
  }

  Map<DateTime, String> get() {
    return _statusByDay;
  }

  String? getStatus(DateTime date) {
    final normalizedDate = DateTime.utc(date.year, date.month, date.day);
    return _statusByDay[normalizedDate];
  }

  Color getColor(DateTime date, Color defaultColor) {
    String? status = getStatus(date);

    switch (status) {
      case "done":
        return colorGreen;
      case "high_risk":
        return colorRed;
      case "low_risk":
        return colorYellow;
      default:
        return defaultColor;
    }
  }

  /// Calculate current streak (consecutive days with "done" status ending today)
  int getCurrentStreak() {
    int streak = 0;
    DateTime checkDate = DateTime.now();

    while (true) {
      final normalizedDate = DateTime.utc(checkDate.year, checkDate.month, checkDate.day);
      final status = _statusByDay[normalizedDate];

      if (status == "done") {
        streak++;
        checkDate = checkDate.subtract(const Duration(days: 1));
      } else {
        break;
      }
    }

    return streak;
  }
}
