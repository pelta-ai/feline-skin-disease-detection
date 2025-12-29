"""
Unit Tests for Storage Providers

Run with: pytest tests/test_storage_provider.py -v
"""

import os
import sys
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.storage import MockStorageProvider, get_storage_provider


class TestMockStorageProvider:
    """Tests for the MockStorageProvider class."""

    def test_upload_file_stores_content(self):
        """Test that uploading a file stores it in memory."""
        storage = MockStorageProvider()

        # Create a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            result = storage.upload_file(temp_path, "user123/2025-12-19/images/test.txt")
            assert result is True
            assert storage.assert_uploaded("user123/2025-12-19/images/test.txt")
        finally:
            os.unlink(temp_path)

    def test_upload_file_without_local_file(self):
        """Test that uploading stores mock content when local file doesn't exist."""
        storage = MockStorageProvider()

        result = storage.upload_file("/nonexistent/path.jpg", "remote/path.jpg")
        assert result is True
        assert storage.assert_uploaded("remote/path.jpg")
        assert storage.get_stored_files()["remote/path.jpg"] == b"mock_content"

    def test_folder_exists_false_initially(self):
        """Test that folders don't exist initially."""
        storage = MockStorageProvider()
        assert storage.folder_exists("some/folder") is False

    def test_folder_exists_after_create(self):
        """Test that folders exist after creation."""
        storage = MockStorageProvider()

        storage.create_folder("user123")
        assert storage.folder_exists("user123") is True

    def test_folder_exists_when_files_present(self):
        """Test that folders exist when files are under them."""
        storage = MockStorageProvider(initial_files={
            "user123/2025-12-19/images/cat.jpg": b"image data"
        })

        assert storage.folder_exists("user123") is True
        assert storage.folder_exists("user123/2025-12-19") is True
        assert storage.folder_exists("user123/2025-12-19/images") is True

    def test_list_objects_with_prefix(self):
        """Test listing objects with a prefix filter."""
        storage = MockStorageProvider(initial_files={
            "user123/2025-12-19/images/cat.jpg": b"image1",
            "user123/2025-12-19/images/dog.jpg": b"image2",
            "user123/2025-12-19/diagnosis/report.txt": b"report",
            "user456/2025-12-19/images/bird.jpg": b"image3",
        })

        # List all images for user123
        images = storage.list_objects("user123/2025-12-19/images/")
        assert len(images) == 2
        assert "user123/2025-12-19/images/cat.jpg" in images
        assert "user123/2025-12-19/images/dog.jpg" in images

    def test_download_file_creates_local_file(self):
        """Test that downloading creates a local file."""
        storage = MockStorageProvider(initial_files={
            "remote/test.txt": b"file content"
        })

        with tempfile.TemporaryDirectory() as temp_dir:
            local_path = os.path.join(temp_dir, "downloaded.txt")
            result = storage.download_file("remote/test.txt", local_path)

            assert result == local_path
            assert os.path.exists(local_path)
            with open(local_path, 'rb') as f:
                assert f.read() == b"file content"

    def test_download_nonexistent_file_returns_none(self):
        """Test that downloading a nonexistent file returns None."""
        storage = MockStorageProvider()

        result = storage.download_file("nonexistent.txt", "/tmp/local.txt")
        assert result is None

    def test_get_file_url_returns_mock_url(self):
        """Test that get_file_url returns a mock URL for existing files."""
        storage = MockStorageProvider(initial_files={
            "user123/image.jpg": b"image data"
        })

        url = storage.get_file_url("user123/image.jpg", expires_in=7200)
        assert url is not None
        assert "mock-storage.example.com" in url
        assert "user123/image.jpg" in url
        assert "expires=7200" in url

    def test_get_file_url_nonexistent_returns_none(self):
        """Test that get_file_url returns None for nonexistent files."""
        storage = MockStorageProvider()

        url = storage.get_file_url("nonexistent.jpg")
        assert url is None

    def test_delete_file(self):
        """Test deleting a file."""
        storage = MockStorageProvider(initial_files={
            "to_delete.txt": b"content"
        })

        assert storage.assert_uploaded("to_delete.txt")
        result = storage.delete_file("to_delete.txt")
        assert result is True
        assert not storage.assert_uploaded("to_delete.txt")

    def test_delete_nonexistent_file_returns_false(self):
        """Test that deleting a nonexistent file returns False."""
        storage = MockStorageProvider()

        result = storage.delete_file("nonexistent.txt")
        assert result is False

    def test_call_log_tracks_method_calls(self):
        """Test that method calls are logged for assertions."""
        storage = MockStorageProvider()

        storage.folder_exists("some/path")
        storage.create_folder("new/folder")
        storage.upload_file("/local/file.txt", "remote/file.txt")

        assert storage.assert_method_called("folder_exists", path="some/path")
        assert storage.assert_method_called("create_folder", path="new/folder")
        assert storage.assert_method_called("upload_file", remote_path="remote/file.txt")

    def test_clear_resets_storage(self):
        """Test that clear() removes all stored data."""
        storage = MockStorageProvider(initial_files={"file.txt": b"data"})
        storage.create_folder("folder")

        storage.clear()

        assert len(storage.get_stored_files()) == 0
        assert len(storage.get_stored_folders()) == 0
        assert len(storage.call_log) == 0

    def test_create_user_folder(self):
        """Test the convenience method for creating user folders."""
        storage = MockStorageProvider()

        storage.create_user_folder("user123")
        assert storage.folder_exists("user123")

    def test_create_today_folders(self):
        """Test the convenience method for creating today's folders."""
        storage = MockStorageProvider()

        storage.create_today_folders("user123")

        # Should create images, annotated_images, and diagnosis folders
        today = storage.get_today_date()
        assert storage.folder_exists(f"user123/{today}/images")
        assert storage.folder_exists(f"user123/{today}/annotated_images")
        assert storage.folder_exists(f"user123/{today}/diagnosis")

    def test_add_file_routes_to_correct_subfolder(self):
        """Test that add_file routes files to correct subfolders."""
        storage = MockStorageProvider()
        today = storage.get_today_date()

        # Upload a regular image
        storage.add_file("cat.jpg", "/fake/cat.jpg", "user123", is_annotated=False)
        assert storage.assert_method_called(
            "upload_file",
            remote_path=f"user123/{today}/images/cat.jpg"
        )

        # Upload an annotated image
        storage.add_file("cat_annotated.jpg", "/fake/cat_annotated.jpg", "user123", is_annotated=True)
        assert storage.assert_method_called(
            "upload_file",
            remote_path=f"user123/{today}/annotated_images/cat_annotated.jpg"
        )

        # Upload a diagnosis file
        storage.add_file("diagnosis.txt", "/fake/diagnosis.txt", "user123", is_annotated=False)
        assert storage.assert_method_called(
            "upload_file",
            remote_path=f"user123/{today}/diagnosis/diagnosis.txt"
        )


class TestStorageProviderFactory:
    """Tests for the get_storage_provider factory function."""

    def test_returns_mock_when_specified(self):
        """Test that specifying 'mock' returns MockStorageProvider."""
        storage = get_storage_provider('mock')
        assert isinstance(storage, MockStorageProvider)

    def test_returns_mock_from_env_var(self, monkeypatch):
        """Test that STORAGE_PROVIDER env var works."""
        monkeypatch.setenv('STORAGE_PROVIDER', 'mock')
        storage = get_storage_provider()
        assert isinstance(storage, MockStorageProvider)

    def test_raises_for_unknown_provider(self):
        """Test that unknown provider types raise ValueError."""
        try:
            get_storage_provider('unknown_provider')
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "unknown_provider" in str(e).lower()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
