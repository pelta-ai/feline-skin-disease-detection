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

CATEGORIES = ["demodicosis", "dermatitis", "flea_allergy", "fungus", "ringworm", "scabies"]


def count_classes(csv_path: str) -> dict[str, int]:
    """Count images per category from a classes CSV file."""
    df = pd.read_csv(csv_path)
    return {cat: int(df[cat].sum()) for cat in CATEGORIES}


def count_all():
    """Count and print image classes for all splits."""
    data_path = Path(constants.DATA_PATH)

    for split in ["train", "val", "test"]:
        csv_path = data_path / f"{split}_classes.csv"
        if not csv_path.exists():
            print(f"{split}: CSV not found ({csv_path})")
            continue

        counts = count_classes(str(csv_path))
        total = sum(counts.values())
        print(f"\n{split} ({total} total):")
        for cat, count in counts.items():
            print(f"  {cat}: {count}")
