import 'package:flutter/material.dart';
import 'package:final_design/utils/constants.dart';

class CustomAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final double height;
  final Widget? action;

  const CustomAppBar(
      {super.key, required this.title, required this.height, this.action});

  @override
  Widget build(BuildContext context) {
    return PreferredSize(
      preferredSize: Size.fromHeight(height),
      child: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        automaticallyImplyLeading: false,
        flexibleSpace: Container(
          decoration: const BoxDecoration(
            gradient: headerGradient,
            borderRadius: BorderRadius.vertical(bottom: Radius.circular(28)),
          ),
          child: Stack(
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
        ),
      ),
    );
  }

  @override
  Size get preferredSize => Size.fromHeight(height);
}
