"""
Abstract base class for transfer-learning classifiers.

Subclasses only need to implement two methods:
    _load_base()   return the pretrained backbone (include_top=False)
    _preprocess(x) apply backbone-specific pixel preprocessing
"""

import os
from abc import ABC, abstractmethod

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tensorflow import keras
from keras import layers, models
from sklearn.metrics import ConfusionMatrixDisplay
import ml_insights as mli
from scipy.optimize import minimize_scalar

from ..utils import constants
from ..data_manipulation.count_image_classes import count_classes_from_folder_structure


class BaseClassifier(ABC):
    def __init__(self, data_path=constants.DATA_PATH, img_size=constants.IMG_SIZE,
                 batch_size=constants.BATCH, base_seed=42):
        self.data_path = data_path
        self.img_size = img_size
        self.batch_size = batch_size
        self.base_seed = base_seed
        self.class_names = None
        self.num_classes = None
        self.train_ds = None
        self.val_ds = None
        self.test_ds = None

    # ── abstract hooks ──────────────────────────────────────────────
    @abstractmethod
    def _load_base(self) -> keras.Model:
        """Return the pretrained backbone with include_top=False."""

    @abstractmethod
    def _preprocess(self, x):
        """Apply backbone-specific input preprocessing."""

    # ── dataset loading ─────────────────────────────────────────────
    def make_sub_datasets(self):
        self.train_ds = keras.utils.image_dataset_from_directory(
            os.path.join(self.data_path, "train"),
            image_size=self.img_size,
            batch_size=self.batch_size,
            shuffle=True,
            seed=self.base_seed,
        )
        self.val_ds = keras.utils.image_dataset_from_directory(
            os.path.join(self.data_path, "val"),
            image_size=self.img_size,
            batch_size=self.batch_size,
            shuffle=False,
        )
        self.test_ds = keras.utils.image_dataset_from_directory(
            os.path.join(self.data_path, "test"),
            image_size=self.img_size,
            batch_size=self.batch_size,
            shuffle=False,
        )

        self.class_names = self.train_ds.class_names
        self.num_classes = len(self.class_names)

    # ── model building ──────────────────────────────────────────────
    def _set_all_seeds(self, seed: int):
        keras.utils.set_random_seed(seed)

    def _build_model(self, learning_rate=1e-3, trainable_backbone=False, unfreeze_last_n_layers=0):
        data_aug = keras.Sequential([
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.05),
            layers.RandomContrast(0.1),
        ])

        base = self._load_base()
        base.trainable = trainable_backbone

        if trainable_backbone and unfreeze_last_n_layers > 0:
            for layer in base.layers[:-unfreeze_last_n_layers]:
                layer.trainable = False

        inputs = layers.Input(shape=self.img_size + (3,))
        x = data_aug(inputs)
        x = self._preprocess(x)
        x = base(x, training=trainable_backbone)
        x = layers.GlobalAveragePooling2D()(x)
        x = layers.Dense(256, activation="relu")(x)
        x = layers.Dropout(0.4)(x)
        outputs = layers.Dense(self.num_classes, activation="softmax")(x)

        model = models.Model(inputs, outputs)
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        return model

    # ── training ────────────────────────────────────────────────────
    def train_one_run(self, seed, save_name, save_path=constants.TRAINED_MODELS_PATH,
                      epochs=50, **build_kwargs):
        if self.train_ds is None or self.val_ds is None:
            raise ValueError("Ensure that train_ds and val_ds are already built.")
        
        counts = count_classes_from_folder_structure()
        total, k = sum(counts.values()), len(counts)
        class_weight = {i: max(total/(k*counts[name]), 1.0)
                for i, name in enumerate(self.class_names)}

        self._set_all_seeds(seed)
        model = self._build_model(**build_kwargs)
        callbacks = [
            keras.callbacks.EarlyStopping(monitor="val_loss", patience=10,
                                        restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5,
                                            patience=4, min_lr=1e-6),
        ]
        history = model.fit(self.train_ds, validation_data=self.val_ds, epochs=epochs, verbose=0, class_weight=class_weight, callbacks=callbacks)

        if save_name is not None:
            if not save_name.endswith(".keras"):
                save_name += ".keras"
            full_save_path = os.path.join(save_path, save_name)
            os.makedirs(save_path, exist_ok=True)
            model.save(full_save_path)

        return model

    # ── evaluation ──────────────────────────────────────────────────
    @staticmethod
    def collect_y_true_y_pred_probs(model, dataset):
        y_true_list, y_prob_list = [], []
        for x_batch, y_batch in dataset:
            probs = model.predict(x_batch, verbose=0)
            y_true_list.append(y_batch.numpy())
            y_prob_list.append(probs)

        y_true = np.concatenate(y_true_list, axis=0)
        y_prob = np.concatenate(y_prob_list, axis=0)
        y_pred = np.argmax(y_prob, axis=1)
        return y_true, y_pred, y_prob

    def _confusion_matrix(self, y_true, y_pred):
        return tf.math.confusion_matrix(y_true, y_pred, num_classes=self.num_classes).numpy()

    def _metrics_from_confusion_matrix(self, confusion_matrix, eps=1e-12):
        true_positives = np.diag(confusion_matrix).astype(np.float64)
        false_positives = np.sum(confusion_matrix, axis=0) - true_positives
        false_negatives = np.sum(confusion_matrix, axis=1) - true_positives

        precision = true_positives / (true_positives + false_positives + eps)
        recall = true_positives / (true_positives + false_negatives + eps)
        f1 = 2 * precision * recall / (precision + recall + eps)

        acc = float(true_positives.sum() / (confusion_matrix.sum() + eps))
        macro_f1 = float(np.mean(f1))
        return acc, precision, recall, f1, macro_f1
    
    @staticmethod
    def display_confusion_matrix(cm, class_names, title=None):
        display = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
        fig, ax = plt.subplots(figsize=(10, 10))
        values_format = '.1f' if np.asarray(cm).dtype.kind == 'f' else 'd'
        display.plot(ax=ax, cmap=plt.cm.Blues, values_format=values_format)

        if title:
            ax.set_title(title)

        plt.tight_layout()
        plt.show()

    def calibrate_and_evaluate(self, model=None, model_path=None, show_plots=False):
        model = self._check_model_exists(model=model, model_path=model_path)

        if self.test_ds is None:
            raise ValueError("Ensure that test_ds is already built.")

        #y_true is the true label, y_pred is the predicted label, y_prob is the predicted probabilities
        y_true, y_pred, y_prob = self.collect_y_true_y_pred_probs(model, self.test_ds)
        cm = self._confusion_matrix(y_true, y_pred)
        acc, prec, rec, f1, macro_f1 = self._metrics_from_confusion_matrix(cm)

        correct = (y_pred == y_true).astype(int)

        ece_before_calib = self.expected_calibration_error(y_true=y_true, y_prob=y_prob)

        T = self.fit_temperature(model=model)
        y_prob_cal = self._scale(y_prob, T)

        ece_after_calib = self.expected_calibration_error(y_true=y_true, y_prob=y_prob_cal)

        if show_plots == True:
            BaseClassifier.display_confusion_matrix(y_true=y_true, y_pred=y_pred)
            rd_before_calib = mli.plot_reliability_diagram(correct, y_prob.max(1), show_histogram=True)
            rd_after_calib = mli.plot_reliability_diagram(correct, y_prob_cal.max(1), show_histogram=True)
            BaseClassifier.display_reliability_diagram(rd_before_calib)
            BaseClassifier.display_reliability_diagram(rd_after_calib)

        return {
            "accuracy": acc,
            "macro_f1": macro_f1,
            "per_class_precision": prec,
            "per_class_recall": rec,
            "per_class_f1": f1,
            "confusion_matrix": cm,
            "expected_calibration_error_before_calibration": ece_before_calib,
            "expected_calibration_error_after_calibration": ece_after_calib,
            "y_true": y_true,
            "y_prob": y_prob,
            "y_prob_cal": y_prob_cal,
            "temperature": T,
        }
    
    # ── calibration ──────────────────────────────────────────────────
    @staticmethod
    def _to_int(y):
        y = np.asarray(y)
        return y.argmax(1) if (y.ndim > 1 and y.shape[1] > 1) else y.ravel().astype(int)
    
    @staticmethod
    def _scale(probs, T):
        z = np.log(np.clip(probs, 1e-12, 1.0)) / T
        z -= z.max(1, keepdims=True)
        e = np.exp(z)
        return e / e.sum(1, keepdims=True)
    
    @staticmethod
    def display_reliability_diagram(rd, title=None):
        if rd is None:
            return
        
        fig = rd if hasattr(rd, "number") else plt.gcf()

        if title:
            fig.suptitle(title)
            fig.tight_layout()

        plt.figure(fig.number)
        plt.show()

    @staticmethod
    def fit_temperature_from_probs(y_true, y_prob):
        y = BaseClassifier._to_int(y_true)
        def nll(T):
            p = BaseClassifier._scale(y_prob, T)
            true_p = p[np.arange(len(y)), y]
            return -np.mean(np.log(np.clip(true_p, 1e-12, 1.0)))
        
        return float(minimize_scalar(nll, bounds=(0.05, 10.0), method="bounded").x)
    
    @staticmethod
    def expected_calibration_error(y_true, y_prob, n_bins=15):
        y = BaseClassifier._to_int(y_true)
        conf = y_prob.max(1)
        correct = (y_prob.argmax(1) == y).astype(float)
        edges = np.linspace(0.0, 1.0, n_bins + 1)
        ece, n = 0.0, len(conf)

        for lo, hi in zip(edges[:-1], edges[1:]):
            m = (conf > lo) & (conf <= hi)
            if m.sum():
                ece += (m.sum() / n) * abs(conf[m].mean() - correct[m].mean())

        return ece

    def fit_temperature(self, model=None, model_path=None):
        model = self._check_model_exists(model=model, model_path=model_path)

        if self.val_ds is None:
            raise ValueError("Ensure that test_ds is already built.")
        
        y_true_val, y_pred, y_prob_val = self.collect_y_true_y_pred_probs(model, self.val_ds)
        return self.fit_temperature_from_probs(y_true_val, y_prob_val)
    
    # ── extras ──────────────────────────────────────────────────
    def _check_model_exists(self, model=None, model_path=None):
        if model is None:
            if model_path is None:
                raise ValueError("Provide model or model_path.")
            model = keras.models.load_model(model_path)

        return model
