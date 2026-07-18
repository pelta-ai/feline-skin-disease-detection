import os, sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import src.ensemble as ensemble
from src.classifiers.base_classifier import BaseClassifier
from src.classifiers.classifier_factory import ClassifierFactory

def _create_cnn_instance(arch="mobilenetv3small"):
    cnn = ClassifierFactory.create(arch)
    cnn.make_sub_datasets()
    return cnn

def _get_x_and_y_batches(dataset):
    x_batch_list = []
    y_batch_list = []

    for x_batch, y_batch in dataset:
        x_batch_list.append(x_batch)
        y_batch_list.append(y_batch)

    return np.concatenate(x_batch_list, axis=0), np.concatenate(y_batch_list, axis=0)

def implement_calibration_on_ensemble():
    cnn = _create_cnn_instance()
    val_images, y_true_val = _get_x_and_y_batches(cnn.val_ds)
    test_images, y_true_test = _get_x_and_y_batches(cnn.test_ds)

    ens_val_probs  = ensemble.ensemble_predict(val_images, low_mem=True)
    ens_test_probs = ensemble.ensemble_predict(test_images, low_mem=True)

    T = BaseClassifier.fit_temperature_from_probs(y_true_val, ens_val_probs)

    ece_before = BaseClassifier.expected_calibration_error(y_true_test, ens_test_probs)
    ece_after  = BaseClassifier.expected_calibration_error(
        y_true_test, BaseClassifier.scale(ens_test_probs, T)
    )

    print(f"T = {T:.4f}")
    print(f"ECE before: {ece_before:.4f}   after: {ece_after:.4f}")
    return T, ece_before, ece_after

if __name__ == "__main__":
    implement_calibration_on_ensemble()