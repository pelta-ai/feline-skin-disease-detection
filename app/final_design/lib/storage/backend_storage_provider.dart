import 'dart:io';
import 'package:final_design/storage/app_storage_provider.dart';
import 'package:final_design/utils/backend_api.dart';

/// Storage provider that delegates operations to the backend API.
///
/// All storage operations (upload, download, list, etc.) are performed
/// via HTTP calls to the backend service. The backend decides the actual
/// storage destination (Supabase by default, or S3) — this provider is
/// agnostic to which one is in use.
class BackendStorageProvider implements AppStorageProvider {
  @override
  Future<bool> createUserFolder(String userId) async {
    try {
      await BackendApiService.createUserFolder(userId);
      return true;
    } catch (e) {
      return false;
    }
  }

  @override
  Future<bool> folderExists(String path) async {
    return await BackendApiService.folderExists(path);
  }

  @override
  Future<bool> createTodayFolder(String userId) async {
    try {
      await BackendApiService.createTodayFolder(userId);
      return true;
    } catch (e) {
      return false;
    }
  }

  @override
  Future<String?> uploadFile(File file, String userId, {bool isAnnotated = false}) async {
    try {
      await BackendApiService.uploadFile(file, userId, isAnnotated);
      // Return the expected path
      final today = await getTodayDate();
      if (today == null) return null;
      final folder = isAnnotated ? 'annotated_images' : 'images';
      return '$userId/$today/$folder/${file.path.split('/').last}';
    } catch (e) {
      return null;
    }
  }

  @override
  Future<String?> uploadFileBytes(List<int> bytes, String fileName, String userId, {bool isAnnotated = false}) async {
    try {
      await BackendApiService.uploadFileBytes(bytes, fileName, userId, isAnnotated);
      // Return the expected path
      final today = await getTodayDate();
      if (today == null) return null;
      final folder = isAnnotated ? 'annotated_images' : 'images';
      return '$userId/$today/$folder/$fileName';
    } catch (e) {
      return null;
    }
  }

  @override
  Future<String?> getFileUrl(String path) async {
    return await BackendApiService.getFileUrl(path);
  }

  @override
  Future<String?> downloadFile(String remotePath, String localPath) async {
    // Note: BackendApiService.triggerDownloadFromStorage has a different
    // signature and is used for a specific workflow. Direct file download is
    // typically done via pre-signed URLs (getFileUrl).
    //
    throw UnimplementedError(
      'Direct download not implemented. Use getFileUrl() for pre-signed URLs.',
    );
  }

  @override
  Future<List<String>> listFiles(String prefix) async {
    return await BackendApiService.listObjectPaths(prefix: prefix);
  }

  @override
  Future<Map<String, dynamic>?> generateAIPredictions({
    required String userId,
    required String fileName,
    required String storageKey,
  }) async {
    return await BackendApiService.generateAIPredictions(
      userId: userId,
      fileName: fileName,
      storageKey: storageKey,
    );
  }

  @override
  Future<String?> getTodayDate() async {
    return await BackendApiService.getTodayDateFromBackend();
  }

  @override
  Future<void> clearAllData() async {
    // Not implemented for the real backend.
    // This would be dangerous - only allow in mock
    throw UnimplementedError(
      'clearAllData() is not available for BackendStorageProvider. '
      'Manage stored data via the storage provider console or CLI.',
    );
  }
}
