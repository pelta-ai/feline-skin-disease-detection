import 'package:flutter/material.dart';

/// Width at or above which we show the wide "web" layout (sidebar + wide
/// content). Below it, users get the mobile layout.
const double kWebBreakpoint = 900;

bool isWide(BuildContext context) =>
    MediaQuery.of(context).size.width >= kWebBreakpoint;

/// Centers a mobile screen in a phone-width column on a neutral backdrop, so a
/// non-web-optimized screen never stretches full width on desktop. On real
/// phones (<= 480 logical px) it's a no-op passthrough.
class PhoneFrame extends StatelessWidget {
  final Widget child;
  const PhoneFrame({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    const maxWidth = 480.0;
    if (width <= maxWidth) return child;
    return ColoredBox(
      color: const Color(0xFF2B2723), // warm dark backdrop
      child: Center(
        child: ClipRect(
          child: SizedBox(
            width: maxWidth,
            child: MediaQuery(
              data: MediaQuery.of(context)
                  .copyWith(size: Size(maxWidth, MediaQuery.of(context).size.height)),
              child: child,
            ),
          ),
        ),
      ),
    );
  }
}
