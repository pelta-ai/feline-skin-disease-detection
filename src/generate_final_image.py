import os, sys, gc
import numpy as np
from PIL import UnidentifiedImageError
import keras


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import src.utils.constants as constants
from src.utils.get_class_names import get_class_names
from src.utils.paths import abs_path
from src.classifiers.base_classifier import BaseClassifier
import src.ensemble as ensemble

def warm_up(model_paths=None):
    paths = ensemble.get_model_paths_ready(model_paths)
    ensemble.load_ensemble(paths)


def generate_final_image(image_path, model_paths=None):
    # Preprocessing is baked into each saved model (Input -> preprocess_input ->
    # backbone), so the raw 0-255 RGB array is fed directly. Average the softmax
    # probabilities equally across every model in the ensemble.
    #
    # If the ensemble is already cached (e.g. warmed up behind Flask), reuse the
    # resident models. Otherwise — typically a one-off CLI run — load them one at
    # a time to keep peak memory low instead of holding all of them resident.

    arr = _preprocess_image(image_path=image_path)
    avg_probs = ensemble.ensemble_predict(arr, model_paths=model_paths, low_mem=False)
    avg_probs = BaseClassifier.scale(avg_probs, constants.T_VALUE_ENSEMBLE)

    indices, confidences = _get_top_k_from_array(avg_probs[0], 3)
    #top = int(np.argmax(avg_probs[0]))
    final_classes = [get_class_names()[indices[0]], get_class_names()[indices[1]], get_class_names()[indices[2]]]
    #confidence = float(avg_probs[0][top])
    print(final_classes, confidences)

    return {
        "label": final_classes,
        "confidence": confidences,
    }

def _get_top_k_from_array(array, k):
    top_indices = []
    top_values = []

    for i in range(k):
        top = next(j for j in range(len(array)) if j not in top_indices)
        for j in range(len(array)):
            if array[j] > array[top] and j not in top_indices:
                top = j
            
        top_indices.append(top)
        top_values.append(float(array[top]))

    return top_indices, top_values

def _preprocess_image(image_path):
    image_path = abs_path(image_path)

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Input image not found: {image_path}")

    try:
        image = keras.utils.load_img(image_path, target_size=constants.IMG_SIZE)
    except (FileNotFoundError, UnidentifiedImageError) as e:
        raise RuntimeError(f"Failed to load image: {image_path}") from e

    arr = keras.utils.img_to_array(image)
    arr = np.expand_dims(arr, axis=0)

    return arr
            
if __name__ == "__main__":
    generate_final_image(constants.TEST_IMAGES_PATH + '\\sample_acne_2.jpg')
