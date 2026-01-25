#!/usr/bin/env python3
"""
Upload training and validation data to Supabase Storage.

This script uploads images from sample_model_data/images/ to Supabase Storage
with the following structure:
    training/{category}/{filename}
    testing/{category}/{filename}

Usage:
    python scripts/upload_training_data.py

Environment Variables:
    SUPABASE_URL: Your Supabase project URL
    SUPABASE_SECRET_KEY: Your Supabase secret key
"""

import os
import sys
from pathlib import Path

# Add app directory to path
APP_DIR = Path(__file__).resolve().parents[1] / "app" / "final_design"
sys.path.insert(0, str(APP_DIR))

from dotenv import load_dotenv

# Load .env from app/final_design/
load_dotenv(APP_DIR / ".env")

from lib.storage.supabase_provider import SupabaseStorageProvider


def get_category_from_filename(filename: str) -> str:
    """Extract category from filename like 'acne_1.jpg' -> 'acne'."""
    name = filename.lower()
    if name.startswith("acne"):
        return "acne"
    elif name.startswith("flea_allergy"):
        return "flea_allergy"
    elif name.startswith("healthy"):
        return "healthy"
    elif name.startswith("lumps_and_bumps") or name.startswith("lumps"):
        return "lumps_and_bumps"
    else:
        return "unknown"


def upload_directory(storage: SupabaseStorageProvider, local_dir: Path, remote_prefix: str):
    """Upload all images from a local directory to Supabase."""
    if not local_dir.exists():
        print(f"Directory not found: {local_dir}")
        return 0

    uploaded = 0
    failed = 0

    for image_path in list(local_dir.glob("*.jpg")) + list(local_dir.glob("*.jpeg")):
        category = get_category_from_filename(image_path.name)
        remote_path = f"{remote_prefix}/{category}/{image_path.name}"

        print(f"  Uploading: {image_path.name} -> {remote_path}")

        if storage.upload_file(str(image_path), remote_path):
            uploaded += 1
        else:
            failed += 1
            print(f"    FAILED: {image_path.name}")

    return uploaded, failed


def main():
    print("=" * 60)
    print("Uploading Training Data to Supabase Storage")
    print("=" * 60)

    # Check environment
    if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_SECRET_KEY"):
        print("\nError: SUPABASE_URL and SUPABASE_SECRET_KEY must be set.")
        print("Make sure app/final_design/.env has these variables.")
        sys.exit(1)

    # Initialize storage
    print("\nConnecting to Supabase...")
    storage = SupabaseStorageProvider()
    print(f"  Bucket: {storage.bucket}")

    # Paths
    project_root = Path(__file__).resolve().parents[1]
    train_dir = project_root / "sample_model_data" / "images" / "train"
    val_dir = project_root / "sample_model_data" / "images" / "val"

    # Upload training data
    print(f"\n--- Uploading Training Data ({train_dir}) ---")
    train_uploaded, train_failed = upload_directory(storage, train_dir, "training")
    print(f"  Training: {train_uploaded} uploaded, {train_failed} failed")

    # Upload validation/testing data
    print(f"\n--- Uploading Testing Data ({val_dir}) ---")
    test_uploaded, test_failed = upload_directory(storage, val_dir, "testing")
    print(f"  Testing: {test_uploaded} uploaded, {test_failed} failed")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Training images: {train_uploaded} uploaded, {train_failed} failed")
    print(f"  Testing images:  {test_uploaded} uploaded, {test_failed} failed")
    print(f"  Total:           {train_uploaded + test_uploaded} uploaded")

    if train_failed + test_failed > 0:
        print(f"\n  WARNING: {train_failed + test_failed} uploads failed!")
        sys.exit(1)
    else:
        print("\n  All uploads successful!")


if __name__ == "__main__":
    main()
