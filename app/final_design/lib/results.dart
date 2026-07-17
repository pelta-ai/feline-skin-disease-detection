import 'package:flutter/material.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/drawer.dart';

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
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Text(
          "No recent diagnoses to show.",
          style: textThemeColor.bodyLarge,
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}
