import 'dart:io';
import 'package:final_design/storage/app_storage_provider.dart';
import 'package:final_design/utils/aws_s3_api.dart';

/// Storage provider that delegates operations to a backend API.
///
/// All storage operations (upload, download, list, etc.) are performed
/// via HTTP calls to the backend service.
class S3StorageProvider implements AppStorageProvider {
  @override
  Future<bool> createUserFolder(String userId) async {
    try {
      await S3ApiService.createUserFolder(userId);
      return true;
    } catch (e) {
      return false;
    }
  }

  @override
  Future<bool> folderExists(String path) async {
    return await S3ApiService.folderExists(path);
  }

  @override
  Future<bool> createTodayFolder(String userId) async {
    try {
      await S3ApiService.createTodayFolder(userId);
      return true;
    } catch (e) {
      return false;
    }
  }

  @override
  Future<String?> uploadFile(File file, String userId, {bool isAnnotated = false}) async {
    try {
      await S3ApiService.uploadFile(file, userId, isAnnotated);
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
      await S3ApiService.uploadFileBytes(bytes, fileName, userId, isAnnotated);
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
    return await S3ApiService.getFileUrl(path);
  }

  @override
  Future<String?> downloadFile(String remotePath, String localPath) async {
    // Note: S3ApiService.triggerDownloadFromS3 has a different signature
    // and is used for a specific workflow. Direct file download from S3
    // is typically done via pre-signed URLs (getFileUrl).
    //
    throw UnimplementedError(
      'Direct download not implemented. Use getFileUrl() for pre-signed URLs.',
    );
  }

  @override
  Future<List<String>> listFiles(String prefix) async {
    return await S3ApiService.listObjectPaths(prefix: prefix);
  }

  @override
  Future<Map<String, dynamic>?> generateAIPredictions({
    required String userId,
    required String fileName,
    required String s3Key,
  }) async {
    return await S3ApiService.generateAIPredictions(
      userId: userId,
      fileName: fileName,
      s3Key: s3Key,
    );
  }

  @override
  Future<String?> getTodayDate() async {
    return await S3ApiService.getTodayDateFromBackend();
  }

  @override
  Future<void> clearAllData() async {
    // Not implemented for production S3
    // This would be dangerous - only allow in mock
    throw UnimplementedError(
      'clearAllData() is not available for S3StorageProvider. '
      'Use AWS console or CLI to manage S3 data.',
    );
  }
}
