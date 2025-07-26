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
        return COLOR_GREEN;
      case "high_risk":
        return COLOR_RED;
      case "low_risk":
        return COLOR_YELLOW;
      default:
        return defaultColor;
    }
  }
}
