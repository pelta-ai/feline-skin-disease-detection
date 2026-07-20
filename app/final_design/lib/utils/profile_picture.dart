import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:final_design/utils/constants.dart';

/// Local-only profile picture storage.
///
/// The image is copied into the app's documents directory and the resulting
/// path is persisted with [SharedPreferences]. Nothing is uploaded — cloud
/// storage is dormant, so the picture lives on the device only and does not
/// follow the user to a new install or a second device.
///
/// [notifier] lets widgets rebuild when the picture changes, so the drawer
/// avatar and the settings screen stay in sync without extra plumbing.
class ProfilePicture {
  ProfilePicture._();

  static const String _prefsKey = 'profile_picture_path';

  /// Current picture path, or null when none is set.
  ///
  /// Widgets can listen to this directly via [ValueListenableBuilder].
  static final ValueNotifier<String?> notifier = ValueNotifier<String?>(null);

  static bool _loaded = false;

  /// Loads the saved path into [notifier].
  ///
  /// Safe to call repeatedly; the work only happens once. A saved path whose
  /// file has since disappeared (e.g. the OS cleared app data) is treated as
  /// "no picture" and the stale preference is cleared.
  static Future<void> load() async {
    if (_loaded) return;
    _loaded = true;

    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_prefsKey);
    if (saved == null) return;

    if (await File(saved).exists()) {
      notifier.value = saved;
    } else {
      await prefs.remove(_prefsKey);
    }
  }

  /// Picks an image from [source] and stores it as the profile picture.
  ///
  /// Returns true when a new picture was saved, false when the user cancelled.
  /// Throws if the file could not be copied, so callers can surface an error.
  static Future<bool> pickFrom(ImageSource source) async {
    final picked = await ImagePicker().pickImage(
      source: source,
      // Avatars render small; downscaling keeps the copy well under a megabyte.
      maxWidth: 512,
      maxHeight: 512,
      imageQuality: 85,
    );
    if (picked == null) return false;

    final dir = await getApplicationDocumentsDirectory();
    final extension = picked.path.split('.').last;
    // A unique filename each time, because Flutter's image cache keys on path:
    // reusing one name would keep showing the previous picture.
    final stamp = DateTime.now().millisecondsSinceEpoch;
    final destination = File('${dir.path}/profile_picture_$stamp.$extension');

    await destination.writeAsBytes(await picked.readAsBytes());

    final previous = notifier.value;

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefsKey, destination.path);
    notifier.value = destination.path;

    await _deleteQuietly(previous);
    return true;
  }

  /// Removes the current profile picture, falling back to the default avatar.
  static Future<void> remove() async {
    final previous = notifier.value;
    if (previous == null) return;

    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_prefsKey);
    notifier.value = null;

    await _deleteQuietly(previous);
  }

  /// Deletes a superseded picture. Failure here is not worth surfacing — the
  /// new picture is already saved and the leftover file is harmless.
  static Future<void> _deleteQuietly(String? path) async {
    if (path == null) return;
    try {
      final file = File(path);
      if (await file.exists()) await file.delete();
    } catch (_) {
      // Ignored on purpose.
    }
  }
}

/// Circular avatar that shows the saved profile picture, or a person icon when
/// none is set.
///
/// Listens to [ProfilePicture.notifier], so every avatar in the app updates the
/// moment the picture changes.
class ProfileAvatar extends StatelessWidget {
  final double radius;

  const ProfileAvatar({super.key, this.radius = 30});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String?>(
      valueListenable: ProfilePicture.notifier,
      builder: (context, path, _) {
        return CircleAvatar(
          radius: radius,
          backgroundColor: colorMainLight,
          backgroundImage: path == null ? null : FileImage(File(path)),
          child: path == null
              ? Icon(
                  Icons.person,
                  size: radius,
                  color: colorGrayDark,
                )
              : null,
        );
      },
    );
  }
}
