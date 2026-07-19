import 'dart:io';
import 'package:final_design/storage/app_storage_provider.dart';
import 'package:final_design/utils/backend_api.dart';

/// Cloud storage provider — delegates operations to the backend API over HTTP.
///
/// This is the frontend client for CLOUD storage. It does not talk to S3 (or
/// Supabase) directly; it makes HTTP calls to the Flask backend, which chooses
/// the actual cloud provider (Supabase by default, S3 legacy) via its
/// STORAGE_PROVIDER env var.
///
/// Note: the underlying `BackendApiService` is likewise a generic backend
/// client — it is not S3-specific.
class CloudStorageProvider implements AppStorageProvider {
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
    // Note: BackendApiService.triggerDownloadFromS3 has a different signature
    // and is used for a specific workflow. Direct file download from S3
    // is typically done via pre-signed URLs (getFileUrl).
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
    required List<int> imageBytes,
  }) async {
    return await BackendApiService.generateAIPredictions(
      userId: userId,
      fileName: fileName,
      imageBytes: imageBytes,
    );
  }

  @override
  Future<String?> getTodayDate() async {
    return await BackendApiService.getTodayDateFromBackend();
  }

  @override
  Future<void> clearAllData() async {
    // Not implemented for production S3
    // This would be dangerous - only allow in mock
    throw UnimplementedError(
      'clearAllData() is not available for CloudStorageProvider. '
      'Use AWS console or CLI to manage S3 data.',
    );
  }
}
