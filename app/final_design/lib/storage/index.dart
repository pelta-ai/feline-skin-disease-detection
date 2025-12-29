/// Storage Module
///
/// Provides a clean abstraction for storage operations.
/// Automatically selects the appropriate provider based on build flags.
///
/// Usage:
///   import 'package:final_design/storage/index.dart';
///
///   // Use the global storage instance
///   await storage.createUserFolder('user123');
///   await storage.uploadFile(file, 'user123');
///
///   // In mock mode, you can clear all data
///   if (AppConfig.useMocks) {
///     await storage.clearAllData();
///   }
///
/// Build flags:
///   flutter run --dart-define=USE_MOCKS=true  → MockStorageProvider (local files)
///   flutter run                                → S3StorageProvider (real S3)
library;

export 'app_storage_provider.dart';
export 's3_storage_provider.dart';
export 'mock_storage_provider.dart';

import 'package:final_design/storage/app_storage_provider.dart';
import 'package:final_design/storage/s3_storage_provider.dart';
import 'package:final_design/storage/mock_storage_provider.dart';
import 'package:final_design/utils/app_config.dart';

/// Global storage provider instance.
///
/// Automatically selects provider based on build flags:
/// - USE_MOCKS=true → MockStorageProvider (local file storage)
/// - USE_MOCKS=false → S3StorageProvider (real AWS S3)
///
/// For manual override in tests, use [setStorageProvider].
AppStorageProvider _storageProvider = AppConfig.useMocks
    ? MockStorageProvider()
    : S3StorageProvider();

/// Get the current storage provider instance.
AppStorageProvider get storage => _storageProvider;

/// Set the storage provider (useful for testing).
///
/// Example:
///   void main() {
///     setStorageProvider(MockStorageProvider());
///     runApp(MyApp());
///   }
void setStorageProvider(AppStorageProvider provider) {
  _storageProvider = provider;
}

/// Factory function to create a new storage provider.
///
/// Args:
///   providerType: 's3' or 'mock'
///
/// Example:
///   final storage = getStorageProvider('mock');
AppStorageProvider getStorageProvider([String providerType = 's3']) {
  switch (providerType.toLowerCase()) {
    case 'mock':
      return MockStorageProvider();
    case 's3':
    default:
      return S3StorageProvider();
  }
}
