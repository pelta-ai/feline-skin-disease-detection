import numpy as np
import os, sys
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import normalize
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from duplicate_image_audit.feature_extractor import FeatureExtractor
import utils.constants as constants
from utils.paths import abs_path

# Cosine-distance bands for DINOv2 embeddings (distance = 1 - cosine similarity).
# CLOSE  : re-encodes, resizes, recompressions - safe to treat as identical.
# MEDIUM : crops, flips, rotations, brightness/watermark changes.
# REVIEW : same lesion or same photo session, different frame. Needs human eyes,
#          but must never be split across train/test - that is the leakage case.
CLOSE_THRESHOLD = 0.02
MEDIUM_THRESHOLD = 0.05
REVIEW_THRESHOLD = 0.15


class KNNDuplicateImageAudit:
    def __init__(self, feature_dict, metric="cosine", close_threshold=CLOSE_THRESHOLD,
                 medium_threshold=MEDIUM_THRESHOLD, review_threshold=REVIEW_THRESHOLD):
        if not (close_threshold <= medium_threshold <= review_threshold):
            raise ValueError(
                "Thresholds must be non-decreasing, got "
                f"close={close_threshold}, medium={medium_threshold}, review={review_threshold}."
            )

        self.feature_dict = feature_dict
        self.metric = metric
        self.close_threshold = close_threshold
        self.medium_threshold = medium_threshold
        self.review_threshold = review_threshold
        self.knn_model = None

    @staticmethod
    def _to_numpy(value):
        """Accepts a torch tensor or an array-like and returns a flat numpy vector."""
        if hasattr(value, "detach"):
            value = value.detach().cpu().numpy()

        return np.asarray(value).squeeze()

    def _get_normalized_vectors(self):
        """Stacks the embeddings into an L2-normalized matrix, in feature_dict key order."""
        if not self.feature_dict:
            return np.empty((0, 0), dtype=np.float64)

        raw_vectors = np.array([self._to_numpy(value) for value in self.feature_dict.values()])
        normalized_vectors = normalize(raw_vectors, norm='l2')

        return normalized_vectors

    def _build_knn_index(self, normalized_vectors):
        image_paths = list(self.feature_dict.keys())

        # A radius index rather than a fixed top-k: duplicate clusters have no known
        # size, and a hardcoded k silently truncates any burst larger than k.
        self.knn_model = NearestNeighbors(radius=self.review_threshold, metric=self.metric, algorithm='auto')
        self.knn_model.fit(normalized_vectors)

        return image_paths

    def _query_similar_images(self, image_path: str, image_paths, normalized_vectors, top_k: int = 5,
                              verbose: bool = True):
        """Debug helper: prints the top_k nearest neighbours of one image in the dataset."""

        if image_path not in self.feature_dict:
            raise ValueError(f"Query image {image_path} not found in extracted features.")

        # Get index of the query image to find its normalized vector
        query_idx = image_paths.index(image_path)
        query_vector = normalized_vectors[query_idx].reshape(1, -1)

        # Never ask for more neighbours than there are images in the index
        top_k = min(top_k, len(image_paths))

        distances, indices = self.knn_model.kneighbors(query_vector, n_neighbors=top_k)

        if verbose:
            print(f"\nTop {top_k} matches for: {os.path.basename(image_path)}")
            for dist, idx in zip(distances[0], indices[0]):
                print(f"-> Distance: {dist:.4f} | Path: {image_paths[idx]}")

        return distances, indices

    def _bucket_for(self, distance):
        """Maps a cosine distance to a band name, or None if the pair is not a duplicate."""
        if distance <= self.close_threshold:
            return "close"
        if distance <= self.medium_threshold:
            return "medium"
        if distance <= self.review_threshold:
            return "review"

        return None

    def find_duplicate_images(self, save_duplicates: bool = True, output_dir=None):
        image_paths = list(self.feature_dict.keys())
        buckets = {"close": {}, "medium": {}, "review": {}}

        # Fewer than two images means there is nothing to compare, and fitting the
        # index on an empty matrix would raise.
        if len(image_paths) >= 2:
            normalized_vectors = self._get_normalized_vectors()
            image_paths = self._build_knn_index(normalized_vectors=normalized_vectors)

            # Query the whole matrix in one call. The epsilon keeps pairs sitting exactly
            # on review_threshold inside the candidate set; _bucket_for owns the real cut.
            distances, indices = self.knn_model.radius_neighbors(
                normalized_vectors,
                radius=self.review_threshold + 1e-9,
                return_distance=True,
                sort_results=True,
            )

            seen_pairs = set()

            for query_idx, (neighbour_distances, neighbour_indices) in enumerate(zip(distances, indices)):
                for distance, neighbour_idx in zip(neighbour_distances, neighbour_indices):
                    # Every image is its own nearest neighbour at distance 0
                    if neighbour_idx == query_idx:
                        continue

                    # (a, b) and (b, a) are the same finding - record it once
                    pair = tuple(sorted((image_paths[query_idx], image_paths[neighbour_idx])))
                    if pair in seen_pairs:
                        continue

                    bucket = self._bucket_for(distance)
                    if bucket is None:
                        continue

                    seen_pairs.add(pair)
                    buckets[bucket][pair] = float(distance)

        print(
            f"\nDuplicate audit over {len(image_paths)} images: "
            f"{len(buckets['close'])} close, {len(buckets['medium'])} medium, "
            f"{len(buckets['review'])} to review."
        )

        if save_duplicates:
            self.save_duplicate_report(buckets, output_dir=output_dir)

        return buckets["close"], buckets["medium"], buckets["review"]

    def save_duplicate_report(self, buckets, output_dir=None):
        """Writes one JSON file per band as a list of records, closest pairs first."""
        output_dir = abs_path(output_dir or constants.DUPLICATE_AUDIT_PATH)
        os.makedirs(output_dir, exist_ok=True)

        written = {}

        for name, pairs in buckets.items():
            records = [
                {"image_a": image_a, "image_b": image_b, "distance": round(distance, 6)}
                for (image_a, image_b), distance in sorted(pairs.items(), key=lambda item: item[1])
            ]

            output_path = os.path.join(output_dir, f"{name}_duplicates.json")
            with open(output_path, "w") as json_file:
                json.dump(records, json_file, indent=4)

            written[name] = output_path

        return written


if __name__ == "__main__":
    fe = FeatureExtractor()
    feature_dict = fe.execute_full_pipeline(save_to_disk=True)

    knn = KNNDuplicateImageAudit(feature_dict=feature_dict)
    close_duplicates, medium_duplicates, review_duplicates = knn.find_duplicate_images()
