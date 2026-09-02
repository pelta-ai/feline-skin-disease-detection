import os, sys
import numpy as np
import keras

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import src.ensemble as ensemble
from src.classifiers.base_classifier import BaseClassifier
from src.classifiers.classifier_factory import ClassifierFactory
from src.utils import constants

N_BINS = 10

def _create_cnn_instance(arch="mobilenetv3small"):
    # Only used for img_size / batch_size when building the datasets - the
    # ensemble members carry their own preprocessing inside their graphs.
    return ClassifierFactory.create(arch)

def _make_split_dataset(cnn, split):
    """BaseClassifier.make_sub_datasets is gone; the CV pipeline builds datasets
    from fold_assignments.csv instead. The ensemble members predate the folds -
    they were trained on the original train/val/test directories - so score them
    on those same directories. Reading a CV fold here would put images the
    ensemble trained on into its own validation and test sets.
    """
    return keras.utils.image_dataset_from_directory(
        os.path.join(constants.PROJECT_ROOT, constants.DATA_PATH, split),
        image_size=cnn.img_size,
        batch_size=cnn.batch_size,
        shuffle=False,
    )

def _get_x_and_y_batches(dataset):
    x_batch_list = []
    y_batch_list = []

    for x_batch, y_batch in dataset:
        x_batch_list.append(x_batch)
        y_batch_list.append(y_batch)

    return np.concatenate(x_batch_list, axis=0), np.concatenate(y_batch_list, axis=0)

def implement_calibration_on_ensemble(n_bins=N_BINS):
    cnn = _create_cnn_instance()
    val_images, y_true_val = _get_x_and_y_batches(_make_split_dataset(cnn, "val"))
    test_images, y_true_test = _get_x_and_y_batches(_make_split_dataset(cnn, "test"))

    ens_val_probs  = ensemble.ensemble_predict(val_images, low_mem=True)
    ens_test_probs = ensemble.ensemble_predict(test_images, low_mem=True)

    T = BaseClassifier.fit_temperature_from_probs(y_true_val, ens_val_probs)
    ens_test_probs_cal = BaseClassifier.scale(ens_test_probs, T)

    # expected_calibration_error returns (ece, per-bin counts). The counts are
    # what say whether the ECE rests on a handful of populated bins.
    ece_before, bins_before = BaseClassifier.expected_calibration_error(
        y_true_test, ens_test_probs, n_bins
    )
    ece_after, bins_after = BaseClassifier.expected_calibration_error(
        y_true_test, ens_test_probs_cal, n_bins
    )

    metrics = {
        "temperature": T,
        "n_images": len(y_true_test),
        "ece_before": ece_before, "ece_after": ece_after,
        "bin_counts_before": bins_before, "bin_counts_after": bins_after,
        "brier_before": BaseClassifier.brier_score(y_true_test, ens_test_probs),
        "brier_after": BaseClassifier.brier_score(y_true_test, ens_test_probs_cal),
        "nll_before": BaseClassifier.negative_log_likelihood(y_true_test, ens_test_probs),
        "nll_after": BaseClassifier.negative_log_likelihood(y_true_test, ens_test_probs_cal),
    }

    print(f"T = {T:.4f}   ({metrics['n_images']} test images)")
    for name in ("ece", "brier", "nll"):
        print(f"{name.upper():5s} before: {metrics[f'{name}_before']:.4f}   "
              f"after: {metrics[f'{name}_after']:.4f}")

    edges = np.linspace(0.0, 1.0, n_bins + 1)
    print("\nconfidence bin   before   after")
    for lo, hi, before, after in zip(edges[:-1], edges[1:], bins_before, bins_after):
        print(f"  ({lo:.1f}, {hi:.1f}]   {before:6d}  {after:6d}")

    return metrics

if __name__ == "__main__":
    implement_calibration_on_ensemble()
