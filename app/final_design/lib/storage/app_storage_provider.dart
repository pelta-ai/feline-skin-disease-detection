import 'dart:io';

/// Abstract interface for storage providers.
///
/// Implementations can be created for AWS S3, Azure Blob, local file system, etc.
/// Use MockStorageProvider for unit testing and development.
///
/// Usage:
///   import 'package:final_design/storage/index.dart';
///
///   // Use the global storage instance
///   await storage.createUserFolder('user123');
///   await storage.uploadFile(file, 'user123');
abstract class AppStorageProvider {
  // ============================================
  // Folder Operations
  // ============================================

  /// Create a folder for a new user
  ///
  /// Called during sign-up to initialize user's storage space.
  /// Returns true if successful, false otherwise.
  Future<bool> createUserFolder(String userId);

  /// Check if a folder exists
  Future<bool> folderExists(String path);

  /// Create a folder for today's date under user's folder
  ///
  /// Structure: {userId}/{date}/
  Future<bool> createTodayFolder(String userId);

  // ============================================
  // File Operations
  // ============================================

  /// Upload a file to storage
  ///
  /// Args:
  ///   file: The local file to upload
  ///   userId: The user's ID
  ///   isAnnotated: Whether this is an annotated image
  ///
  /// Returns: The remote path if successful, null otherwise
  Future<String?> uploadFile(File file, String userId, {bool isAnnotated = false});

  /// Upload file bytes to storage (works on web)
  ///
  /// Args:
  ///   bytes: The file content as bytes
  ///   fileName: Name of the file
  ///   userId: The user's ID
  ///   isAnnotated: Whether this is an annotated image
  ///
  /// Returns: The remote path if successful, null otherwise
  Future<String?> uploadFileBytes(List<int> bytes, String fileName, String userId, {bool isAnnotated = false});

  /// Get a URL to access a file
  ///
  /// For the real backend: Returns a pre-signed URL
  /// For mock: Returns a local file path
  Future<String?> getFileUrl(String path);

  /// Download a file from storage
  ///
  /// Returns: Local path to downloaded file, or null if failed
  Future<String?> downloadFile(String remotePath, String localPath);

  /// List files in a folder
  Future<List<String>> listFiles(String prefix);

  // ============================================
  // AI Integration
  // ============================================

  /// Generate AI predictions for an uploaded image
  ///
  /// This calls the backend to run YOLO + CNN on the image.
  /// Returns a map with 'label' and 'annotated_url' on success.
  Future<Map<String, dynamic>?> generateAIPredictions({
    required String userId,
    required String fileName,
    required String storageKey,
  });

  /// Get today's date from the backend (for consistency)
  Future<String?> getTodayDate();

  // ============================================
  // Utility
  // ============================================

  /// Clear all stored data (for testing/dev)
  ///
  /// WARNING: This deletes all data. Use with caution.
  Future<void> clearAllData();
}
