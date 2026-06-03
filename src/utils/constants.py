# This file holds paths to all folders as well as common constants used in this project
import os
from pathlib import Path

CLASS_NAMES = ["demodicosis", "dermatitis", "flea allergy", "fungus", "ringworm", "scabies"]

BASE_DIR = Path(__file__).resolve().parents[1]

TRAINED_MODELS_PATH = "trained_models"
TEST_IMAGES_PATH = "test_images"
TEST_RESULTS_PATH = "test_results"

DATA_PATH = "new_data"
DATA_IMAGES_PATH = DATA_PATH

CNN_DATA_NPZ_NAME = "feline_skin_disease_sample_data"
CNN_MODEL_PATH = os.path.join(TRAINED_MODELS_PATH, "sample_cnn.keras")
YOLO_MODEL_PATH = os.path.join(TRAINED_MODELS_PATH, "sample_yolo.pt")

# Ensemble used for final inference. Frozen transfer-learning gave the best
# reliability/performance combo (lowest seed-to-seed variance); EfficientNet-B0
# and ResNet-50 are complementary on the weaker classes. Probabilities are
# averaged equally across all models, so keep the per-architecture seed counts
# balanced to weight the two architectures equally.
ENSEMBLE_SEEDS = [1, 2, 3, 4, 5]
ENSEMBLE_MODEL_PATHS = [
    os.path.join(TRAINED_MODELS_PATH, f"{arch}_frozen_seed_{seed}.keras")
    for arch in ("efficientnetb0", "resnet50")
    for seed in ENSEMBLE_SEEDS
]

TEMP_FOLDER_PATH = "temp_folder"
TEMP_FOLDER_RAW_PATH = os.path.join(TEMP_FOLDER_PATH, "raw_image")
TEMP_FOLDER_ANNOTATED_PATH = os.path.join(TEMP_FOLDER_PATH, "annotated_image")

#BGR Values
DISEASE_COLORS = {'acne': (66, 66, 245), 'flea_allergy': (66, 170, 245), 'lumps_and_bumps': (66, 239, 245)}

#Shared Classifier Head Vars
IMG_SIZE = (224, 224)
BATCH = 32
SEED = 42