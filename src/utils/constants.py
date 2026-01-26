# This file holds paths to all folders as well as common constants used in this project
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

TRAINED_MODELS_PATH = "trained_models"
TEST_IMAGES_PATH = "test_images"
TEST_RESULTS_PATH = "test_results"

DATA_PATH = "sample_model_data"
DATA_IMAGES_PATH = os.path.join(DATA_PATH, "images")
DATA_LABELS_PATH = os.path.join(DATA_PATH, "labels")

CNN_DATA_NPZ_NAME = "feline_skin_disease_sample_data"
CNN_MODEL_PATH = os.path.join(TRAINED_MODELS_PATH, "sample_cnn.keras")
YOLO_MODEL_PATH = os.path.join(TRAINED_MODELS_PATH, "sample_yolo.pt")

TEMP_FOLDER_PATH = "temp_folder"
TEMP_FOLDER_RAW_PATH = os.path.join(TEMP_FOLDER_PATH, "raw_image")
TEMP_FOLDER_ANNOTATED_PATH = os.path.join(TEMP_FOLDER_PATH, "annotated_image")

#BGR Values
DISEASE_COLORS = {'acne': (66, 66, 245), 'flea_allergy': (66, 170, 245), 'lumps_and_bumps': (66, 239, 245)}