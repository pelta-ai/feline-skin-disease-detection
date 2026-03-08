"""
Abstract base class for transfer-learning classifiers.

Subclasses only need to implement two methods:
    _load_base()   return the pretrained backbone (include_top=False)
    _preprocess(x) apply backbone-specific pixel preprocessing
"""

import os
from abc import ABC, abstractmethod

import numpy as np
import tensorflow as tf
from tensorflow import keras
from keras import layers, models

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import utils.constants as constants


class BaseClassifier(ABC):
    def __init__(self, data_path=constants.DATA_IMAGES_PATH, img_size=constants.IMG_SIZE,
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
                      epochs=10, **build_kwargs):
        if self.train_ds is None or self.val_ds is None:
            raise ValueError("Ensure that train_ds and val_ds are already built.")

        self._set_all_seeds(seed)
        model = self._build_model(**build_kwargs)
        model.fit(self.train_ds, validation_data=self.val_ds, epochs=epochs, verbose=0)

        if save_name is not None:
            if not save_name.endswith(".keras"):
                save_name += ".keras"
            full_save_path = os.path.join(save_path, save_name)
            os.makedirs(save_path, exist_ok=True)
            model.save(full_save_path)

        return model

    # ── evaluation ──────────────────────────────────────────────────
    def _collect_y_true_y_pred_probs(self, model, dataset):
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

    def evaluate(self, model=None, model_path=None):
        if model is None:
            if model_path is None:
                raise ValueError("Provide model or model_path.")
            model = keras.models.load_model(model_path)

        if self.test_ds is None:
            raise ValueError("Ensure that test_ds is already built.")

        y_true, y_pred, y_prob = self._collect_y_true_y_pred_probs(model, self.test_ds)
        cm = self._confusion_matrix(y_true, y_pred)
        acc, prec, rec, f1, macro_f1 = self._metrics_from_confusion_matrix(cm)

        return {
            "accuracy": acc,
            "macro_f1": macro_f1,
            "per_class_precision": prec,
            "per_class_recall": rec,
            "per_class_f1": f1,
            "confusion_matrix": cm,
        }
