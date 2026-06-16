"""
Organize a flat class-folder dataset into train/val/test splits (80/10/10).

Expects the source layout (see constants.DATA_PATH):
    final_data/
        <class_a>/  *.jpg
        <class_b>/  *.jpg
        ...

and reorganizes it in place into:
    final_data/
        train/<class>/  val/<class>/  test/<class>/

Files are MOVED (not copied). Augmented variants of the same source photo
(Roboflow exports share a "<base>.rf.<hash>" name) are grouped so every
variant of one photo lands in the same split, preventing train/test leakage.

Usage:
    python src/data_manipulation/split_dataset.py
"""

import os
import random
import shutil
import sys
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.constants as constants

SPLITS = ("train", "val", "test")
SPLIT_RATIOS = (0.8, 0.1, 0.1)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def base_image_key(filename: str) -> str:
    """Group augmented variants of one source photo together.

    Roboflow names look like "<base>.rf.<hash>.<ext>"; everything before
    ".rf." identifies the original photo. Files without ".rf." are treated
    as their own group (the whole stem is the key).
    """
    if ".rf." in filename:
        return filename.split(".rf.")[0]
    return Path(filename).stem


def split_class(class_dir: Path, rng: random.Random) -> dict[str, int]:
    """Move one class folder's images into train/val/test subfolders.

    Returns the file count moved into each split.
    """
    images = [
        f for f in class_dir.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS
    ]

    # Group files by source photo so variants never split across sets.
    groups: dict[str, list[Path]] = {}
    for f in images:
        groups.setdefault(base_image_key(f.name), []).append(f)

    # Shuffle group keys deterministically, then slice 80/10/10 by photo.
    keys = sorted(groups)
    rng.shuffle(keys)

    n = len(keys)
    n_train = int(n * SPLIT_RATIOS[0])
    n_val = int(n * SPLIT_RATIOS[1])
    split_keys = {
        "train": keys[:n_train],
        "val": keys[n_train:n_train + n_val],
        "test": keys[n_train + n_val:],
    }

    moved = {split: 0 for split in SPLITS}
    data_root = class_dir.parent
    for split, group_keys in split_keys.items():
        dest_dir = data_root / split / class_dir.name
        dest_dir.mkdir(parents=True, exist_ok=True)
        for key in group_keys:
            for f in groups[key]:
                shutil.move(str(f), str(dest_dir / f.name))
                moved[split] += 1

    return moved


def split_dataset(directory: str = constants.DATA_PATH, seed: int = constants.SEED):
    """Split every class folder under `directory` into train/val/test."""
    root = Path(directory)
    if not root.is_dir():
        print(f"Data directory not found: {root}")
        sys.exit(1)

    # Refuse to run if splits already exist, to avoid clobbering a split set.
    existing = [s for s in SPLITS if (root / s).exists()]
    if existing:
        print(f"Split folders already exist ({', '.join(existing)}). Aborting.")
        sys.exit(1)

    class_dirs = [d for d in sorted(root.iterdir()) if d.is_dir()]
    if not class_dirs:
        print(f"No class folders found in {root}.")
        sys.exit(1)

    rng = random.Random(seed)
    print(f"Splitting {len(class_dirs)} classes into "
          f"{int(SPLIT_RATIOS[0]*100)}/{int(SPLIT_RATIOS[1]*100)}/{int(SPLIT_RATIOS[2]*100)} "
          f"(train/val/test), grouping by source photo:\n")

    for class_dir in class_dirs:
        moved = split_class(class_dir, rng)
        total = sum(moved.values())
        # The original class folder should now be empty of images; remove it
        # if nothing is left behind.
        if not any(class_dir.iterdir()):
            class_dir.rmdir()
        print(f"  {class_dir.name}: {total} files "
              f"(train={moved['train']}, val={moved['val']}, test={moved['test']})")

    print("\nDone.")


if __name__ == "__main__":
    split_dataset()
