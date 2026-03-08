"""
Sort images into disease-category subfolders based on a classes CSV file.

The CSV is expected to sit alongside the image directory, e.g.:
    new_data/test_classes.csv  ->  images in new_data/test/

Usage:
    python src/data_manipulation/sort_images_from_csv.py new_data/test_classes.csv
    python src/data_manipulation/sort_images_from_csv.py new_data/train_classes.csv
"""

import shutil
import sys, os
from pathlib import Path

import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.constants as constants

CATEGORIES = ["demodicosis", "dermatitis", "flea_allergy", "fungus", "ringworm", "scabies"]


def sort_images(csv_path: str):
    csv_path = Path(csv_path)
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        sys.exit(1)

    # Derive the image directory from the CSV name (e.g. test_classes.csv -> test/)
    split_name = csv_path.stem.replace("_classes", "")
    image_dir = csv_path.parent / split_name

    if not image_dir.exists():
        print(f"Image directory not found: {image_dir}")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    moved = 0
    skipped = 0

    for _, row in df.iterrows():
        filename = row["filename"]
        image_path = image_dir / filename

        if not image_path.exists():
            print(f"  MISSING: {filename}")
            skipped += 1
            continue

        cats = [cat for cat in CATEGORIES if row[cat] == 1]
        if not cats:
            print(f"  NO CATEGORY: {filename}")
            skipped += 1
            continue

        # Move to primary category, copy to additional categories
        primary_dir = image_dir / cats[0]
        primary_dir.mkdir(exist_ok=True)
        shutil.move(str(image_path), str(primary_dir / filename))
        moved += 1

        for extra in cats[1:]:
            extra_dir = image_dir / extra
            extra_dir.mkdir(exist_ok=True)
            shutil.copy2(str(primary_dir / filename), str(extra_dir / filename))
            moved += 1

    print(f"Done. {moved} sorted, {skipped} skipped.")


if __name__ == "__main__":
    sort_images(os.path.join(constants.DATA_PATH, "val_classes.csv"))
