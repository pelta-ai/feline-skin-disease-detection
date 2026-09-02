import 'dart:developer';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'package:final_design/auth/index.dart';
import 'package:final_design/disclaimer.dart';
import 'package:final_design/utils/app_config.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/utils/custom_app_bar.dart';
import 'package:final_design/utils/session.dart';
import 'package:final_design/utils/profile_picture.dart';
import 'package:final_design/utils/responsive.dart';
import 'package:final_design/web_shell.dart';

/// Account and app settings.
///
/// Reached from the drawer. The user is always signed in here — the screen sits
/// behind [AuthWrapper] — so it offers account management rather than sign-in.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  /// Guards the password-reset row so a slow network can't queue several mails.
  bool _sendingReset = false;

  @override
  void initState() {
    super.initState();
    ProfilePicture.load();
  }

  void _toast(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), duration: const Duration(seconds: 3)),
    );
  }

  // ============================================
  // Profile picture
  // ============================================

  Future<void> _changePicture(ImageSource source) async {
    try {
      final changed = await ProfilePicture.pickFrom(source);
      if (changed) _toast('Profile picture updated');
    } on StateError catch (e) {
      // Desktop image_picker implementations have no camera delegate, so
      // ImageSource.camera throws instead of returning null.
      log('Camera unavailable for profile picture: $e');
      _toast('Camera is not available on this device.');
    } catch (e) {
      // Log the real cause — a single catch-all toast makes failures like the
      // one above impossible to tell apart.
      log('Could not save profile picture: $e');
      _toast(AppConfig.isDevelopment
          // Surfaced in dev builds only: without it the cause is invisible
          // unless you happen to be watching the console.
          ? 'Could not save image: $e'
          : 'Could not save that image. Please try another.');
    }
  }

  /// Bottom sheet offering camera, gallery, and (when set) removal.
  Future<void> _showPictureOptions() async {
    final hasPicture = ProfilePicture.notifier.value != null;
    // Desktop builds have no camera support, so offering it would only ever
    // produce an error.
    final hasCamera = ImagePicker().supportsImageSource(ImageSource.camera);

    await showModalBottomSheet<void>(
      context: context,
      backgroundColor: colorMainLight,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (sheetContext) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 8),
            if (hasCamera)
              ListTile(
                leading: const Icon(Icons.photo_camera_outlined,
                    color: colorGrayDark),
                title: Text('Take a photo', style: textThemeColor.bodyLarge),
                onTap: () {
                  Navigator.of(sheetContext).pop();
                  _changePicture(ImageSource.camera);
                },
              ),
            ListTile(
              leading:
                  const Icon(Icons.photo_library_outlined, color: colorGrayDark),
              title: Text('Choose from gallery',
                  style: textThemeColor.bodyLarge),
              onTap: () {
                Navigator.of(sheetContext).pop();
                _changePicture(ImageSource.gallery);
              },
            ),
            if (hasPicture)
              ListTile(
                leading: const Icon(Icons.delete_outline, color: colorRed),
                title: Text(
                  'Remove picture',
                  style: textThemeColor.bodyLarge?.copyWith(color: colorRed),
                ),
                onTap: () async {
                  Navigator.of(sheetContext).pop();
                  await ProfilePicture.remove();
                  _toast('Profile picture removed');
                },
              ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  // ============================================
  // Display name
  // ============================================

  Future<void> _editDisplayName() async {
    final controller =
        TextEditingController(text: auth.currentUserDisplayName ?? '');

    final newName = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: colorMainLight,
        title: Text('Display name', style: textThemeColor.titleMedium),
        content: TextField(
          controller: controller,
          autofocus: true,
          textCapitalization: TextCapitalization.words,
          style: textThemeColor.bodyLarge,
          decoration: const InputDecoration(hintText: 'Your name'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: Text('Cancel',
                style: textThemeColor.bodyLarge?.copyWith(color: colorGrayDark)),
          ),
          TextButton(
            onPressed: () =>
                Navigator.of(dialogContext).pop(controller.text.trim()),
            child: Text('Save', style: textThemeColor.bodyLarge),
          ),
        ],
      ),
    );

    if (newName == null || newName.isEmpty) return;
    if (newName == auth.currentUserDisplayName) return;

    final result = await auth.updateDisplayName(newName);
    if (!mounted) return;

    if (result.success) {
      // Rebuild so the header picks up the new name.
      setState(() {});
      _toast('Display name updated');
    } else {
      _toast(result.errorMessage ?? 'Could not update display name');
    }
  }

  // ============================================
  // Password / sign out
  // ============================================

  Future<void> _sendPasswordReset() async {
    final email = auth.currentUserEmail;
    if (email == null) {
      _toast('No email address on this account');
      return;
    }

    setState(() => _sendingReset = true);
    final result = await auth.sendPasswordResetEmail(email);
    if (!mounted) return;
    setState(() => _sendingReset = false);

    _toast(result.success
        ? 'Password reset link sent to $email'
        : result.errorMessage ?? 'Could not send reset email');
  }

  Future<void> _confirmSignOut() async {
    final shouldSignOut = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: colorMainLight,
        title: Text('Sign out?', style: textThemeColor.titleMedium),
        content: Text(
          'You will need to sign in again to run a scan.',
          style: textThemeColor.bodyMedium,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: Text('Cancel',
                style: textThemeColor.bodyLarge?.copyWith(color: colorGrayDark)),
          ),
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: Text('Sign out',
                style: textThemeColor.bodyLarge?.copyWith(color: colorRed)),
          ),
        ],
      ),
    );

    if (shouldSignOut != true) return;

    await auth.signOut();
    // Wipe this session's in-memory data so the next account on this device
    // can't see the previous user's scans or streak.
    clearUserSession();
    if (!mounted) return;

    // Drop the whole history so back can't return to a signed-in screen.
    Navigator.of(context)
        .pushNamedAndRemoveUntil('/login', (route) => false);
  }

  // ============================================
  // Build
  // ============================================

  @override
  Widget build(BuildContext context) {
    if (isWide(context)) return _buildWide(context);
    return _buildMobile(context);
  }

  Widget _buildMobile(BuildContext context) {
    return Scaffold(
      backgroundColor: colorMainLight,
      appBar: CustomAppBar(
        title: "Settings",
        height: 120,
        action: IconButton(
          icon: const Icon(Icons.close, color: colorWhite),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 24, 20, 32),
        children: _contentChildren(context),
      ),
    );
  }

  Widget _buildWide(BuildContext context) {
    return WebShell(
      active: '/settings',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("Settings", style: textThemeColor.displayMedium),
          const SizedBox(height: 24),
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 640),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: _contentChildren(context),
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _contentChildren(BuildContext context) {
    return [
          _ProfileHeader(onTapPicture: _showPictureOptions),
          const SizedBox(height: 28),

          _SectionLabel('Account'),
          _SettingsTile(
            icon: Icons.person_outline,
            title: 'Display name',
            subtitle: (auth.currentUserDisplayName?.isNotEmpty ?? false)
                ? auth.currentUserDisplayName
                : 'Not set',
            onTap: _editDisplayName,
          ),
          _SettingsTile(
            icon: Icons.mail_outline,
            title: 'Email',
            subtitle: auth.currentUserEmail ?? 'Unknown',
            // Changing an email address re-runs verification, so it is left out
            // until that flow is designed.
            trailing: auth.isEmailVerified
                ? const Icon(Icons.verified, color: colorGreen, size: 20)
                : null,
          ),
          _SettingsTile(
            icon: Icons.lock_outline,
            title: 'Change password',
            subtitle: _sendingReset
                ? 'Sending…'
                : 'Send a reset link to your email',
            onTap: _sendingReset ? null : _sendPasswordReset,
          ),

          const SizedBox(height: 20),
          _SectionLabel('About'),
          _SettingsTile(
            icon: Icons.health_and_safety_outlined,
            title: 'Medical disclaimer',
            subtitle: 'Read it again',
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute<void>(
                builder: (_) => const DisclaimerScreen(),
              ),
            ),
          ),
          _SettingsTile(
            icon: Icons.info_outline,
            title: 'Version',
            subtitle:
                '${AppConfig.appName} ${AppConfig.appVersion} (${AppConfig.appBuildNumber})',
          ),

          const SizedBox(height: 28),
          TextButton(
            onPressed: _confirmSignOut,
            style: TextButton.styleFrom(
              backgroundColor: colorPrimary,
              padding: const EdgeInsets.symmetric(vertical: 18),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(30),
              ),
            ),
            child: Text(
              'Sign Out',
              style: textThemeWhite.titleSmall?.copyWith(fontSize: 14),
            ),
          ),
    ];
  }
}

