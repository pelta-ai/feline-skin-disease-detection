"""
Count images per disease category for each split (train/val/test)
using the classes CSV files in new_data/.
"""

import os
import sys
from pathlib import Path

import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.constants as constants
from utils.get_class_names import get_class_names

class_names = get_class_names(os.path.join(constants.DATA_PATH, "train"))

def count_classes_from_csv(csv_path: str) -> dict[str, int]:
    """Count images per category from a classes CSV file."""
    df = pd.read_csv(csv_path)
    return {cat: int(df[cat].sum()) for cat in constants.CLASS_NAMES}

def count_classes_from_folder_structure(directory=constants.DATA_PATH):
    root = Path(directory)
    class_counts = {}

    for split_dir in root.iterdir():
        if not split_dir.is_dir():
            continue
        
        for class_dir in split_dir.iterdir():
            if not class_dir.is_dir():
                continue

            count = sum(1 for f in class_dir.iterdir() if f.is_file() and f.suffix.lower() != ".csv")
            class_counts[class_dir.name] = class_counts.get(class_dir.name, 0) + count

    return class_counts

def count_all():
    """Count and print image classes for all splits."""
    data_path = Path(constants.DATA_PATH)

    for split in ["train", "val", "test"]:
        csv_path = data_path / f"{split}_classes.csv"
        if not csv_path.exists():
            print(f"{split}: CSV not found ({csv_path})")
            continue

        counts = count_classes_from_csv(str(csv_path))
        total = sum(counts.values())
        print(f"\n{split} ({total} total):")
        for cat, count in counts.items():
            print(f"  {cat}: {count}")

print(count_classes_from_folder_structure())