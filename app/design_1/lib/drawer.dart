import 'package:flutter/material.dart';
import 'package:design_1/utils/constants.dart';

Drawer createDrawer(BuildContext context, String currentScreen) {
  return Drawer(
    backgroundColor: COLOR_MAIN,
    child: ListView(
      padding: EdgeInsets.zero,
      children: [
        Padding(
          padding: const EdgeInsets.only(top: 20),
        ),
        CircleAvatar(
          radius: 30,
          backgroundImage: AssetImage("assets/images/pfp.jpg"),
          //backgroundColor: Colors.grey[200],
        ),
        Padding(
          padding: const EdgeInsets.only(top: 20),
        ),
        ListTile(
          leading: Icon(
            Icons.home,
            color: COLOR_WHITE,
            size: 24.0
          ),
          title: Text(
            "Home",
            style: textThemeWhite.titleSmall,
            ),
          onTap: () {
            if (ModalRoute.of(context)?.settings.name == '/home') {
              Navigator.of(context).pop();
            }
            else {
              Navigator.pushReplacementNamed(context, '/home');
            }
          }
        ),
        ListTile(
          leading: Icon(
            Icons.bolt,
            color: COLOR_WHITE,
            size: 24.0
          ),
          title: Text(
            "Streak",
            style: textThemeWhite.titleSmall,
            ),
          onTap: () {
            if (ModalRoute.of(context)?.settings.name == '/streak') {
              Navigator.of(context).pop();
            }
            else {
              Navigator.pushReplacementNamed(context, '/streak');
            }
          }
        ),
        ListTile(
          leading: Icon(
            Icons.newspaper,
            color: COLOR_WHITE,
            size: 24.0
          ),
          title: Text(
            "Recent Diagnosis",
            style: textThemeWhite.titleSmall,
            ),
          onTap: () {
            //TODO
          }
        ),
        ListTile(
          leading: Icon(
            Icons.settings,
            color: COLOR_WHITE,
            size: 24.0
          ),
          title: Text(
            "Settings",
            style: textThemeWhite.titleSmall,
            ),
          onTap: () {}
        ),
      ],
    ),
  );
}