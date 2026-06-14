import os, sys
import numpy as np
from PIL import UnidentifiedImageError
import keras


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

    models = _load_ensemble(model_paths_full)

    try:
        image = keras.utils.load_img(image_path, target_size=constants.IMG_SIZE)
    except (FileNotFoundError, UnidentifiedImageError) as e:
        raise RuntimeError(f"Failed to load image: {image_path}") from e

    arr = keras.utils.img_to_array(image)
    arr = np.expand_dims(arr, axis=0)

    # Preprocessing is baked into each saved model (Input -> preprocess_input ->
    # backbone), so the raw 0-255 RGB array is fed directly. Average the softmax
    # probabilities equally across every model in the ensemble.
    avg_probs = np.mean([np.array(m(arr, training=False)) for m in models], axis=0)

    top = int(np.argmax(avg_probs[0]))
    final_class = get_class_names()[top]
    confidence = float(avg_probs[0][top])
    print(final_class, confidence)

    base_name = os.path.basename(image_path)
    base_name_without_extension = os.path.splitext(base_name)[0]
    os.makedirs(output_dir_full, exist_ok=True)
    output_path = os.path.join(output_dir_full, base_name_without_extension + ".jpg")

    image.save(output_path)
    print(f"Saved annotated image to: {output_path}")

    return {
        "label": final_class,
        "confidence": confidence,
        "output_path": output_path,
    }


if __name__ == "__main__":
    generate_final_image(constants.TEST_IMAGES_PATH + '\\sample_acne_2.jpg')
