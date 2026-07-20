import 'dart:convert';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:final_design/utils/constants.dart';

/// Local-only profile picture storage.
///
/// The picture is held as bytes and persisted base64-encoded in
/// [SharedPreferences]. Nothing is uploaded — cloud storage is dormant, so the
/// picture stays on this device and does not follow the user elsewhere.
///
/// Bytes rather than a file on disk: `path_provider` and `dart:io` have no web
/// implementation, so a file-based approach throws `MissingPluginException` in
/// the browser. `shared_preferences` works on every platform the app targets.
///
/// [notifier] lets widgets rebuild when the picture changes, so the drawer
/// avatar and the settings screen stay in sync without extra plumbing.
class ProfilePicture {
  ProfilePicture._();

  static const String _prefsKey = 'profile_picture_bytes';

  /// Longest edge of the stored image, in pixels.
  ///
  /// Avatars render small, and the encoded result has to fit in browser
  /// local storage alongside everything else, so the source is downscaled
  /// rather than stored at full camera resolution.
  static const int _maxEdge = 256;

  /// Ceiling on what may be persisted when downscaling fails and the original
  /// is used instead. Base64 inflates by ~4/3, and browser local storage is
  /// only a few megabytes in total.
  static const int _maxStoredBytes = 1024 * 1024;

  /// Current picture bytes, or null when none is set.
  ///
  /// Widgets can listen to this directly via [ValueListenableBuilder].
  static final ValueNotifier<Uint8List?> notifier =
      ValueNotifier<Uint8List?>(null);

  static bool _loaded = false;

  /// Loads the saved picture into [notifier].
  ///
  /// Safe to call repeatedly; the work only happens once. Unreadable saved data
  /// is discarded rather than left to fail on every render.
  static Future<void> load() async {
    if (_loaded) return;
    _loaded = true;

    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_prefsKey);
    if (saved == null) return;

    try {
      notifier.value = base64Decode(saved);
    } catch (_) {
      await prefs.remove(_prefsKey);
    }
  }

  /// Picks an image from [source] and stores it as the profile picture.
  ///
  /// Returns true when a new picture was saved, false when the user cancelled.
  /// Throws if the image could not be decoded or stored, so callers can surface
  /// an error.
  static Future<bool> pickFrom(ImageSource source) async {
    final picked = await ImagePicker().pickImage(source: source);
    if (picked == null) return false;

    final original = await picked.readAsBytes();

    // Downscale in Dart rather than via ImagePicker's maxWidth/maxHeight: the
    // web and desktop implementations silently ignore those options, so the
    // full-resolution original would be what we tried to store.
    Uint8List stored;
    try {
      stored = await _downscale(original);
    } catch (e) {
      // Downscaling is an optimisation, not a requirement. Keep the original
      // when it is small enough to persist, rather than failing outright.
      if (original.lengthInBytes > _maxStoredBytes) rethrow;
      stored = original;
    }

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefsKey, base64Encode(stored));
    notifier.value = stored;
    return true;
  }

  /// Removes the current profile picture, falling back to the default avatar.
  static Future<void> remove() async {
    if (notifier.value == null) return;

    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_prefsKey);
    notifier.value = null;
  }

  /// Re-encodes [bytes] so the longest edge is at most [_maxEdge].
  ///
  /// Deliberately built from decode + canvas draw + [ui.Image.toByteData]:
  /// `ImageDescriptor.width` and friends throw `UnsupportedError` on web, and
  /// the resize options on `instantiateImageCodec` are not honoured everywhere.
  /// Drawing through a [ui.PictureRecorder] behaves the same on every platform.
  static Future<Uint8List> _downscale(Uint8List bytes) async {
    final codec = await ui.instantiateImageCodec(bytes);
    final frame = await codec.getNextFrame();
    final source = frame.image;

    final width = source.width;
    final height = source.height;
    final longestEdge = width > height ? width : height;

    // Already small enough — keep the original encoding, which is usually
    // smaller than the PNG produced below.
    if (longestEdge <= _maxEdge) {
      source.dispose();
      codec.dispose();
      return bytes;
    }

    final scale = _maxEdge / longestEdge;
    final targetWidth = (width * scale).round();
    final targetHeight = (height * scale).round();

    final recorder = ui.PictureRecorder();
    ui.Canvas(recorder).drawImageRect(
      source,
      ui.Rect.fromLTWH(0, 0, width.toDouble(), height.toDouble()),
      ui.Rect.fromLTWH(0, 0, targetWidth.toDouble(), targetHeight.toDouble()),
      ui.Paint()..filterQuality = ui.FilterQuality.medium,
    );

    final picture = recorder.endRecording();
    final resized = await picture.toImage(targetWidth, targetHeight);
    final data = await resized.toByteData(format: ui.ImageByteFormat.png);

    picture.dispose();
    resized.dispose();
    source.dispose();
    codec.dispose();

    if (data == null) {
      throw StateError('Could not re-encode the selected image');
    }
    return data.buffer.asUint8List();
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
    return ValueListenableBuilder<Uint8List?>(
      valueListenable: ProfilePicture.notifier,
      builder: (context, bytes, _) {
        return CircleAvatar(
          radius: radius,
          backgroundColor: colorMainLight,
          backgroundImage: bytes == null ? null : MemoryImage(bytes),
          child: bytes == null
              ? Icon(Icons.person, size: radius, color: colorGrayDark)
              : null,
        );
      },
    );
  }
}
