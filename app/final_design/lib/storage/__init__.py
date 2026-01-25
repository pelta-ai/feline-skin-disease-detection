"""
Storage Provider Module

This module provides a clean abstraction for cloud storage operations.
Use the factory function to get the appropriate provider based on environment.

Usage:
    from lib.storage import get_storage_provider, StorageProvider

    # Get the configured storage provider (defaults to Supabase)
    storage = get_storage_provider()

    # Use it
    storage.upload_file("/local/image.jpg", "users/uid/2026-01-24/images/image.jpg")

    # For testing
    from lib.storage import MockStorageProvider
    mock_storage = MockStorageProvider()

Environment Variables:
    STORAGE_PROVIDER: 'supabase' (default), 's3', or 'mock'
"""

import os
from typing import Optional

from lib.storage.storage_provider import StorageProvider
from lib.storage.s3_provider import S3StorageProvider
from lib.storage.mock_provider import MockStorageProvider

# Lazy imports - only load when needed
# This allows running with mock without installing cloud SDKs
SupabaseStorageProvider = None

def _get_supabase_provider():
    global SupabaseStorageProvider
    if SupabaseStorageProvider is None:
        from lib.storage.supabase_provider import SupabaseStorageProvider as _SupabaseStorageProvider
        SupabaseStorageProvider = _SupabaseStorageProvider
    return SupabaseStorageProvider

__all__ = [
    'StorageProvider',
    'S3StorageProvider',
    'MockStorageProvider',
    'get_storage_provider',
]


def get_storage_provider(
    provider_type: Optional[str] = None,
    **kwargs
) -> StorageProvider:
    """Factory function to get the appropriate storage provider.

    Args:
        provider_type: 'supabase', 's3', 'mock', or None (uses STORAGE_PROVIDER env var)
        **kwargs: Additional arguments passed to the provider constructor

    Returns:
        Configured StorageProvider instance

    Environment Variables:
        STORAGE_PROVIDER: 'supabase' (default), 's3', or 'mock'

    Examples:
        # Production (uses Supabase by default)
        storage = get_storage_provider()

        # Explicit Supabase
        storage = get_storage_provider('supabase', bucket='pelta-storage')

        # Legacy S3
        storage = get_storage_provider('s3', bucket='my-bucket')

        # Testing
        storage = get_storage_provider('mock')
    """
    if provider_type is None:
        provider_type = os.environ.get('STORAGE_PROVIDER', 'supabase').lower()

    if provider_type == 'mock':
        return MockStorageProvider(**kwargs)
    elif provider_type == 's3':
        return S3StorageProvider(**kwargs)
    elif provider_type == 'supabase':
        SupabaseProvider = _get_supabase_provider()
        return SupabaseProvider(**kwargs)
    else:
        raise ValueError(f"Unknown storage provider type: {provider_type}")
