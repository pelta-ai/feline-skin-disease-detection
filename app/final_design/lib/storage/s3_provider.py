"""
AWS S3 Storage Provider Implementation

This module implements the StorageProvider interface for AWS S3.

Environment Variables:
    AWS_ACCESS_KEY_ID: Your AWS access key
    AWS_SECRET_ACCESS_KEY: Your AWS secret key
    AWS_DEFAULT_REGION: AWS region (default: us-east-1)
    S3_BUCKET_NAME: S3 bucket name (optional, can be passed to constructor)

Usage:
    from storage.s3_provider import S3StorageProvider

    # Using environment variable for bucket
    storage = S3StorageProvider()

    # Or specify bucket explicitly
    storage = S3StorageProvider(bucket="my-bucket")

    # Upload a file
    storage.upload_file("/local/image.jpg", "user123/2025-12-19/images/image.jpg")
"""

import os
import logging
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError

from lib.storage.storage_provider import StorageProvider

logger = logging.getLogger(__name__)


class S3StorageProvider(StorageProvider):
    """AWS S3 implementation of StorageProvider."""

    def __init__(self, bucket: Optional[str] = None, region: Optional[str] = None):
        """Initialize S3 storage provider.

        Args:
            bucket: S3 bucket name. Defaults to S3_BUCKET_NAME env var or
                    'felineskindiseasedetectionbucket'
            region: AWS region. Defaults to AWS_DEFAULT_REGION env var or 'us-east-1'
        """
        self.bucket = bucket or os.environ.get(
            'S3_BUCKET_NAME', 'felineskindiseasedetectionbucket'
        )
        self.region = region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        self.client = boto3.client('s3', region_name=self.region)

    def list_objects(self, prefix: str = "") -> List[str]:
        """List all object paths under a given prefix."""
        try:
            paginator = self.client.get_paginator('list_objects_v2')
            paths = []

            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    if not key.endswith('/'):  # Skip folder markers
                        paths.append(key)

            return paths
        except ClientError as e:
            logger.error(f"Error listing objects with prefix '{prefix}': {e}")
            return []

    def folder_exists(self, path: str) -> bool:
        """Check if a folder/prefix exists in S3."""
        if not path.endswith('/'):
            path += '/'

        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket, Prefix=path, MaxKeys=1
            )
            return 'Contents' in response
        except ClientError as e:
            logger.error(f"Error checking folder existence '{path}': {e}")
            return False

    def create_folder(self, path: str) -> bool:
        """Create a folder in S3 (creates an empty object with trailing slash)."""
        if not path.endswith('/'):
            path += '/'

        try:
            self.client.put_object(Bucket=self.bucket, Key=path)
            logger.info(f"Folder '{path}' created successfully")
            return True
        except ClientError as e:
            logger.error(f"Error creating folder '{path}': {e}")
            return False

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file from local filesystem to S3."""
        try:
            self.client.upload_file(
                Filename=local_path,
                Bucket=self.bucket,
                Key=remote_path
            )
            logger.info(f"Successfully uploaded '{local_path}' to '{remote_path}'")
            return True
        except ClientError as e:
            logger.error(f"Error uploading file to '{remote_path}': {e}")
            return False
        except FileNotFoundError:
            logger.error(f"Local file not found: '{local_path}'")
            return False

    def download_file(self, remote_path: str, local_path: str) -> Optional[str]:
        """Download a file from S3 to local filesystem."""
        # Ensure local directory exists
        local_dir = os.path.dirname(local_path)
        if local_dir:
            os.makedirs(local_dir, exist_ok=True)

        try:
            self.client.download_file(self.bucket, remote_path, local_path)
            logger.info(f"Successfully downloaded '{remote_path}' to '{local_path}'")
            return local_path
        except ClientError as e:
            logger.error(f"Error downloading file '{remote_path}': {e}")
            return None

    def get_file_url(self, path: str, expires_in: int = 3600) -> Optional[str]:
        """Generate a presigned URL for accessing a file in S3."""
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': path},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating URL for '{path}': {e}")
            return None

    def delete_file(self, path: str) -> bool:
        """Delete a file from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=path)
            logger.info(f"Successfully deleted '{path}'")
            return True
        except ClientError as e:
            logger.error(f"Error deleting file '{path}': {e}")
            return False

    # Convenience methods specific to this app

    def create_user_folder(self, user_id: str) -> bool:
        """Create the base folder for a user."""
        return self.create_folder(user_id)

    def create_today_folders(self, user_id: str) -> bool:
        """Create today's folders for a user (images, annotated_images, diagnosis)."""
        base_path = self.get_user_path(user_id)
        success = True

        for subfolder in ['images', 'annotated_images', 'diagnosis']:
            if not self.create_folder(f"{base_path}{subfolder}/"):
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
        today = self.get_today_date()
        base_path = f"{user_id}/{today}"

        # Ensure folders exist
        if not self.folder_exists(base_path):
            self.create_today_folders(user_id)

        # Determine destination based on file type
        if file_name.endswith('.txt'):
            subfolder = 'diagnosis'
        elif is_annotated:
            subfolder = 'annotated_images'
        else:
            subfolder = 'images'

        remote_path = f"{base_path}/{subfolder}/{file_name}"
        return self.upload_file(local_path, remote_path)
