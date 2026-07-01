import os, sys
import utils.constants as constants

# Resolve the dataset path relative to the project root (two levels up from this
# file: src/utils/ -> project root) so class names load no matter what the
# current working directory is when the script is launched.
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_class_names(directory=None):
    if directory is None:
        directory = os.path.join(_PROJECT_ROOT, constants.DATA_PATH, "train")
    try:
        # Sort to match Keras' image_dataset_from_directory, which assigns class
        # indices in sorted order during training.
        return sorted(os.listdir(directory))
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Class-names directory not found: {directory}. "
            "Expected the training data folder to exist at this path."
        )
