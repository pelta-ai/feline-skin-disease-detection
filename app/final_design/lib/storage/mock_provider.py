"""
Mock Storage Provider for Testing

This module implements the StorageProvider interface with in-memory storage.
Use this for unit tests to avoid hitting real cloud services.

Usage:
    from storage.mock_provider import MockStorageProvider

    # Create mock with optional pre-populated files
    storage = MockStorageProvider()

    # Or with initial data
    storage = MockStorageProvider(initial_files={
        "user123/2025-12-19/images/cat.jpg": b"fake image data"
    })

    # Use in tests
    assert storage.upload_file("/tmp/test.jpg", "remote/test.jpg")
    assert storage.folder_exists("remote/")
"""

import os
import logging
from typing import Dict, List, Optional
from lib.storage.storage_provider import StorageProvider

logger = logging.getLogger(__name__)


class MockStorageProvider(StorageProvider):
    """In-memory mock implementation of StorageProvider for testing."""

    def __init__(self, initial_files: Optional[Dict[str, bytes]] = None):
        """Initialize mock storage.

        Args:
            initial_files: Optional dict of {path: content} to pre-populate
        """
        self._files: Dict[str, bytes] = initial_files or {}
        self._folders: set = set()

        # Track method calls for assertions in tests
        self.call_log: List[Dict] = []

    def _log_call(self, method: str, **kwargs):
        """Log method calls for test assertions."""
        self.call_log.append({"method": method, **kwargs})

    def list_objects(self, prefix: str = "") -> List[str]:
        """List all object paths under a given prefix."""
        self._log_call("list_objects", prefix=prefix)

        return [
            path for path in self._files.keys()
            if path.startswith(prefix) and not path.endswith('/')
        ]

    def folder_exists(self, path: str) -> bool:
        """Check if a folder exists."""
        self._log_call("folder_exists", path=path)

        if not path.endswith('/'):
            path += '/'

        # Check if folder was explicitly created
        if path in self._folders:
            return True

        # Check if any files exist under this prefix
        return any(f.startswith(path) for f in self._files.keys())

    def create_folder(self, path: str) -> bool:
        """Create a folder."""
        self._log_call("create_folder", path=path)

        if not path.endswith('/'):
            path += '/'

        self._folders.add(path)
        return True

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file (simulated - stores empty bytes if local file doesn't exist)."""
        self._log_call("upload_file", local_path=local_path, remote_path=remote_path)

        try:
            # Try to read actual file if it exists
            if os.path.exists(local_path):
                with open(local_path, 'rb') as f:
                    self._files[remote_path] = f.read()
            else:
                # For testing, store placeholder content
                self._files[remote_path] = b"mock_content"

            return True
        except Exception as e:
            logger.error(f"Mock upload error: {e}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> Optional[str]:
        """Download a file (simulated - writes stored bytes or mock content)."""
        self._log_call("download_file", remote_path=remote_path, local_path=local_path)

        if remote_path not in self._files:
            return None

        try:
            # Ensure directory exists
            local_dir = os.path.dirname(local_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)

            with open(local_path, 'wb') as f:
                f.write(self._files[remote_path])

            return local_path
        except Exception as e:
            logger.error(f"Mock download error: {e}")
            return None

    def get_file_url(self, path: str, expires_in: int = 3600) -> Optional[str]:
        """Generate a mock URL for a file."""
        self._log_call("get_file_url", path=path, expires_in=expires_in)

        if path in self._files:
            return f"https://mock-storage.example.com/{path}?expires={expires_in}"

        return None

    def delete_file(self, path: str) -> bool:
        """Delete a file from mock storage."""
        self._log_call("delete_file", path=path)

        if path in self._files:
            del self._files[path]
            return True

        return False

    # Test helper methods

    def get_stored_files(self) -> Dict[str, bytes]:
        """Get all stored files (for test assertions)."""
        return self._files.copy()

    def get_stored_folders(self) -> set:
        """Get all created folders (for test assertions)."""
        return self._folders.copy()

    def clear(self):
        """Clear all stored data."""
        self._files.clear()
        self._folders.clear()
        self.call_log.clear()

    def assert_uploaded(self, remote_path: str) -> bool:
        """Assert that a file was uploaded to a specific path."""
        return remote_path in self._files

    def assert_method_called(self, method: str, **expected_kwargs) -> bool:
        """Assert that a method was called with specific arguments."""
        for call in self.call_log:
            if call["method"] == method:
                if all(call.get(k) == v for k, v in expected_kwargs.items()):
                    return True
        return False

    # App-specific convenience methods (matching S3Provider)

    def create_user_folder(self, user_id: str) -> bool:
        """Create the base folder for a user."""
        return self.create_folder(user_id)

    def create_today_folders(self, user_id: str) -> bool:
        """Create today's folders for a user."""
        base_path = self.get_user_path(user_id)

        for subfolder in ['images', 'annotated_images', 'diagnosis']:
            self.create_folder(f"{base_path}{subfolder}/")

        return True

    def add_file(self, file_name: str, local_path: str, user_id: str,
                 is_annotated: bool = False) -> bool:
        """Add a file to the appropriate user folder."""
        today = self.get_today_date()
        base_path = f"{user_id}/{today}"

        if file_name.endswith('.txt'):
            subfolder = 'diagnosis'
        elif is_annotated:
            subfolder = 'annotated_images'
        else:
            subfolder = 'images'

        remote_path = f"{base_path}/{subfolder}/{file_name}"
        return self.upload_file(local_path, remote_path)
