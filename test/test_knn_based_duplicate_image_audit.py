import json
import os

import numpy as np
import pytest
import torch

from duplicate_image_audit.knn_based_duplicate_image_audit import KNNDuplicateImageAudit

# DINOv2-base embedding width. Nothing here depends on the real model, but keeping
# the width honest means the tests exercise the same shapes production does.
FEATURE_DIM = 768


def one_hot(axis, scale=1.0):
    """A vector pointing along a single axis. Two different axes are orthogonal,
    which is cosine distance 1.0 - comfortably 'not a duplicate'."""
    vector = np.zeros(FEATURE_DIM)
    vector[axis] = scale

    return torch.tensor(vector, dtype=torch.float32)


def vector_at_distance(distance, axis_a=0, axis_b=1):
    """Builds a unit vector sitting at exactly `distance` cosine distance from one_hot(axis_a).

    For unit vectors, cosine distance = 1 - cos(theta), so theta = arccos(1 - distance).
    """
    theta = np.arccos(np.clip(1.0 - distance, -1.0, 1.0))
    vector = np.zeros(FEATURE_DIM)
    vector[axis_a] = np.cos(theta)
    vector[axis_b] = np.sin(theta)

    return torch.tensor(vector, dtype=torch.float32)


def pair_at_distance(distance):
    return {"a.jpg": one_hot(0), "b.jpg": vector_at_distance(distance)}


def all_pairs(*buckets):
    merged = {}
    for bucket in buckets:
        merged.update(bucket)

    return merged


class TestNormalization:
    def test_vectors_are_unit_norm(self):
        # Deliberately unnormalized inputs - real DINOv2 embeddings are not unit length
        feature_dict = {"a.jpg": one_hot(0, scale=17.0), "b.jpg": one_hot(1, scale=0.03)}

        vectors = KNNDuplicateImageAudit(feature_dict)._get_normalized_vectors()

        assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0)

    def test_vector_rows_line_up_with_key_order(self):
        """_get_normalized_vectors and _build_knn_index walk the dict separately and
        rely on insertion order matching. If that ever drifts, every reported pair
        points at the wrong file."""
        feature_dict = {f"image_{axis}.jpg": one_hot(axis) for axis in range(5)}

        audit = KNNDuplicateImageAudit(feature_dict)
        vectors = audit._get_normalized_vectors()
        image_paths = audit._build_knn_index(vectors)

        for row, image_path in enumerate(image_paths):
            expected_axis = int(image_path.split("_")[1].split(".")[0])
            assert int(np.argmax(vectors[row])) == expected_axis

    def test_accepts_batched_tensors_with_leading_dim(self):
        feature_dict = {"a.jpg": one_hot(0).reshape(1, -1), "b.jpg": one_hot(1).reshape(1, -1)}

        vectors = KNNDuplicateImageAudit(feature_dict)._get_normalized_vectors()

        assert vectors.shape == (2, FEATURE_DIM)


