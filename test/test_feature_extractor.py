import os

import numpy as np
import pytest
import torch

from duplicate_image_audit.feature_extractor import FeatureExtractor


def make_file(root, relative_path):
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"not a real image")

    return path


class TestImageDiscovery:
    def test_picks_up_supported_extensions(self, tmp_path):
        for name in ("a.jpg", "b.jpeg", "c.png", "d.bmp", "e.webp", "f.tiff"):
            make_file(tmp_path, name)

        found = FeatureExtractor(dataset_path=tmp_path)._get_image_paths()

        assert len(found) == 6

    def test_ignores_non_image_files(self, tmp_path):
        make_file(tmp_path, "keep.jpg")
        for name in ("notes.txt", "labels.csv", "model.keras", "README"):
            make_file(tmp_path, name)

        found = FeatureExtractor(dataset_path=tmp_path)._get_image_paths()

        assert [os.path.basename(path) for path in found] == ["keep.jpg"]

    def test_extension_matching_is_case_insensitive(self, tmp_path):
        make_file(tmp_path, "shouty.JPG")
        make_file(tmp_path, "mixed.PnG")

        found = FeatureExtractor(dataset_path=tmp_path)._get_image_paths()

        assert len(found) == 2

    def test_walks_class_subdirectories(self, tmp_path):
        make_file(tmp_path, "train/mites/one.jpg")
        make_file(tmp_path, "train/ringworm/two.jpg")
        make_file(tmp_path, "test/mites/three.jpg")

        found = FeatureExtractor(dataset_path=tmp_path)._get_image_paths()

        assert len(found) == 3
        assert all(os.path.isabs(path) or os.path.exists(path) for path in found)

    def test_empty_directory_yields_no_paths(self, tmp_path):
        assert FeatureExtractor(dataset_path=tmp_path)._get_image_paths() == []


class TestBatching:
    @pytest.mark.parametrize(
        "image_count, batch_size, expected_sizes",
        [
            (10, 3, [3, 3, 3, 1]),
            (9, 3, [3, 3, 3]),
            (2, 5, [2]),
            (1, 1, [1]),
            (0, 4, []),
        ],
    )
    def test_batch_sizes(self, image_count, batch_size, expected_sizes):
        paths = [f"image_{i}.jpg" for i in range(image_count)]

        batches = FeatureExtractor(batch_size=batch_size)._divide_images_in_batches(paths)

        assert [len(batch) for batch in batches] == expected_sizes

    def test_no_image_is_dropped_or_duplicated(self):
        paths = [f"image_{i}.jpg" for i in range(23)]

        batches = FeatureExtractor(batch_size=4)._divide_images_in_batches(paths)

        assert [path for batch in batches for path in batch] == paths


class TestFeaturePersistence:
    def test_save_and_load_round_trip(self, tmp_path):
        feature_dict = {
            "a.jpg": torch.arange(4, dtype=torch.float32),
            "b.jpg": torch.ones(4, dtype=torch.float32),
        }

        extractor = FeatureExtractor()
        output_path = extractor.save_features(feature_dict, output_dir=str(tmp_path))
        reloaded = FeatureExtractor.load_features(output_dir=str(tmp_path))

        assert os.path.exists(output_path)
        assert list(reloaded) == list(feature_dict)
        for key in feature_dict:
            assert torch.equal(reloaded[key], feature_dict[key])

    def test_creates_output_directory_if_missing(self, tmp_path):
        output_dir = tmp_path / "nested" / "features"

        output_path = FeatureExtractor().save_features({"a.jpg": torch.zeros(2)}, output_dir=str(output_dir))

        assert os.path.exists(output_path)


class TestDeviceSelection:
    def test_selects_a_device_and_reports_gpu_use(self):
        extractor = FeatureExtractor()
        extractor.model = torch.nn.Linear(2, 2)

        using_gpu = extractor._move_model_to_GPU()

        assert extractor.device.type in {"cuda", "mps", "cpu"}
        assert using_gpu == (extractor.device.type != "cpu")


@pytest.mark.slow
class TestRealForwardPass:
    """Downloads facebook/dinov2-base on first run. Deselect with -m 'not slow'."""

    def test_embeddings_are_stable_and_discriminative(self, tmp_path):
        from PIL import Image

        rng = np.random.default_rng(0)
        noise = rng.integers(0, 255, size=(64, 64, 3), dtype=np.uint8)

        original = tmp_path / "original.jpg"
        copy = tmp_path / "copy.jpg"
        different = tmp_path / "different.jpg"

        Image.fromarray(noise).save(original)
        Image.fromarray(noise).save(copy)
        Image.fromarray(rng.integers(0, 255, size=(64, 64, 3), dtype=np.uint8)).save(different)

        extractor = FeatureExtractor(dataset_path=tmp_path, batch_size=2)
        feature_dict = extractor.execute_full_pipeline(save_to_disk=False)

        assert len(feature_dict) == 3
        assert all(tensor.ndim == 1 for tensor in feature_dict.values())

        def cosine_distance(path_a, path_b):
            a = feature_dict[str(path_a)].numpy()
            b = feature_dict[str(path_b)].numpy()
            return 1.0 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        # Byte-identical re-encodes must sit far below the close-duplicate cut,
        # and an unrelated image must sit well above it.
        assert cosine_distance(original, copy) < 0.02
        assert cosine_distance(original, different) > 0.02
