import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:final_design/storage/app_storage_provider.dart';
import 'package:intl/intl.dart';

/// Mock implementation of AppStorageProvider for testing and development.
///
/// Stores files locally on the device instead of S3.
/// Data persists across app restarts (stored in app's documents directory).
///
/// CLEARING MOCK DATA:
///
/// Option 1: In code (dev mode only)
///   await storage.clearAllData();
///
/// Option 2: Manually delete folder
///   Android: /data/data/com.example.final_design/app_flutter/mock_storage/
///   iOS: {app_sandbox}/Documents/mock_storage/
///
/// Option 3: Uninstall and reinstall the app
///
/// Option 4: Add a "Clear Data" button in Settings (dev mode)
///   ```dart
///   if (AppConfig.useMocks) {
///     ElevatedButton(
///       onPressed: () => storage.clearAllData(),
///       child: Text('Clear Mock Data'),
///     )
///   }
///   ```
class MockStorageProvider implements AppStorageProvider {
  static const String _mockStorageFolder = 'mock_storage';

  Directory? _baseDir;

  /// Get the base directory for mock storage
  Future<Directory> _getBaseDir() async {
    if (_baseDir != null) return _baseDir!;

    final appDir = await getApplicationDocumentsDirectory();
    _baseDir = Directory('${appDir.path}/$_mockStorageFolder');

    if (!await _baseDir!.exists()) {
      await _baseDir!.create(recursive: true);
    }

    return _baseDir!;
  }

  @override
  Future<bool> createUserFolder(String userId) async {
    try {
      final baseDir = await _getBaseDir();
      final userDir = Directory('${baseDir.path}/$userId');
      await userDir.create(recursive: true);
      return true;
    } catch (e) {
      return false;
    }
  }

  @override
  Future<bool> folderExists(String path) async {
    try {
      final baseDir = await _getBaseDir();
      final dir = Directory('${baseDir.path}/$path');
      return await dir.exists();
    } catch (e) {
      return false;
    }
  }

  @override
  Future<bool> createTodayFolder(String userId) async {
    try {
      final baseDir = await _getBaseDir();
      final today = _getTodayDate();
      final todayDir = Directory('${baseDir.path}/$userId/$today');
      await todayDir.create(recursive: true);

      // Also create subdirectories
      await Directory('${todayDir.path}/images').create(recursive: true);
      await Directory('${todayDir.path}/annotated_images').create(recursive: true);

      return true;
    } catch (e) {
      return false;
    }
  }

  @override
  Future<String?> uploadFile(File file, String userId, {bool isAnnotated = false}) async {
    try {
      final baseDir = await _getBaseDir();
      final today = _getTodayDate();
      final folder = isAnnotated ? 'annotated_images' : 'images';
      final fileName = file.path.split(Platform.pathSeparator).last;

      // Ensure directory exists
      final targetDir = Directory('${baseDir.path}/$userId/$today/$folder');
      await targetDir.create(recursive: true);

      // Copy file to mock storage
      final targetPath = '${targetDir.path}/$fileName';
      await file.copy(targetPath);

      return '$userId/$today/$folder/$fileName';
    } catch (e) {
      return null;
    }
  }

  @override
  Future<String?> getFileUrl(String path) async {
    try {
      final baseDir = await _getBaseDir();
      final file = File('${baseDir.path}/$path');

      if (await file.exists()) {
        return file.path; // Return local path as "URL"
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  @override
  Future<String?> downloadFile(String remotePath, String localPath) async {
    try {
      final baseDir = await _getBaseDir();
      final sourceFile = File('${baseDir.path}/$remotePath');

      if (await sourceFile.exists()) {
        await sourceFile.copy(localPath);
        return localPath;
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  @override
  Future<List<String>> listFiles(String prefix) async {
    try {
      final baseDir = await _getBaseDir();
      final dir = Directory('${baseDir.path}/$prefix');

      if (!await dir.exists()) {
        return [];
      }

      final files = await dir.list(recursive: true).toList();
      return files
          .whereType<File>()
          .map((f) => f.path.replaceFirst('${baseDir.path}/', ''))
          .toList();
    } catch (e) {
      return [];
    }
  }

  @override
  Future<Map<String, dynamic>?> generateAIPredictions({
    required String userId,
    required String fileName,
    required String s3Key,
  }) async {
    // In mock mode, return fake predictions
    // This simulates the AI backend without actually running models
    await Future.delayed(const Duration(milliseconds: 500)); // Simulate processing

    // Return mock prediction
    final mockLabels = ['Healthy', 'Feline Acne', 'Flea Allergy', 'Lumps/Bumps'];
    final randomLabel = mockLabels[DateTime.now().millisecond % mockLabels.length];

    // Get the uploaded image path as the "annotated" URL
    final baseDir = await _getBaseDir();
    final imagePath = '${baseDir.path}/$s3Key';

    return {
      'label': randomLabel,
      'annotated_url': imagePath, // In mock, just return original image path
      'confidence': 0.85 + (DateTime.now().millisecond % 15) / 100,
      'mock': true, // Flag to indicate this is mock data
    };
  }

  @override
  Future<String?> getTodayDate() async {
    return _getTodayDate();
  }

  /// Helper to get today's date in ISO format
  String _getTodayDate() {
    return DateFormat('yyyy-MM-dd').format(DateTime.now());
  }

  @override
  Future<void> clearAllData() async {
    try {
      final baseDir = await _getBaseDir();
      if (await baseDir.exists()) {
        await baseDir.delete(recursive: true);
      }
      _baseDir = null; // Reset cached directory
    } catch (e) {
      // Ignore errors during cleanup
    }
  }

  /// Get storage info for debugging
  Future<Map<String, dynamic>> getStorageInfo() async {
    final baseDir = await _getBaseDir();
    final exists = await baseDir.exists();

    int fileCount = 0;
    int totalSize = 0;

    if (exists) {
      final files = await baseDir.list(recursive: true).toList();
      for (final entity in files) {
        if (entity is File) {
          fileCount++;
          totalSize += await entity.length();
        }
      }
    }

    return {
      'path': baseDir.path,
      'exists': exists,
      'fileCount': fileCount,
      'totalSizeBytes': totalSize,
      'totalSizeMB': (totalSize / (1024 * 1024)).toStringAsFixed(2),
    };
  }
}