class TestBucketing:
    def test_identical_images_are_close_duplicates(self):
        feature_dict = {"a.jpg": one_hot(0), "b.jpg": one_hot(0)}

        close, medium, review = KNNDuplicateImageAudit(feature_dict).find_duplicate_images(
            save_duplicates=False
        )

        assert list(close) == [("a.jpg", "b.jpg")]
        assert close[("a.jpg", "b.jpg")] == pytest.approx(0.0, abs=1e-6)
        assert medium == {} and review == {}

    def test_orthogonal_images_are_not_flagged(self):
        feature_dict = {"a.jpg": one_hot(0), "b.jpg": one_hot(1)}

        close, medium, review = KNNDuplicateImageAudit(feature_dict).find_duplicate_images(
            save_duplicates=False
        )

        assert close == {} and medium == {} and review == {}

    @pytest.mark.parametrize(
        "distance, expected_bucket",
        [
            (0.000, "close"),
            (0.019, "close"),
            (0.021, "medium"),
            (0.049, "medium"),
            (0.051, "review"),
            (0.149, "review"),
            (0.160, None),
            (0.400, None),
        ],
    )
    def test_threshold_boundaries(self, distance, expected_bucket):
        audit = KNNDuplicateImageAudit(pair_at_distance(distance))
        close, medium, review = audit.find_duplicate_images(save_duplicates=False)

        landed = {"close": close, "medium": medium, "review": review}
        found = {name: bucket for name, bucket in landed.items() if bucket}

        if expected_bucket is None:
            assert found == {}, f"distance {distance} should not be reported"
        else:
            assert list(found) == [expected_bucket]
            assert found[expected_bucket][("a.jpg", "b.jpg")] == pytest.approx(distance, abs=1e-4)

    def test_custom_thresholds_are_respected(self):
        audit = KNNDuplicateImageAudit(
            pair_at_distance(0.30), close_threshold=0.1, medium_threshold=0.2, review_threshold=0.4
        )
        close, medium, review = audit.find_duplicate_images(save_duplicates=False)

        assert close == {} and medium == {}
        assert list(review) == [("a.jpg", "b.jpg")]

    def test_out_of_order_thresholds_rejected(self):
        with pytest.raises(ValueError, match="non-decreasing"):
            KNNDuplicateImageAudit({}, close_threshold=0.2, medium_threshold=0.05)


class TestPairHygiene:
    def test_no_image_is_paired_with_itself(self):
        feature_dict = {f"image_{axis}.jpg": one_hot(axis) for axis in range(4)}

        results = all_pairs(*KNNDuplicateImageAudit(feature_dict).find_duplicate_images(
            save_duplicates=False
        ))

        assert all(image_a != image_b for image_a, image_b in results)

    def test_each_pair_reported_once_not_in_both_orders(self):
        feature_dict = {"a.jpg": one_hot(0), "b.jpg": one_hot(0)}

        results = all_pairs(*KNNDuplicateImageAudit(feature_dict).find_duplicate_images(
            save_duplicates=False
        ))

        assert len(results) == 1
        assert ("b.jpg", "a.jpg") not in results

    def test_pair_keys_are_sorted(self):
        feature_dict = {"z.jpg": one_hot(0), "a.jpg": one_hot(0)}

        results = all_pairs(*KNNDuplicateImageAudit(feature_dict).find_duplicate_images(
            save_duplicates=False
        ))

        assert list(results) == [("a.jpg", "z.jpg")]

    def test_cluster_larger_than_five_is_fully_reported(self):
        """Regression: a fixed n_neighbors=5 index silently truncated any burst of
        near-identical frames larger than five."""
        feature_dict = {f"burst_{i}.jpg": one_hot(0) for i in range(7)}

        close, _, _ = KNNDuplicateImageAudit(feature_dict).find_duplicate_images(
            save_duplicates=False
        )

        assert len(close) == 21  # C(7, 2)

    def test_distinct_clusters_do_not_bleed_together(self):
        feature_dict = {
            "cluster_a_1.jpg": one_hot(0),
            "cluster_a_2.jpg": one_hot(0),
            "cluster_b_1.jpg": one_hot(1),
            "cluster_b_2.jpg": one_hot(1),
        }

        close, _, _ = KNNDuplicateImageAudit(feature_dict).find_duplicate_images(
            save_duplicates=False
        )

        assert set(close) == {
            ("cluster_a_1.jpg", "cluster_a_2.jpg"),
            ("cluster_b_1.jpg", "cluster_b_2.jpg"),
        }


