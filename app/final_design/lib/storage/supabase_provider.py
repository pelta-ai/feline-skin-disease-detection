"""
Supabase Storage Provider Implementation

This module implements the StorageProvider interface for Supabase Storage.

Environment Variables:
    SUPABASE_URL: Your Supabase project URL (e.g., https://xxx.supabase.co)
    SUPABASE_SECRET_KEY: Secret key for server-side operations

Usage:
    from storage.supabase_provider import SupabaseStorageProvider

    storage = SupabaseStorageProvider()
    storage.upload_file("/local/image.jpg", "users/abc123/2026-01-24/images/image.jpg")
"""

import os
import logging
from datetime import datetime
from typing import List, Optional

from supabase import create_client, Client

from lib.storage.storage_provider import StorageProvider

logger = logging.getLogger(__name__)


class SupabaseStorageProvider(StorageProvider):
    """Supabase Storage implementation of StorageProvider."""

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
        bucket: str = "pelta-storage"
    ):
        """Initialize Supabase storage provider.

        Args:
            url: Supabase project URL. Defaults to SUPABASE_URL env var.
            key: Service role key. Defaults to SUPABASE_SERVICE_ROLE_KEY env var.
            bucket: Storage bucket name. Defaults to 'pelta-storage'.
        """
        self.url = url or os.environ.get('SUPABASE_URL')
        self.key = key or os.environ.get('SUPABASE_SECRET_KEY')
        self.bucket = bucket

        if not self.url or not self.key:
            raise ValueError(
                "Supabase URL and secret key are required. "
                "Set SUPABASE_URL and SUPABASE_SECRET_KEY environment variables."
            )

        self.client: Client = create_client(self.url, self.key)
        self.storage = self.client.storage

    def _get_date_folder(self) -> str:
        """Get today's date in YYYY-MM-DD format."""
        return datetime.now().strftime('%Y-%m-%d')

    def list_objects(self, prefix: str = "") -> List[str]:
        """List all object paths under a given prefix."""
        try:
            # Supabase list returns objects in a folder
            # We need to handle nested paths by splitting the prefix
            parts = prefix.rstrip('/').split('/') if prefix else []

            response = self.storage.from_(self.bucket).list(path='/'.join(parts) if parts else '')

            paths = []
            for item in response:
                item_path = f"{prefix}/{item['name']}" if prefix else item['name']
                if item.get('metadata'):  # It's a file
                    paths.append(item_path)
                else:  # It's a folder, recurse
                    nested = self.list_objects(item_path)
                    paths.extend(nested)

            return paths
        except Exception as e:
            logger.error(f"Error listing objects with prefix '{prefix}': {e}")
            return []

    def folder_exists(self, path: str) -> bool:
        """Check if a folder/prefix exists in Supabase Storage."""
        try:
            path = path.rstrip('/')
            parts = path.split('/')
            parent = '/'.join(parts[:-1]) if len(parts) > 1 else ''
            folder_name = parts[-1]

            response = self.storage.from_(self.bucket).list(path=parent)

            for item in response:
                if item['name'] == folder_name:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking folder existence '{path}': {e}")
            return False

    def create_folder(self, path: str) -> bool:
        """Create a folder in Supabase Storage.

        Note: Supabase doesn't have explicit folders. Folders are created
        implicitly when uploading files. This method creates a .keep file.
        """
        try:
            path = path.rstrip('/')
            keep_file = f"{path}/.keep"

            # Upload an empty .keep file to create the folder
            self.storage.from_(self.bucket).upload(
                path=keep_file,
                file=b'',
                file_options={"content-type": "text/plain"}
            )
            logger.info(f"Folder '{path}' created successfully")
            return True
        except Exception as e:
            # Folder might already exist
            if "Duplicate" in str(e) or "already exists" in str(e).lower():
                return True
            logger.error(f"Error creating folder '{path}': {e}")
            return False

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file from local filesystem to Supabase Storage."""
        try:
            with open(local_path, 'rb') as f:
                file_data = f.read()

            # Determine content type
            ext = os.path.splitext(local_path)[1].lower()
            content_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.txt': 'text/plain',
                '.json': 'application/json',
                '.pt': 'application/octet-stream',
                '.keras': 'application/octet-stream',
            }
            content_type = content_types.get(ext, 'application/octet-stream')

            self.storage.from_(self.bucket).upload(
                path=remote_path,
                file=file_data,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            logger.info(f"Successfully uploaded '{local_path}' to '{remote_path}'")
            return True
        except Exception as e:
            logger.error(f"Error uploading file to '{remote_path}': {e}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> Optional[str]:
        """Download a file from Supabase Storage to local filesystem."""
        try:
            # Ensure local directory exists
            local_dir = os.path.dirname(local_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)

            response = self.storage.from_(self.bucket).download(remote_path)

            with open(local_path, 'wb') as f:
                f.write(response)

            logger.info(f"Successfully downloaded '{remote_path}' to '{local_path}'")
            return local_path
        except Exception as e:
            logger.error(f"Error downloading file '{remote_path}': {e}")
            return None

    def get_file_url(self, path: str, expires_in: int = 3600) -> Optional[str]:
        """Generate a signed URL for accessing a file in Supabase Storage."""
        try:
            response = self.storage.from_(self.bucket).create_signed_url(
                path=path,
                expires_in=expires_in
            )
            return response.get('signedURL') or response.get('signedUrl')
        except Exception as e:
            logger.error(f"Error generating URL for '{path}': {e}")
            return None

    def delete_file(self, path: str) -> bool:
        """Delete a file from Supabase Storage."""
        try:
            self.storage.from_(self.bucket).remove([path])
            logger.info(f"Successfully deleted '{path}'")
            return True
        except Exception as e:
            logger.error(f"Error deleting file '{path}': {e}")
            return False

    # Convenience methods specific to this app

    def create_user_folder(self, user_id: str) -> bool:
        """Create the base folder for a user."""
        return self.create_folder(f"users/{user_id}")

    def create_today_folders(self, user_id: str) -> bool:
        """Create today's folders for a user (images, annotated_images, diagnosis)."""
        today = self._get_date_folder()
        base_path = f"users/{user_id}/{today}"
        success = True

        for subfolder in ['images', 'annotated_images', 'diagnosis']:
            if not self.create_folder(f"{base_path}/{subfolder}"):
                success = False

        return success

    def add_file(self, file_name: str, local_path: str, user_id: str,
                 is_annotated: bool = False) -> bool:
        """Add a file to the appropriate user folder based on type.

        Args:
            file_name: Name of the file
            local_path: Local path to the file
            user_id: User's unique identifier
            is_annotated: True for annotated images, False for raw images

        Returns:
            True if successful, False otherwise
        """
        today = self._get_date_folder()
        base_path = f"users/{user_id}/{today}"

        # Determine destination based on file type
        if file_name.endswith('.txt'):
            subfolder = 'diagnosis'
        elif is_annotated:
            subfolder = 'annotated_images'
        else:
            subfolder = 'images'

        remote_path = f"{base_path}/{subfolder}/{file_name}"
        return self.upload_file(local_path, remote_path)

    def get_user_path(self, user_id: str) -> str:
        """Get the base path for a user's today folder."""
        today = self._get_date_folder()
        return f"users/{user_id}/{today}/"

    @staticmethod
    def get_today_date() -> str:
        """Get today's date in YYYY-MM-DD format."""
        return datetime.now().strftime('%Y-%m-%d')

    # Training data methods

    def upload_training_image(self, local_path: str, category: str) -> bool:
        """Upload an image to the training dataset.

        Args:
            local_path: Local path to the image
            category: Disease category (acne, flea_allergy, healthy, lumps_and_bumps)
        """
        file_name = os.path.basename(local_path)
        remote_path = f"training/{category}/{file_name}"
        return self.upload_file(local_path, remote_path)

    def upload_testing_image(self, local_path: str, category: str) -> bool:
        """Upload an image to the testing dataset.

        Args:
            local_path: Local path to the image
            category: Disease category (acne, flea_allergy, healthy, lumps_and_bumps)
        """
        file_name = os.path.basename(local_path)
        remote_path = f"testing/{category}/{file_name}"
        return self.upload_file(local_path, remote_path)

    def list_training_images(self, category: Optional[str] = None) -> List[str]:
        """List training images, optionally filtered by category."""
        prefix = f"training/{category}" if category else "training"
        return self.list_objects(prefix)

    def list_testing_images(self, category: Optional[str] = None) -> List[str]:
        """List testing images, optionally filtered by category."""
        prefix = f"testing/{category}" if category else "testing"
        return self.list_objects(prefix)
