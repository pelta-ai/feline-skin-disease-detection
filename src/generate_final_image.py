import os, sys, gc
import numpy as np
from PIL import UnidentifiedImageError
import keras
import tensorflow as tf


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.constants as constants
from utils.get_class_names import get_class_names


# Models are expensive to load (seconds each), so cache them across calls keyed
# by the resolved path tuple. Behind Flask this means the ensemble loads once on
# the first request and is reused for every prediction after that.
_MODEL_CACHE = {}


def _load_ensemble(model_paths):
    key = tuple(model_paths)
    if key not in _MODEL_CACHE:
        _MODEL_CACHE[key] = [keras.models.load_model(p) for p in model_paths]
    return _MODEL_CACHE[key]


def _avg_probs_low_mem(arr, model_paths):
    """Average ensemble probabilities while holding only one model in memory at
    a time: load, predict, free, repeat. Peak RAM stays at ~one model instead of
    the whole ensemble, which avoids swap thrashing on low-RAM machines. Slower
    (re-reads each model from disk) but the only way to run the ensemble when
    free RAM is smaller than the loaded ensemble."""
    total = None
    for p in model_paths:
        model = keras.models.load_model(p)
        probs = np.array(model(arr, training=False))
        total = probs if total is None else total + probs
        del model
        keras.backend.clear_session()
        gc.collect()
    return total / len(model_paths)


def warm_up(model_paths=None):
    """Eagerly load the ensemble into the cache so the first prediction request
    isn't slow. Safe to call once at server startup; shares _MODEL_CACHE with
    generate_final_image, so later calls reuse the already-loaded models."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _abs(path):
        return path if os.path.isabs(path) else os.path.join(project_root, path)

    if model_paths is None:
        model_paths = constants.ENSEMBLE_MODEL_PATHS

    model_paths_full = [_abs(p) for p in model_paths]
    return _load_ensemble(model_paths_full)


def generate_final_image(image_path, model_paths=None, output_dir=constants.TEMP_FOLDER_ANNOTATED_PATH):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _abs(path):
        return path if os.path.isabs(path) else os.path.join(project_root, path)

    if model_paths is None:
        model_paths = constants.ENSEMBLE_MODEL_PATHS

    model_paths_full = [_abs(p) for p in model_paths]
    print(model_paths_full)
    output_dir_full = _abs(output_dir)
    image_path = _abs(image_path)

    if not model_paths_full:
        raise ValueError("No ensemble models provided")

    for p in model_paths_full:
        if not p.endswith(".keras"):
            raise ValueError(f"Ensemble model must be a .keras model: {p}")
        if not os.path.exists(p):
            raise FileNotFoundError(f"CNN model file not found: {p}")

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Input image not found: {image_path}")

    try:
        image = keras.utils.load_img(image_path, target_size=constants.IMG_SIZE)
    except (FileNotFoundError, UnidentifiedImageError) as e:
        raise RuntimeError(f"Failed to load image: {image_path}") from e

    arr = keras.utils.img_to_array(image)
    arr = np.expand_dims(arr, axis=0)

    # Preprocessing is baked into each saved model (Input -> preprocess_input ->
    # backbone), so the raw 0-255 RGB array is fed directly. Average the softmax
    # probabilities equally across every model in the ensemble.
    #
    # If the ensemble is already cached (e.g. warmed up behind Flask), reuse the
    # resident models. Otherwise — typically a one-off CLI run — load them one at
    # a time to keep peak memory low instead of holding all of them resident.
    cache_key = tuple(model_paths_full)
    if cache_key in _MODEL_CACHE:
        models = _MODEL_CACHE[cache_key]
        avg_probs = np.mean([np.array(m(arr, training=False)) for m in models], axis=0)
    else:
        avg_probs = _avg_probs_low_mem(arr, model_paths_full)

    indices, confidences = _get_top_k_from_array(avg_probs[0], 3)
    #top = int(np.argmax(avg_probs[0]))
    final_classes = [get_class_names()[indices[0]], get_class_names()[indices[1]], get_class_names()[indices[2]]]
    #confidence = float(avg_probs[0][top])
    print(final_classes, confidences)

    base_name = os.path.basename(image_path)
    base_name_without_extension = os.path.splitext(base_name)[0]
    os.makedirs(output_dir_full, exist_ok=True)
    output_path = os.path.join(output_dir_full, base_name_without_extension + ".jpg")

    image.save(output_path)
    print(f"Saved annotated image to: {output_path}")

    return {
        "label": final_classes,
        "confidence": confidences,
        "output_path": output_path,
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
            
if __name__ == "__main__":
    generate_final_image(constants.TEST_IMAGES_PATH + '\\sample_acne_2.jpg')
