import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/auth/index.dart';

/// Wide-screen split layout for pre-auth screens (login / sign-up): a warm
/// brand panel on the left and the form on the right. On phones the caller
/// falls back to the mobile single-column form instead.
class AuthWebScaffold extends StatelessWidget {
  final Widget form;
  const AuthWebScaffold({super.key, required this.form});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          // Left: brand / hero panel
          Expanded(
            child: Container(
              decoration: const BoxDecoration(gradient: headerGradient),
              padding: const EdgeInsets.all(56),
              alignment: Alignment.centerLeft,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('🐱', style: TextStyle(fontSize: 64)),
                  const SizedBox(height: 20),
                  Text('Pelta',
                      style: GoogleFonts.poppins(
                          color: colorWhite,
                          fontWeight: FontWeight.w700,
                          fontSize: 46)),
                  const SizedBox(height: 14),
                  SizedBox(
                    width: 380,
                    child: Text(
                      "Early detection for your cat's skin health.",
                      style: GoogleFonts.poppins(
                          color: colorWhite,
                          fontSize: 18,
                          fontWeight: FontWeight.w400,
                          height: 1.45),
                    ),
                  ),
                ],
              ),
            ),
          ),
          // Right: the form
          Expanded(
            child: Container(
              color: colorCream,
              alignment: Alignment.center,
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 460),
                child: form,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Wide-screen ("web") layout: a persistent left navigation sidebar plus a
/// centered wide content area. Used by screens on desktop-width windows.
class WebShell extends StatelessWidget {
  /// Route name of the active section, used to highlight the sidebar item.
  final String active;
  final Widget child;

  const WebShell({super.key, required this.active, required this.child});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: colorCream,
      body: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _Sidebar(active: active),
          Expanded(
            child: SingleChildScrollView(
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 1040),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 40, vertical: 32),
                    child: child,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _NavItem {
  final String label;
  final IconData icon;
  final String route;
  const _NavItem(this.label, this.icon, this.route);
}

const _navItems = [
  _NavItem('Home', Icons.home_outlined, '/home'),
  _NavItem('Recent Diagnosis', Icons.history, '/recent_diagnosis'),
  // Streak is dormant for now — screen and route are kept but not linked.
  // _NavItem('Streak', Icons.local_fire_department_outlined, '/streak'),
  _NavItem('Settings', Icons.settings_outlined, '/settings'),
];

class _Sidebar extends StatelessWidget {
  final String active;
  const _Sidebar({required this.active});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 264,
      decoration: const BoxDecoration(
        color: colorSurface,
        border: Border(right: BorderSide(color: colorBorder)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(24, 34, 24, 28),
            child: Row(
              children: [
                const Text('🐱', style: TextStyle(fontSize: 26)),
                const SizedBox(width: 10),
                Text('Pelta',
                    style: textThemeColor.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w700, fontSize: 22)),
              ],
            ),
          ),
          for (final item in _navItems)
            _SideLink(item: item, active: item.route == active),
          const Spacer(),
          const Divider(height: 1, color: colorBorder),
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextButton.icon(
              onPressed: () async {
                await auth.signOut();
                if (context.mounted) {
                  Navigator.of(context)
                      .pushNamedAndRemoveUntil('/login', (route) => false);
                }
              },
              icon: const Icon(Icons.logout, size: 20, color: colorGrayDark),
              label: Align(
                alignment: Alignment.centerLeft,
                child: Text('Log out',
                    style: textThemeColor.bodyLarge?.copyWith(
                        color: colorGrayDark, fontWeight: FontWeight.w500)),
              ),
              style: TextButton.styleFrom(
                padding:
                    const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                alignment: Alignment.centerLeft,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SideLink extends StatelessWidget {
  final _NavItem item;
  final bool active;
  const _SideLink({required this.item, required this.active});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
      child: Material(
        color: active ? colorMain : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: active
              ? null
              : () {
                  if (item.route == '/home') {
                    Navigator.of(context).pushNamedAndRemoveUntil(
                        '/home', (route) => false);
                  } else {
                    Navigator.of(context).pushNamed(item.route);
                  }
                },
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
            child: Row(
              children: [
                Icon(item.icon,
                    size: 20, color: active ? colorPrimary : colorGrayDark),
                const SizedBox(width: 12),
                Text(item.label,
                    style: textThemeColor.bodyLarge?.copyWith(
                        color: active ? colorPrimary : colorBlack,
                        fontWeight:
                            active ? FontWeight.w600 : FontWeight.w500)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
