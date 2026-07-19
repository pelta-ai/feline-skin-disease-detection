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
///   - CloudStorageProvider: Calls backend API for cloud storage operations
///     (kept for future use; the app is moving toward on-device local storage)
///   - MockStorageProvider: On-device local file storage (mobile/desktop only)
library;

import 'package:flutter/foundation.dart' show kIsWeb;

export 'app_storage_provider.dart';
export 'cloud_storage_provider.dart';
export 'mock_storage_provider.dart';

import 'package:final_design/storage/app_storage_provider.dart';
import 'package:final_design/storage/cloud_storage_provider.dart';
import 'package:final_design/storage/mock_storage_provider.dart';
import 'package:final_design/utils/app_config.dart';

/// Global storage provider instance.
///
/// On web: Always uses CloudStorageProvider (backend handles storage)
/// On mobile/desktop with USE_MOCKS=true: Uses MockStorageProvider (local files)
/// On mobile/desktop without mocks: Uses CloudStorageProvider (backend)
AppStorageProvider _storageProvider = _selectProvider();

AppStorageProvider _selectProvider() {
  // Web can't use local file storage, always call backend
  if (kIsWeb) {
    return CloudStorageProvider();
  }

  // Mobile/desktop can use local mock storage
  if (AppConfig.useMocks) {
    return MockStorageProvider();
  } else {
    return CloudStorageProvider();
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
    case 'cloud':
    case 's3':
    default:
      return CloudStorageProvider();
  }
}
