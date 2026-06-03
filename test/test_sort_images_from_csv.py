"""
Unit tests for sort_images_from_csv.py

Run with: pytest test/test_sort_images_from_csv.py -v
"""

from pathlib import Path

import pandas as pd
import pytest

from src.data_manipulation.sort_images_from_csv import CATEGORIES, sort_images


@pytest.fixture
def setup_data(tmp_path):
    """Create a temporary directory mimicking new_data/ structure."""
    split_dir = tmp_path / "test"
    split_dir.mkdir()

    # Create dummy images
    images = {
        "img_dermatitis.jpg": {"demodicosis": 0, "dermatitis": 1, "flea_allergy": 0, "fungus": 0, "ringworm": 0, "scabies": 0},
        "img_fungus.jpg": {"demodicosis": 0, "dermatitis": 0, "flea_allergy": 0, "fungus": 1, "ringworm": 0, "scabies": 0},
        "img_multi.jpg": {"demodicosis": 0, "dermatitis": 0, "flea_allergy": 1, "fungus": 0, "ringworm": 1, "scabies": 0},
        "img_no_category.jpg": {"demodicosis": 0, "dermatitis": 0, "flea_allergy": 0, "fungus": 0, "ringworm": 0, "scabies": 0},
    }

    rows = []
    for filename, labels in images.items():
        (split_dir / filename).write_bytes(b"fake image data")
        rows.append({"filename": filename, **labels})

    # Write CSV at parent level: tmp_path/test_classes.csv
    df = pd.DataFrame(rows)
    csv_path = tmp_path / "test_classes.csv"
    df.to_csv(csv_path, index=False)

    return tmp_path, csv_path, split_dir


def test_single_category_sorted(setup_data):
    """Images with one category get moved into the correct subfolder."""
    tmp_path, csv_path, split_dir = setup_data

    sort_images(str(csv_path))

    assert (split_dir / "dermatitis" / "img_dermatitis.jpg").exists()
    assert (split_dir / "fungus" / "img_fungus.jpg").exists()
    # Original should no longer be in root
    assert not (split_dir / "img_dermatitis.jpg").exists()
    assert not (split_dir / "img_fungus.jpg").exists()


def test_multi_label_copied_to_all(setup_data):
    """Images with multiple labels get moved to primary and copied to others."""
    tmp_path, csv_path, split_dir = setup_data

    sort_images(str(csv_path))

    assert (split_dir / "flea_allergy" / "img_multi.jpg").exists()
    assert (split_dir / "ringworm" / "img_multi.jpg").exists()
    assert not (split_dir / "img_multi.jpg").exists()


def test_no_category_skipped(setup_data):
    """Images with no category label stay in place."""
    tmp_path, csv_path, split_dir = setup_data

    sort_images(str(csv_path))

    # Should remain in the root since it has no category
    assert (split_dir / "img_no_category.jpg").exists()


def test_missing_image_skipped(tmp_path):
    """Rows referencing missing files are skipped without error."""
    split_dir = tmp_path / "test"
    split_dir.mkdir()

    df = pd.DataFrame([{
        "filename": "does_not_exist.jpg",
        "demodicosis": 0, "dermatitis": 1, "flea_allergy": 0,
        "fungus": 0, "ringworm": 0, "scabies": 0,
    }])
    csv_path = tmp_path / "test_classes.csv"
    df.to_csv(csv_path, index=False)

    # Should not raise
    sort_images(str(csv_path))


def test_csv_not_found():
    """Passing a nonexistent CSV exits with error."""
    with pytest.raises(SystemExit):
        sort_images("/nonexistent/path/test_classes.csv")


def test_image_dir_not_found(tmp_path):
    """If the derived image directory doesn't exist, exits with error."""
    csv_path = tmp_path / "train_classes.csv"
    csv_path.write_text("filename,demodicosis,dermatitis,flea_allergy,fungus,ringworm,scabies\n")

    with pytest.raises(SystemExit):
        sort_images(str(csv_path))