/// Avatar plus name/email, with the avatar tappable to change the picture.
class _ProfileHeader extends StatelessWidget {
  final VoidCallback onTapPicture;

  const _ProfileHeader({required this.onTapPicture});

  @override
  Widget build(BuildContext context) {
    final name = auth.currentUserDisplayName;

    return Column(
      children: [
        GestureDetector(
          onTap: onTapPicture,
          child: Stack(
            alignment: Alignment.bottomRight,
            children: [
              const ProfileAvatar(radius: 48),
              Container(
                padding: const EdgeInsets.all(6),
                decoration: const BoxDecoration(
                  color: colorMain,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.edit, size: 16, color: colorWhite),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        Text(
          (name?.isNotEmpty ?? false) ? name! : 'Pelta user',
          style: textThemeColor.titleMedium,
        ),
        const SizedBox(height: 2),
        Text(
          auth.currentUserEmail ?? '',
          style: textThemeColor.bodyMedium,
        ),
      ],
    );
  }
}

/// Small caps heading that separates groups of rows.
class _SectionLabel extends StatelessWidget {
  final String text;

  const _SectionLabel(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 8),
      child: Text(
        text.toUpperCase(),
        style: textThemeColor.bodySmall?.copyWith(
          color: colorGrayDark,
          fontWeight: FontWeight.w600,
          letterSpacing: 1.1,
        ),
      ),
    );
  }
}

/// One settings row. Rows without [onTap] are informational only.
class _SettingsTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? subtitle;
  final VoidCallback? onTap;
  final Widget? trailing;

  const _SettingsTile({
    required this.icon,
    required this.title,
    this.subtitle,
    this.onTap,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: colorWhite,
        borderRadius: BorderRadius.circular(14),
      ),
      child: ListTile(
        shape:
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        leading: Icon(icon, color: colorGrayDark, size: 22),
        title: Text(title, style: textThemeColor.bodyLarge),
        subtitle: subtitle == null
            ? null
            : Text(subtitle!, style: textThemeColor.bodyMedium),
        trailing: trailing ??
            (onTap == null
                ? null
                : const Icon(Icons.chevron_right,
                    color: colorGrayDark, size: 20)),
        onTap: onTap,
      ),
    );
  }
}
