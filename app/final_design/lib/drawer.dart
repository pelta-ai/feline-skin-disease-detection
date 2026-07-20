import 'package:flutter/material.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/utils/profile_picture.dart';

Drawer createDrawer(BuildContext context, String currentScreen) {
  return Drawer(
    backgroundColor: colorMain,
    child: ListView(
      padding: EdgeInsets.zero,
      children: [
        Padding(
          padding: const EdgeInsets.only(top: 20),
        ),
        const ProfileAvatar(radius: 30),
        Padding(
          padding: const EdgeInsets.only(top: 20),
        ),
        ListTile(
            leading: Icon(Icons.home, color: colorWhite, size: 24.0),
            title: Text(
              "Home",
              style: textThemeWhite.titleSmall,
            ),
            onTap: () {
              if (ModalRoute.of(context)?.settings.name == '/home') {
                Navigator.of(context).pop();
              } else {
                Navigator.pushReplacementNamed(context, '/home');
              }
            }),
        // ListTile(
        //     leading: Icon(Icons.bolt, color: colorWhite, size: 24.0),
        //     title: Text(
        //       "Streak",
        //       style: textThemeWhite.titleSmall,
        //     ),
        //     onTap: () {
        //       if (ModalRoute.of(context)?.settings.name == '/streak') {
        //         Navigator.of(context).pop();
        //       } else {
        //         Navigator.pushReplacementNamed(context, '/streak');
        //       }
        //     }),
        ListTile(
            leading: Icon(Icons.newspaper, color: colorWhite, size: 24.0),
            title: Text(
              "Recent Diagnosis",
              style: textThemeWhite.titleSmall,
            ),
            onTap: () {
              if (ModalRoute.of(context)?.settings.name ==
                  '/recent_diagnosis') {
                Navigator.of(context).pop();
              } else {
                Navigator.pushReplacementNamed(context, '/recent_diagnosis');
              }
            }),
        ListTile(
            leading: Icon(Icons.settings, color: colorWhite, size: 24.0),
            title: Text(
              "Settings",
              style: textThemeWhite.titleSmall,
            ),
            onTap: () {
              Navigator.of(context).pop(); // Close drawer first
              Navigator.pushNamed(context, '/settings');
            }),
      ],
    ),
  );
}
