import 'package:final_design/utils/constants.dart';
import 'package:final_design/streak_data.dart';
import 'package:flutter/material.dart';

class StaticMiniCalendar extends StatelessWidget {
  final StreakData streakData = StreakData();

  StaticMiniCalendar({super.key});

  List<int> getLast7DaysDateNumbers() {
    final today = DateTime.now();
    return List.generate(7, (index) {
      final date = today.subtract(Duration(days: 6 - index));
      return date.day;
    });
  }

  List<Widget> getWeekWidgets() {
    List<Widget> dateWidgets = [];

    for (var i = 0; i < 7; i++) {
      dateWidgets.add(
        CircleAvatar(
            radius: 21,
            backgroundColor: streakData.getColor(
                DateTime.utc(DateTime.now().year, DateTime.now().month,
                    getLast7DaysDateNumbers()[i]),
                COLOR_GRAY),
            child: Text(getLast7DaysDateNumbers()[i].toString(),
                style: textThemeWhite.titleSmall)),
      );
    }

    return dateWidgets;
  }

  int getMonth() {
    var today = DateTime.now();
    return today.month;
  }

  String getYear() {
    var today = DateTime.now();
    return today.year.toString();
  }

  String getMonthName(int monthNumber) {
    const months = [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December'
    ];

    return months[monthNumber - 1]; // months is 0-indexed
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.only(top: 25),
          child: Text("${getMonthName(getMonth())}, ${getYear()}",
              style: textThemeWhite.titleSmall),
        ),
        Padding(
            padding: const EdgeInsets.symmetric(horizontal: 25, vertical: 12),
            child: SizedBox(
                width: double.infinity,
                height: 60,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: getWeekWidgets(),
                )))
      ],
    );
  }
}
