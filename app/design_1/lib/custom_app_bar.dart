import 'package:flutter/material.dart';
import 'package:design_1/utils/constants.dart';

class CustomAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final double height;
  final Widget? action;

  const CustomAppBar({super.key, required this.title, required this.height, this.action});

  @override
  Widget build(BuildContext context) {
    return PreferredSize(
      preferredSize: Size.fromHeight(height),
      child: AppBar(
        backgroundColor: COLOR_MAIN,
        elevation: 0,
        automaticallyImplyLeading: false,
        flexibleSpace: Stack(
          children: [
            Center(
              child: Padding(
                padding: const EdgeInsets.only(top: 40), // tweak as needed
                child: Text(
                  title,
                  style: textThemeWhite.displayMedium,
                  textAlign: TextAlign.center,
                ),
              ),
            ),
            if (action != null)
              Positioned(
                top: 40,
                right: 12,
                child: action!,
              ),
          ],
        ),
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(bottom: Radius.circular(20)),
        ),
      ),
    );
  }

  @override
  Size get preferredSize => Size.fromHeight(height);
}