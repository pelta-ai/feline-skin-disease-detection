class StreakData {
  final Map<DateTime, String> _statusByDay = {};

  Map<DateTime, String> get status => _statusByDay;

  void setStatus(DateTime date, String status) {
    final normalizedDate = DateTime.utc(date.year, date.month, date.day);
    _statusByDay[normalizedDate] = status;
  }

  String? getStatus(DateTime date) {
    final normalizedDate = DateTime.utc(date.year, date.month, date.day);
    return _statusByDay[normalizedDate];
  }
}