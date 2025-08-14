# This file holds paths to all folders as well as common constants used in this project

TRAINED_MODELS_PATH = "trained_models"
TEST_IMAGES_PATH = "test_images"
TEST_RESULTS_PATH = "test_results"

DATA_PATH = "sample_model_data"
DATA_IMAGES_PATH = DATA_PATH + "\\images"
DATA_LABELS_PATH = DATA_PATH + "\\labels"

CNN_DATA_NPZ_NAME = "feline_skin_disease_sample_data"
CNN_MODEL_PATH = TRAINED_MODELS_PATH + "\\sample_cnn.keras"
YOLO_MODEL_PATH = TRAINED_MODELS_PATH + "\\sample_yolo.pt"

#BGR Values
DISEASE_COLORS = {'acne': (66, 66, 245), 'flea_allergy': (66, 170, 245), 'lumps_and_bumps': (66, 239, 245)}