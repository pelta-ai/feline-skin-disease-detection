# This file holds paths to all folders as well as common constants used in this project
import os, sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


TRAINED_MODELS_PATH = "trained_models"
MODEL_PROBS_PATH = "model_probs"
TEST_IMAGES_PATH = "test_images"
TEST_RESULTS_PATH = "test_results"

DATA_PATH = "new_data"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

DUPLICATE_AUDIT_PATH = os.path.join("src", "duplicate_image_audit")
DUPLICATE_AUDIT_FEATURES_NAME = "dinov2_features.pt"

CNN_DATA_NPZ_NAME = "feline_skin_disease_sample_data"
CNN_MODEL_PATH = os.path.join(TRAINED_MODELS_PATH, "sample_cnn.keras")

# Ensemble used for final inference. Frozen transfer-learning gave the best
# reliability/performance combo (lowest seed-to-seed variance); EfficientNet-B0
# and ResNet-50 are complementary on the weaker classes. Probabilities are
# averaged equally across all models, so keep the per-architecture seed counts
# balanced to weight the two architectures equally.
ENSEMBLE_SEEDS = [1, 2, 3, 4, 5]
ENSEMBLE_MODEL_PATHS = [
    os.path.join(TRAINED_MODELS_PATH, f"{arch}_frozen_seed_{seed}.keras")
    for arch in ("new_mobilenetv3small",)
    for seed in ENSEMBLE_SEEDS
]

TEMP_FOLDER_PATH = "temp_folder"
TEMP_FOLDER_RAW_PATH = os.path.join(TEMP_FOLDER_PATH, "raw_image")
TEMP_FOLDER_ANNOTATED_PATH = os.path.join(TEMP_FOLDER_PATH, "annotated_image")

#Shared Classifier Head Vars
IMG_SIZE = (224, 224)
BATCH = 32
SEED = 42

T_VALUE_ENSEMBLE = 1.1187

HF_BUCKET_URI = "hf://buckets/anishanup/felineskindiseasedetectionmodels"