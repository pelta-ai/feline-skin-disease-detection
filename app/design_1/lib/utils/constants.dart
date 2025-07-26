import 'package:flutter/material.dart';

double getScreenHeight(BuildContext context) {
  return MediaQuery.of(context).size.height;
}

double getScreenWidth(BuildContext context) {
  return MediaQuery.of(context).size.width;
}

const COLOR_WHITE = Colors.white;
const COLOR_GRAY = Color.fromRGBO(143, 142, 142, 0.37);
const COLOR_GRAY_DARK = Color.fromRGBO(77, 76, 76, 1.0);
const COLOR_BLACK = Color.fromRGBO(28, 33, 32, 1.0);  

const COLOR_GREEN = Color.fromRGBO(0, 191, 99, 1.0);
const COLOR_YELLOW = Color.fromRGBO(255, 222, 89, 1.0);
const COLOR_RED = Color.fromRGBO(255, 49, 49, 1.0);

const COLOR_MAIN = Color.fromRGBO(235, 207, 176, 1.0);
const COLOR_MAIN_LIGHT = Color.fromRGBO(255, 240, 224, 1.0);
const COLOR_MAIN_TRANSPARENT = Color.fromRGBO(243, 219, 194, 1.0);


TextTheme textThemeColor = TextTheme(
  displayMedium: TextStyle(
    color: COLOR_BLACK, fontWeight: FontWeight.w700, fontSize: 40, fontFamily: 'Poppins'),
  bodyLarge: TextStyle(
    color: COLOR_BLACK, fontWeight: FontWeight.w700, fontSize: 14.5, fontFamily: 'Poppins'),
  bodyMedium: TextStyle(
    color: COLOR_GRAY_DARK, fontWeight: FontWeight.w400, fontSize: 12.1, fontFamily: 'Poppins'),
  bodySmall: TextStyle(
    color: COLOR_GRAY, fontWeight: FontWeight.w400, fontSize: 10.5, fontFamily: 'Poppins'),
);

TextTheme textThemeWhite = TextTheme(
  displayMedium: TextStyle(
    color: COLOR_WHITE, fontWeight: FontWeight.w700, fontSize: 40, fontFamily: 'Poppins'),
  displaySmall: TextStyle(
    color: COLOR_WHITE, fontWeight: FontWeight.w700, fontSize: 21.7, fontFamily: 'Poppins'),
  titleSmall: TextStyle(
    color: COLOR_WHITE, fontWeight: FontWeight.w700, fontSize: 10.5, fontFamily: 'Poppins'),
  bodySmall: TextStyle(
    color: COLOR_WHITE, fontWeight: FontWeight.w400, fontSize: 10.5, fontFamily: 'Poppins'),
);