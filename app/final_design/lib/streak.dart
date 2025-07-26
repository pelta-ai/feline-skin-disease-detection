import 'dart:developer';

import 'package:final_design/utils/aws_s3_api.dart';
import 'package:final_design/streak_data.dart';
import 'package:flutter/material.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/drawer.dart';
import 'package:table_calendar/table_calendar.dart';

class StreakScreen extends StatelessWidget {
  const StreakScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
        appBar: PreferredSize(
            preferredSize: Size.fromHeight(getScreenHeight(context) * 0.184),
            child: AppBar(
              backgroundColor: COLOR_MAIN,
              automaticallyImplyLeading: true,
              iconTheme: IconThemeData(color: COLOR_WHITE),
              flexibleSpace: Stack(
                children: [
                  Column(
                    children: [
                      Padding(padding: const EdgeInsets.only(top: 60)),
                      Center(
                          child: Text(
                        "Streak",
                        style: textThemeWhite.displaySmall,
                      )),
                      Center(
                          child: Text(
                        "Current Streak",
                        style: textThemeWhite.titleSmall,
                      )),
                      Center(
                          child: Text(
                        "[Current Streak]",
                        style: textThemeWhite.displaySmall,
                      ))
                    ],
                  )
                ],
              ),
              shape: const RoundedRectangleBorder(
                borderRadius:
                    BorderRadius.vertical(bottom: Radius.circular(20)),
              ),
            )),
        drawer: createDrawer(context, "Streak"),
        body: Streak());
  }
}

class Streak extends StatelessWidget {
  DateTime today = DateTime.now();
  final StreakData streakData = StreakData();

  Streak({super.key});

  Future<void> updateStreak() async {
    if (await S3ApiService.folderExists("$CURRENT_USER/$TODAY_DATE/")) {
      streakData.setStatus(DateTime.now(), "done");
      log("Done");
    }
  }

  bool isStoredDate(DateTime day) {
    return streakData.get().keys.any((d) => isSameDay(d, day));
  }

  @override
  Widget build(BuildContext context) {
    updateStreak();

    return Container(
      padding: const EdgeInsets.only(top: 34, left: 61, right: 61),
      child: Column(
        children: [
          TableCalendar(
            headerStyle:
                HeaderStyle(formatButtonVisible: false, titleCentered: true),
            focusedDay: today,
            firstDay: DateTime.utc(2025, 7, 8),
            lastDay: DateTime.utc(3025, 7, 8),
            calendarStyle: CalendarStyle(isTodayHighlighted: false),
            calendarBuilders:
                CalendarBuilders(defaultBuilder: (context, day, focusedDay) {
              if (isStoredDate(day)) {
                Color bgColor =
                    streakData.getColor(DateTime.now(), Colors.transparent);

                return Container(
                  margin: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: bgColor,
                    shape: BoxShape.circle,
                  ),
                  width: 40,
                  height: 40,
                  child: Center(
                    child: Text(
                      '${day.day}',
                      style: TextStyle(
                        color: bgColor == Colors.transparent
                            ? COLOR_BLACK
                            : COLOR_WHITE,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                );
              }
            }),
          )
        ],
      ),
    );
  }
}