class TestDegenerateInputs:
    @pytest.mark.parametrize("image_count", [0, 1, 2, 3])
    def test_small_datasets_do_not_crash(self, image_count):
        """A fixed n_neighbors=5 raised 'n_neighbors <= n_samples_fit' below five images."""
        feature_dict = {f"image_{i}.jpg": one_hot(i) for i in range(image_count)}

        close, medium, review = KNNDuplicateImageAudit(feature_dict).find_duplicate_images(
            save_duplicates=False
        )

        assert close == {} and medium == {} and review == {}

    def test_two_identical_images_is_enough_to_report(self):
        feature_dict = {"a.jpg": one_hot(0), "b.jpg": one_hot(0)}

        close, _, _ = KNNDuplicateImageAudit(feature_dict).find_duplicate_images(
            save_duplicates=False
        )

        assert len(close) == 1


class TestReportWriting:
    def test_writes_one_json_file_per_band(self, tmp_path):
        feature_dict = {
            "a.jpg": one_hot(0),
            "b.jpg": one_hot(0),
            "c.jpg": vector_at_distance(0.03),
            "d.jpg": vector_at_distance(0.10),
        }

        KNNDuplicateImageAudit(feature_dict).find_duplicate_images(output_dir=str(tmp_path))

        for band in ("close", "medium", "review"):
            assert (tmp_path / f"{band}_duplicates.json").exists()

    def test_report_survives_a_json_round_trip(self, tmp_path):
        """Tuple keys used to make json.dump raise TypeError outright."""
        feature_dict = {"a.jpg": one_hot(0), "b.jpg": one_hot(0)}

        KNNDuplicateImageAudit(feature_dict).find_duplicate_images(output_dir=str(tmp_path))

        with open(tmp_path / "close_duplicates.json") as json_file:
            records = json.load(json_file)

        assert records == [{"image_a": "a.jpg", "image_b": "b.jpg", "distance": 0.0}]

    def test_records_are_sorted_closest_first(self, tmp_path):
        feature_dict = {
            "base.jpg": one_hot(0),
            "far.jpg": vector_at_distance(0.14, axis_b=1),
            "near.jpg": vector_at_distance(0.06, axis_b=2),
        }

        KNNDuplicateImageAudit(feature_dict).find_duplicate_images(output_dir=str(tmp_path))

        with open(tmp_path / "review_duplicates.json") as json_file:
            records = json.load(json_file)

        distances = [record["distance"] for record in records]
        assert distances == sorted(distances)

    def test_save_duplicates_false_writes_nothing(self, tmp_path):
        feature_dict = {"a.jpg": one_hot(0), "b.jpg": one_hot(0)}

        KNNDuplicateImageAudit(feature_dict).find_duplicate_images(
            save_duplicates=False, output_dir=str(tmp_path)
        )

        assert list(tmp_path.iterdir()) == []

    def test_creates_output_directory_if_missing(self, tmp_path):
        output_dir = tmp_path / "does" / "not" / "exist"
        feature_dict = {"a.jpg": one_hot(0), "b.jpg": one_hot(0)}

        KNNDuplicateImageAudit(feature_dict).find_duplicate_images(output_dir=str(output_dir))

        assert (output_dir / "close_duplicates.json").exists()


class TestQueryHelper:
    def test_unknown_path_raises(self):
        audit = KNNDuplicateImageAudit({"a.jpg": one_hot(0), "b.jpg": one_hot(1)})
        vectors = audit._get_normalized_vectors()
        image_paths = audit._build_knn_index(vectors)

        with pytest.raises(ValueError, match="not found in extracted features"):
            audit._query_similar_images("missing.jpg", image_paths, vectors, verbose=False)

    def test_top_k_is_capped_at_dataset_size(self):
        """Asking for 5 neighbours in a 3-image index used to raise."""
        audit = KNNDuplicateImageAudit({f"image_{i}.jpg": one_hot(i) for i in range(3)})
        vectors = audit._get_normalized_vectors()
        image_paths = audit._build_knn_index(vectors)

        distances, indices = audit._query_similar_images(
            "image_0.jpg", image_paths, vectors, top_k=5, verbose=False
        )

        assert distances.shape == (1, 3)
        assert indices.shape == (1, 3)
