import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:final_design/auth/index.dart';

double getScreenHeight(BuildContext context) {
  return MediaQuery.of(context).size.height;
}

double getScreenWidth(BuildContext context) {
  return MediaQuery.of(context).size.width;
}

// Date and user info (computed at runtime)
String get todayDate =>
    DateFormat('yyyy-MM-dd').format(DateTime.now()); // ISO 8601 format

/// Current user ID from the auth provider
/// Returns null if not logged in
String? get currentUser => auth.currentUserId;

// Colors - using Dart's recommended lowerCamelCase for constants
const colorWhite = Colors.white;
const colorGray = Color.fromRGBO(143, 142, 142, 0.37);
const colorGrayDark = Color.fromRGBO(77, 76, 76, 1.0);
const colorBlack = Color.fromRGBO(28, 33, 32, 1.0);

const colorGreen = Color.fromRGBO(0, 191, 99, 1.0);
const colorYellow = Color.fromRGBO(255, 222, 89, 1.0);
const colorRed = Color.fromRGBO(255, 49, 49, 1.0);

const colorMain = Color.fromRGBO(235, 207, 176, 1.0);
const colorMainLight = Color.fromRGBO(255, 240, 224, 1.0);
const colorMainTransparent = Color.fromRGBO(243, 219, 194, 1.0);

TextTheme textThemeColor = TextTheme(
  displayMedium: TextStyle(
      color: colorBlack,
      fontWeight: FontWeight.w700,
      fontSize: 40,
      fontFamily: 'Poppins'),
  titleMedium: TextStyle(
      color: colorBlack,
      fontWeight: FontWeight.w600,
      fontSize: 18,
      fontFamily: 'Poppins'),
  bodyLarge: TextStyle(
      color: colorBlack,
      fontWeight: FontWeight.w700,
      fontSize: 14.5,
      fontFamily: 'Poppins'),
  bodyMedium: TextStyle(
      color: colorGrayDark,
      fontWeight: FontWeight.w400,
      fontSize: 12.1,
      fontFamily: 'Poppins'),
  bodySmall: TextStyle(
      color: colorGray,
      fontWeight: FontWeight.w400,
      fontSize: 10.5,
      fontFamily: 'Poppins'),
);

TextTheme textThemeWhite = TextTheme(
  displayMedium: TextStyle(
      color: colorWhite,
      fontWeight: FontWeight.w700,
      fontSize: 40,
      fontFamily: 'Poppins'),
  displaySmall: TextStyle(
      color: colorWhite,
      fontWeight: FontWeight.w700,
      fontSize: 21.7,
      fontFamily: 'Poppins'),
  titleSmall: TextStyle(
      color: colorWhite,
      fontWeight: FontWeight.w700,
      fontSize: 10.5,
      fontFamily: 'Poppins'),
  bodySmall: TextStyle(
      color: colorWhite,
      fontWeight: FontWeight.w400,
      fontSize: 10.5,
      fontFamily: 'Poppins'),
);
