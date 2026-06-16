"""
Find (and optionally remove) images that Keras can enumerate by extension but
TensorFlow cannot actually decode.

keras.utils.image_dataset_from_directory filters only by file extension, so a
corrupt download, an HTML page saved as .jpg, or a WebP renamed to .jpg passes
enumeration and then crashes training with:
    InvalidArgumentError: Unknown image file format.

This scans every image under a directory using the SAME decoder training uses
(tf.image.decode_image, expand_animations=False) and reports the undecodable
files. With --delete it removes them; with --quarantine DIR it moves them aside.

Usage:
    python src/data_manipulation/clean_corrupt_images.py                 # report only
    python src/data_manipulation/clean_corrupt_images.py --delete        # remove bad files
    python src/data_manipulation/clean_corrupt_images.py --quarantine bad # move bad files
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

import tensorflow as tf

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.constants as constants

# Extensions Keras' image_dataset_from_directory enumerates by default.
ENUMERATED_EXTS = {".bmp", ".gif", ".jpeg", ".jpg", ".png"}


def is_decodable(path: Path) -> bool:
    """True if TF can decode the file the same way training does."""
    try:
        data = tf.io.read_file(str(path))
        tf.image.decode_image(data, channels=3, expand_animations=False)
        return True
    except (tf.errors.InvalidArgumentError, tf.errors.NotFoundError, Exception):
        return False


def find_corrupt(directory: str):
    """Return a list of undecodable image files under `directory`."""
    root = Path(directory)
    bad = []
    checked = 0
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in ENUMERATED_EXTS:
            continue
        checked += 1
        if not is_decodable(path):
            bad.append(path)
    print(f"Checked {checked} images under {root}; {len(bad)} undecodable.")
    return bad


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default=constants.DATA_PATH,
                        help="Root to scan (default: constants.DATA_PATH)")
    parser.add_argument("--delete", action="store_true",
                        help="Delete undecodable files")
    parser.add_argument("--quarantine", metavar="DIR",
                        help="Move undecodable files into DIR instead of deleting")
    args = parser.parse_args()

    bad = find_corrupt(args.directory)
    for p in bad:
        print(f"  BAD: {p}")

    if not bad:
        return

    if args.quarantine:
        qroot = Path(args.quarantine)
        for p in bad:
            dest = qroot / p.relative_to(args.directory)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), str(dest))
        print(f"Moved {len(bad)} files into {qroot}.")
    elif args.delete:
        for p in bad:
            p.unlink()
        print(f"Deleted {len(bad)} files.")
    else:
        print("\nReport only. Re-run with --delete or --quarantine DIR to act.")


if __name__ == "__main__":
    main()
