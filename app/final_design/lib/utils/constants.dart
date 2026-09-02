import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
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

// ---------------------------------------------------------------------------
// Color palette — warm, friendly, cohesive (Material 3 evolution of the
// original beige/green identity). Existing names are preserved so every screen
// picks up the refreshed look automatically; a few new tokens are added for
// modern components (colorPrimary + the header gradient).
// ---------------------------------------------------------------------------

const colorWhite = Colors.white;

// Brand — warm terracotta primary (CTAs, headers). Deep enough for white text.
const colorPrimary = Color(0xFFB85C38);
const colorPrimaryLight = Color(0xFFD98A5C);

// Warm neutral surfaces
const colorCream = Color(0xFFFFF8F1); // app background
const colorSurface = Color(0xFFFFFFFF); // cards

// Text
const colorBlack = Color(0xFF2B2723); // primary text (warm near-black)
const colorGrayDark = Color(0xFF6E655C); // secondary text (readable warm grey)
const colorGray = Color(0xFFF3EADF); // input fill / subtle surface
const colorBorder = Color(0xFFE7DACB); // hairline borders

// Status
const colorGreen = Color(0xFF12B76A); // positive / healthy
const colorYellow = Color(0xFFF5B942); // caution
const colorRed = Color(0xFFEF4444); // concern

// Warm accents (kept for existing references)
const colorMain = Color(0xFFF6E0CC); // soft peach accent surface
const colorMainLight = colorCream;
const colorMainTransparent = Color(0xFFF3DBC2);

// Header gradient (warm, used by CustomAppBar)
const headerGradient = LinearGradient(
  colors: [colorPrimary, colorPrimaryLight],
  begin: Alignment.topLeft,
  end: Alignment.bottomRight,
);

TextTheme textThemeColor = TextTheme(
  displayMedium: GoogleFonts.poppins(
      color: colorBlack, fontWeight: FontWeight.w700, fontSize: 34),
  titleMedium: GoogleFonts.poppins(
      color: colorBlack, fontWeight: FontWeight.w600, fontSize: 18),
  bodyLarge: GoogleFonts.poppins(
      color: colorBlack, fontWeight: FontWeight.w600, fontSize: 15),
  bodyMedium: GoogleFonts.poppins(
      color: colorGrayDark, fontWeight: FontWeight.w400, fontSize: 14),
  bodySmall: GoogleFonts.poppins(
      color: colorGrayDark, fontWeight: FontWeight.w500, fontSize: 13),
);

TextTheme textThemeWhite = TextTheme(
  displayMedium: GoogleFonts.poppins(
      color: colorWhite, fontWeight: FontWeight.w700, fontSize: 34),
  displaySmall: GoogleFonts.poppins(
      color: colorWhite, fontWeight: FontWeight.w700, fontSize: 22),
  titleSmall: GoogleFonts.poppins(
      color: colorWhite, fontWeight: FontWeight.w600, fontSize: 15),
  bodySmall: GoogleFonts.poppins(
      color: colorWhite, fontWeight: FontWeight.w400, fontSize: 13),
);
