#!/usr/bin/env python3
"""
Generate NPZ files from images stored in Supabase.

This script downloads training/testing images from Supabase and creates
preprocessed numpy arrays for ML training.

Usage:
    # Generate split by category (smaller files, <50MB each)
    python scripts/generate_npz_from_supabase.py --split

    # Generate single combined file
    python scripts/generate_npz_from_supabase.py --combined

    # Dry run (just show what would be downloaded)
    python scripts/generate_npz_from_supabase.py --dry-run

Environment Variables:
    SUPABASE_URL: Your Supabase project URL
    SUPABASE_SECRET_KEY: Your Supabase secret key
"""

import os
import sys
import time
import argparse
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

# Add app directory to path
APP_DIR = Path(__file__).resolve().parents[1] / "app" / "final_design"
sys.path.insert(0, str(APP_DIR))

from dotenv import load_dotenv
load_dotenv(APP_DIR / ".env")

from lib.storage.supabase_provider import SupabaseStorageProvider

# Constants
CATEGORIES = ["acne", "flea_allergy", "healthy", "lumps_and_bumps"]
IMAGE_SIZE = (224, 224)  # Standard size for CNN models
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "sample_model_data" / "preprocessed"


def download_and_process_images(storage, prefix: str, temp_dir: str) -> dict:
    """Download images from Supabase and convert to numpy arrays."""
    results = {cat: [] for cat in CATEGORIES}

    # List all images under prefix
    all_files = storage.list_objects(prefix)
    image_files = [f for f in all_files if f.endswith(('.jpg', '.jpeg', '.png'))]

    print(f"  Found {len(image_files)} images under {prefix}/")

    for remote_path in image_files:
        # Extract category from path like "training/acne/acne_1.jpg"
        parts = remote_path.split('/')
        if len(parts) >= 2:
            category = parts[1]  # training/CATEGORY/filename
        else:
            continue

        if category not in CATEGORIES:
            continue

        # Download to temp file
        filename = os.path.basename(remote_path)
        local_path = os.path.join(temp_dir, filename)

        result = storage.download_file(remote_path, local_path)
        if result:
            try:
                # Load and preprocess image
                img = Image.open(local_path).convert('RGB')
                img = img.resize(IMAGE_SIZE)
                arr = np.array(img, dtype=np.float32) / 255.0  # Normalize to 0-1
                results[category].append(arr)
            except Exception as e:
                print(f"    Error processing {filename}: {e}")
            finally:
                # Clean up temp file
                if os.path.exists(local_path):
                    os.remove(local_path)

    return results


def save_split_npz(train_data: dict, test_data: dict):
    """Save separate npz files for each category."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for category in CATEGORIES:
        train_arr = np.array(train_data[category]) if train_data[category] else np.array([])
        test_arr = np.array(test_data[category]) if test_data[category] else np.array([])

        output_file = OUTPUT_DIR / f"{category}.npz"
        np.savez_compressed(
            output_file,
            train_images=train_arr,
            test_images=test_arr,
            category=category
        )

        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"  Saved {output_file.name}: {len(train_arr)} train, {len(test_arr)} test ({size_mb:.1f} MB)")


def save_combined_npz(train_data: dict, test_data: dict):
    """Save single combined npz file with all categories."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Combine all training images
    all_train_images = []
    all_train_labels = []
    for i, category in enumerate(CATEGORIES):
        for img in train_data[category]:
            all_train_images.append(img)
            all_train_labels.append(i)

    # Combine all testing images
    all_test_images = []
    all_test_labels = []
    for i, category in enumerate(CATEGORIES):
        for img in test_data[category]:
            all_test_images.append(img)
            all_test_labels.append(i)

    output_file = OUTPUT_DIR / "combined.npz"
    np.savez_compressed(
        output_file,
        train_images=np.array(all_train_images),
        train_labels=np.array(all_train_labels),
        test_images=np.array(all_test_images),
        test_labels=np.array(all_test_labels),
        categories=CATEGORIES
    )

    size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"  Saved {output_file.name}: {len(all_train_images)} train, {len(all_test_images)} test ({size_mb:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Generate NPZ from Supabase images")
    parser.add_argument("--split", action="store_true", help="Save separate files per category")
    parser.add_argument("--combined", action="store_true", help="Save single combined file")
    parser.add_argument("--dry-run", action="store_true", help="Just show what would be downloaded")
    args = parser.parse_args()

    if not args.split and not args.combined and not args.dry_run:
        args.split = True  # Default to split mode

    print("=" * 60)
    print("Generate NPZ from Supabase Storage")
    print("=" * 60)

    # Check environment
    if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_SECRET_KEY"):
        print("\nError: SUPABASE_URL and SUPABASE_SECRET_KEY must be set.")
        sys.exit(1)

    # Initialize storage
    print("\nConnecting to Supabase...")
    storage = SupabaseStorageProvider()

    if args.dry_run:
        print("\n--- Dry Run: Listing files ---")
        for prefix in ["training", "testing"]:
            files = storage.list_objects(prefix)
            print(f"\n{prefix}/: {len(files)} files")
            for f in files[:5]:
                print(f"  {f}")
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more")
        return

    start_time = time.time()

    # Download and process images
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n--- Downloading Training Images ---")
        train_data = download_and_process_images(storage, "training", temp_dir)

        print(f"\n--- Downloading Testing Images ---")
        test_data = download_and_process_images(storage, "testing", temp_dir)

    download_time = time.time() - start_time
    print(f"\nDownload + processing time: {download_time:.1f} seconds")

    # Save npz files
    save_start = time.time()
    print(f"\n--- Saving NPZ Files ---")

    if args.split:
        save_split_npz(train_data, test_data)

    if args.combined:
        save_combined_npz(train_data, test_data)

    save_time = time.time() - save_start
    total_time = time.time() - start_time

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    train_count = sum(len(v) for v in train_data.values())
    test_count = sum(len(v) for v in test_data.values())
    print(f"  Training images: {train_count}")
    print(f"  Testing images:  {test_count}")
    print(f"  Download time:   {download_time:.1f}s")
    print(f"  Save time:       {save_time:.1f}s")
    print(f"  Total time:      {total_time:.1f}s")
    print(f"\n  Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
