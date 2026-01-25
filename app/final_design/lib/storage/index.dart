/// Storage Module
///
/// Provides a clean abstraction for storage operations.
///
/// Usage:
///   import 'package:final_design/storage/index.dart';
///
///   await storage.createUserFolder('user123');
///   await storage.uploadFile(file, 'user123');
///   await storage.getFileUrl('user123/2025-01-19/images/photo.jpg');
///
/// Providers:
///   - S3StorageProvider: Calls backend API for storage operations
///   - MockStorageProvider: Local file storage for offline testing (mobile/desktop only)
library;

import 'package:flutter/foundation.dart' show kIsWeb;

export 'app_storage_provider.dart';
export 's3_storage_provider.dart';
export 'mock_storage_provider.dart';

import 'package:final_design/storage/app_storage_provider.dart';
import 'package:final_design/storage/s3_storage_provider.dart';
import 'package:final_design/storage/mock_storage_provider.dart';
import 'package:final_design/utils/app_config.dart';

/// Global storage provider instance.
///
/// On web: Always uses S3StorageProvider (backend handles storage)
/// On mobile/desktop with USE_MOCKS=true: Uses MockStorageProvider (local files)
/// On mobile/desktop without mocks: Uses S3StorageProvider (backend)
AppStorageProvider _storageProvider = _selectProvider();

AppStorageProvider _selectProvider() {
  // Web can't use local file storage, always call backend
  if (kIsWeb) {
    return S3StorageProvider();
  }

  // Mobile/desktop can use local mock storage
  if (AppConfig.useMocks) {
    return MockStorageProvider();
  } else {
    return S3StorageProvider();
  }
}

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

/// Factory function to create a storage provider.
///
/// Args:
///   providerType: 'backend' (default) or 'mock'
AppStorageProvider getStorageProvider([String providerType = 'backend']) {
  switch (providerType.toLowerCase()) {
    case 'mock':
      return MockStorageProvider();
    case 'backend':
    case 's3':
    default:
      return S3StorageProvider();
  }
}
