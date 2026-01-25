"""
Storage Provider Interface

This module defines the abstract base class for storage providers.
Implementations can be created for AWS S3, Azure Blob, Google Cloud Storage, etc.

Usage:
    from storage.s3_provider import S3StorageProvider
    storage = S3StorageProvider(bucket="my-bucket")
    storage.upload_file("/local/path.jpg", "remote/path.jpg")
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date


class StorageProvider(ABC):
    """Abstract base class for cloud storage providers.

    All storage implementations (S3, Azure, GCS, Mock) must implement these methods.
    This enables easy switching between providers and unit testing with mocks.
    """

    @abstractmethod
    def list_objects(self, prefix: str = "") -> List[str]:
        """List all object paths under a given prefix.

        Args:
            prefix: The prefix/folder path to list objects from

        Returns:
            List of object paths (excluding folder markers)
        """
        pass

    @abstractmethod
    def folder_exists(self, path: str) -> bool:
        """Check if a folder/prefix exists in storage.

        Args:
            path: The folder path to check

        Returns:
            True if folder exists, False otherwise
        """
        pass

    @abstractmethod
    def create_folder(self, path: str) -> bool:
        """Create a folder/prefix in storage.

        Args:
            path: The folder path to create

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file from local filesystem to storage.

        Args:
            local_path: Path to the local file
            remote_path: Destination path in storage

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> Optional[str]:
        """Download a file from storage to local filesystem.

        Args:
            remote_path: Path to file in storage
            local_path: Destination path on local filesystem

        Returns:
            Local path if successful, None otherwise
        """
        pass

    @abstractmethod
    def get_file_url(self, path: str, expires_in: int = 3600) -> Optional[str]:
        """Generate a temporary URL for accessing a file.

        Args:
            path: Path to the file in storage
            expires_in: URL expiration time in seconds (default 1 hour)

        Returns:
            Temporary URL string, or None if failed
        """
        pass

    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """Delete a file from storage.

        Args:
            path: Path to the file to delete

        Returns:
            True if successful, False otherwise
        """
        pass

    # Utility methods (not abstract - shared implementation)

    @staticmethod
    def get_today_date() -> str:
        """Returns today's date in ISO 8601 format (YYYY-MM-DD).

        Benefits:
        - Lexicographically sortable (chronological order in listings)
        - Consistent 10-character format
        - International standard

        Returns:
            Date string like "2026-01-24"
        """
        return date.today().strftime("%Y-%m-%d")

    def get_user_path(self, user_id: str, subfolder: str = "") -> str:
        """Generate a user-specific path with today's date.

        Args:
            user_id: The user's unique identifier
            subfolder: Optional subfolder (images, annotated_images, diagnosis)

        Returns:
            Path like "user123/2026-01-24/images/"
        """
        today = self.get_today_date()
        if subfolder:
            return f"{user_id}/{today}/{subfolder}/"
        return f"{user_id}/{today}/"
