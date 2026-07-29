import os, sys, json
import utils.constants as constants

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_class_names(directory=None):
    # 1. Explicit directory wins. Training and evaluation scripts pass this.
    if directory is not None:
        return sorted(os.listdir(directory))

    # 2. A class_names.json shipped alongside the model weights. This is the
    #    only source that cannot drift from the loaded models, so it is
    #    preferred at inference time.
    manifest = os.path.join(constants.MODEL_DIR, "class_names.json")
    if os.path.exists(manifest):
        with open(manifest) as f:
            return json.load(f)

    # 3. Fall back to scanning the dataset directory (local dev).
    fallback = os.path.join(_PROJECT_ROOT, constants.DATA_PATH, "train")
    try:
        return sorted(os.listdir(fallback))
    except FileNotFoundError:
        raise FileNotFoundError(
            f"No class names available. Looked for {manifest}, then {fallback}. "
            "Ship a class_names.json with the model weights, or point DATA_PATH "
            "at the training data."
        )