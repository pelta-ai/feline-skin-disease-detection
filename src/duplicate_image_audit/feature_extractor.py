import os, sys
from PIL import Image
import torch
from transformers import AutoImageProcessor, AutoModel
import pillow_heif
import pillow_avif

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.constants as constants
from utils.paths import abs_path

class FeatureExtractor:
    def __init__(self, model_ckpt="facebook/dinov2-base", dataset_path=constants.DATA_PATH, batch_size=32):
        self.model_ckpt = model_ckpt
        # constants.DATA_PATH is repo-relative; resolve it so the audit finds the
        # dataset regardless of the working directory it is launched from.
        self.dataset_path = abs_path(str(dataset_path))
        self.batch_size = batch_size
        self.processor = None
        self.model = None
        self.device = None

    def _load_model_and_processor(self):
        self.processor = AutoImageProcessor.from_pretrained(self.model_ckpt)
        self.model = AutoModel.from_pretrained(self.model_ckpt)

    def _move_model_to_GPU(self) -> bool:
        """Assigns optimal execution device (CUDA -> MPS -> CPU)."""
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = torch.device("mps")  # Support for Apple Silicon
        else:
            self.device = torch.device("cpu")

        self.model.to(self.device)
        return self.device.type != "cpu"

    def _get_image_paths(self) -> list[str]:
        """Collects all file paths from the dataset directory, excluding non-image files."""
        valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
        image_paths = []

        for root, _, files in os.walk(self.dataset_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in valid_extensions:
                    image_paths.append(os.path.join(root, file))

        return image_paths

    def _divide_images_in_batches(self, image_paths: list[str]) -> list[list[str]]:
        batches = []

        for i in range(0, len(image_paths), self.batch_size):
            batches.append(image_paths[i : i + self.batch_size])

        return batches

    def _extract_features(self, image_path_batches: list[list[str]]):
        self.model.eval()
        feature_dict = {}

        with torch.no_grad():
            for path_batch in image_path_batches:
                # 1. Open all PIL images for THIS batch
                pil_images = [Image.open(p).convert("RGB") for p in path_batch]

                # 2. Process all images AT ONCE into one stacked tensor
                inputs = self.processor(images=pil_images, return_tensors="pt").to(
                    self.device
                )

                # 3. Single forward pass for the whole batch
                outputs = self.model(**inputs)

                # 4. Extract representation vectors
                if (
                    hasattr(outputs, "pooler_output")
                    and outputs.pooler_output is not None
                ):
                    embeddings = outputs.pooler_output.cpu()
                else:
                    embeddings = outputs.last_hidden_state.mean(dim=1).cpu()

                # 5. Map each vector back to its corresponding path
                for path, embedding in zip(path_batch, embeddings):
                    feature_dict[path] = embedding

        return feature_dict

    def save_features(self, feature_dict, output_dir=None):
        """Persists the {image_path: embedding} map so audits can rerun without a forward pass."""
        output_dir = abs_path(output_dir or constants.DUPLICATE_AUDIT_PATH)
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, constants.DUPLICATE_AUDIT_FEATURES_NAME)
        torch.save(feature_dict, output_path)

        return output_path

    @staticmethod
    def load_features(output_dir=None):
        """Reloads a feature map written by save_features."""
        output_dir = abs_path(output_dir or constants.DUPLICATE_AUDIT_PATH)
        output_path = os.path.join(output_dir, constants.DUPLICATE_AUDIT_FEATURES_NAME)

        return torch.load(output_path, weights_only=False)

    def execute_full_pipeline(self, save_to_disk: bool = False):
        """Orchestrates model loading, hardware setup, and feature extraction."""
        self._load_model_and_processor()
        using_gpu = self._move_model_to_GPU()

        device_name = self.device.type.upper()
        print(f"Feature Extractor initialized on device: {device_name}")

        image_paths = self._get_image_paths()
        print(f"Found {len(image_paths)} images to process.")

        batches = self._divide_images_in_batches(image_paths=image_paths)
        print(f"Divided images into {len(batches)} batches of approximately size {self.batch_size}.")

        feature_dict = self._extract_features(batches)
        print("Feature extraction complete.")

        if save_to_disk:
            self.save_features(feature_dict)
            print("Successfully saved features to disk.")

        return feature_dict