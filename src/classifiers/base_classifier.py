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

from ..utils import constants

# matplotlib, sklearn, ml_insights, scipy, and count_image_classes (pandas) are
# imported lazily inside the training/evaluation methods that use them. The
# inference path (used by the deployed backend) needs none of them, so the slim
# production image can omit those heavy deps.


class BaseClassifier(ABC):
    def __init__(self, data_path=constants.DATA_PATH, img_size=constants.IMG_SIZE,
                 batch_size=constants.BATCH, base_seed=42, name=None):
        self.data_path = data_path
        self.img_size = img_size
        self.batch_size = batch_size
        self.base_seed = base_seed
        self.class_names = None
        self.num_classes = None
        self.name = name

    # ── abstract hooks ──────────────────────────────────────────────
    @abstractmethod
    def _load_base(self) -> keras.Model:
        """Return the pretrained backbone with include_top=False."""

    @abstractmethod
    def _preprocess(self, x):
        """Apply backbone-specific input preprocessing."""

    # ── dataset loading ─────────────────────────────────────────────
    def make_dataset_from_df(self, df, shuffle=False, seed=None):
        if self.class_names is None:
            raise ValueError("Call set_class_names(full_df) first.")

        idx = {c: i for i, c in enumerate(self.class_names)}   # <-- here
        paths = df["path"].values
        labels = df["label"].map(idx).values.astype("int32")

        ds = tf.data.Dataset.from_tensor_slices((paths, labels))
        if shuffle:
            ds = ds.shuffle(len(paths), seed=seed, reshuffle_each_iteration=True)

        def _load(path, label):
            img = tf.io.read_file(path)
            img = tf.io.decode_image(img, channels=3, expand_animations=False)
            img = tf.image.resize(img, self.img_size)
            return tf.cast(img, tf.float32), label

        ds = ds.map(_load, num_parallel_calls=tf.data.AUTOTUNE)
        return ds.batch(self.batch_size).prefetch(tf.data.AUTOTUNE)


    def set_class_names(self, full_df):
        self.class_names = sorted(full_df["label"].unique())
        self.num_classes = len(self.class_names)

    # def make_sub_datasets(self):
    #     self.train_ds = keras.utils.image_dataset_from_directory(
    #         os.path.join(self.data_path, "train"),
    #         image_size=self.img_size,
    #         batch_size=self.batch_size,
    #         shuffle=True,
    #         seed=self.base_seed,
    #     )
    #     self.val_ds = keras.utils.image_dataset_from_directory(
    #         os.path.join(self.data_path, "val"),
    #         image_size=self.img_size,
    #         batch_size=self.batch_size,
    #         shuffle=False,
    #     )
    #     self.test_ds = keras.utils.image_dataset_from_directory(
    #         os.path.join(self.data_path, "test"),
    #         image_size=self.img_size,
    #         batch_size=self.batch_size,
    #         shuffle=False,
    #     )

    #     self.class_names = self.train_ds.class_names
    #     self.num_classes = len(self.class_names)

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
    def train_one_run(self, train_df, val_df, test_df, seed, strategy, fold=None, epochs=50, keep_models=True, model_save_path=constants.TRAINED_MODELS_PATH, probs_save_path=constants.MODEL_PROBS_PATH, **build_kwargs):
        train_ds = self.make_dataset_from_df(train_df, shuffle=True, seed=seed)
        val_ds   = self.make_dataset_from_df(val_df)
        test_ds  = self.make_dataset_from_df(test_df)
        
        # A fold's train split can miss a rare class entirely. Weight only the
        # classes actually present; absent ones get a neutral 1.0 (their weight is
        # never applied, since no sample carries that label).
        counts = train_df["label"].value_counts().to_dict()
        total = sum(counts.values())
        k = sum(1 for name in self.class_names if counts.get(name, 0) > 0)
        class_weight = {
            i: max(total / (k * counts[name]), 1.0) if counts.get(name, 0) > 0 else 1.0
            for i, name in enumerate(self.class_names)
        }

        self._set_all_seeds(seed)
        model = self._build_model(**build_kwargs)
        callbacks = [
            keras.callbacks.EarlyStopping(monitor="val_loss", patience=10,
                                        restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5,
                                            patience=4, min_lr=1e-6),
        ]
        history = model.fit(train_ds, validation_data=val_ds, epochs=epochs,
                        verbose=0, class_weight=class_weight, callbacks=callbacks)

        probs = model.predict(test_ds, verbose=0)

        probs_save_name = f"preds_{self.name}_{strategy}_f{fold}_s{seed}.npy"
        full_probs_save_path = os.path.join(probs_save_path, probs_save_name)
        os.makedirs(probs_save_path, exist_ok=True)
        np.save(full_probs_save_path, probs)
        np.save(os.path.join(probs_save_path, f"preds_val_{self.name}_{strategy}_f{fold}_s{seed}.npy"),
        model.predict(val_ds, verbose=0))
        
        test_df.to_csv(os.path.join(probs_save_path, f"testset_f{fold}.csv"), index=False)

        if keep_models:
            model_save_name = f"{self.name}_{strategy}_f{fold}_s{seed}.keras"
            full_model_save_path = os.path.join(model_save_path, model_save_name)
            os.makedirs(model_save_path, exist_ok=True)
            model.save(full_model_save_path)

        return dict(arch=self.name, strategy=strategy, fold=fold, seed=seed,
                epochs_run=len(history.history["loss"]),
                n_train=len(train_df), n_test=len(test_df))

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
    
    def display_confusion_matrix(self, cm, title=None):
        if (self.class_names == None):
            raise ValueError("Ensure that class names are already defined.")
        display = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=self.class_names)
        fig, ax = plt.subplots(figsize=(10, 10))
        values_format = '.1f' if np.asarray(cm).dtype.kind == 'f' else 'd'
        display.plot(ax=ax, cmap=plt.cm.Blues, values_format=values_format)

        if title:
            ax.set_title(title)

        plt.tight_layout()
        plt.show()

    # ── rewritten: evaluate one seed from saved probabilities ───────
    def calibrate_and_evaluate(self, probs_dir, strategy, seed,
                               fold_assignments_path, n_folds=5,
                               n_bins=10, show_plots=False):
        import pandas as pd

        if self.class_names is None:
            raise ValueError("Call set_class_names(full_df) first.")

        fa = pd.read_csv(fold_assignments_path)
        true_parts, raw_parts, cal_parts, temperatures = [], [], [], []

        for k in range(n_folds):
            # validation: fit this fold's temperature, then discard
            val_probs = np.load(os.path.join(
                probs_dir, f"preds_val_{self.name}_{strategy}_f{k}_s{seed}.npy"))
            val_rows = fa[(fa["fold"] == k) & (fa["role"] == "val")]
            val_true = self._labels_to_int(val_rows["label"])
            if len(val_true) != len(val_probs):
                raise ValueError(f"fold {k}: {len(val_probs)} val probs vs "
                                 f"{len(val_true)} val labels")
            T = self.fit_temperature_from_probs(val_true, val_probs)
            temperatures.append(T)

            # test: apply this fold's temperature
            test_probs = np.load(os.path.join(
                probs_dir, f"preds_{self.name}_{strategy}_f{k}_s{seed}.npy"))
            test_rows = pd.read_csv(os.path.join(probs_dir, f"testset_f{k}.csv"))
            test_true = self._labels_to_int(test_rows["label"])
            if len(test_true) != len(test_probs):
                raise ValueError(f"fold {k}: {len(test_probs)} test probs vs "
                                 f"{len(test_true)} test labels")

            true_parts.append(test_true)
            raw_parts.append(test_probs)
            cal_parts.append(self.scale(test_probs, T))

        y_true = np.concatenate(true_parts)
        y_prob = np.concatenate(raw_parts)
        y_prob_cal = np.concatenate(cal_parts)
        y_pred = y_prob.argmax(1)

        # discrimination: unchanged by temperature scaling
        cm = self._confusion_matrix(y_true, y_pred)
        acc, prec, rec, f1, macro_f1 = self._metrics_from_confusion_matrix(cm)

        ece_before, bins_before = self.expected_calibration_error(y_true, y_prob, n_bins)
        ece_after, bins_after = self.expected_calibration_error(y_true, y_prob_cal, n_bins)

        if show_plots:
            self.display_confusion_matrix(cm, title=f"{self.name} {strategy} s{seed}")
            correct = (y_pred == y_true).astype(int)
            self.display_reliability_diagram(mli.plot_reliability_diagram(
                correct, y_prob.max(1), show_histogram=True))
            self.display_reliability_diagram(mli.plot_reliability_diagram(
                correct, y_prob_cal.max(1), show_histogram=True))

        return {
            "arch": self.name, "strategy": strategy, "seed": seed,
            "n_images": len(y_true), "temperatures": temperatures,
            "accuracy": acc, "macro_f1": macro_f1,
            "per_class_precision": prec, "per_class_recall": rec,
            "per_class_f1": f1, "confusion_matrix": cm,
            "ece_before": ece_before, "ece_after": ece_after,
            "bin_counts_before": bins_before, "bin_counts_after": bins_after,
            "brier_before": self.brier_score(y_true, y_prob),
            "brier_after": self.brier_score(y_true, y_prob_cal),
            "nll_before": self.negative_log_likelihood(y_true, y_prob),
            "nll_after": self.negative_log_likelihood(y_true, y_prob_cal),
            "y_true": y_true, "y_prob": y_prob, "y_prob_cal": y_prob_cal,
        }
    
    # ── calibration ──────────────────────────────────────────────────
    @staticmethod
    def _to_int(y):
        y = np.asarray(y)
        return y.argmax(1) if (y.ndim > 1 and y.shape[1] > 1) else y.ravel().astype(int)
    
    @staticmethod
    def scale(probs, T):
        z = np.log(np.clip(probs, 1e-12, 1.0)) / T
        z -= z.max(1, keepdims=True)
        e = np.exp(z)
        return e / e.sum(1, keepdims=True)
    
    @staticmethod
    def display_reliability_diagram(rd, title=None):
        import matplotlib.pyplot as plt

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
        from scipy.optimize import minimize_scalar

        y = BaseClassifier._to_int(y_true)
        def nll(T):
            p = BaseClassifier.scale(y_prob, T)
            true_p = p[np.arange(len(y)), y]
            return -np.mean(np.log(np.clip(true_p, 1e-12, 1.0)))
        
        return float(minimize_scalar(nll, bounds=(0.05, 10.0), method="bounded").x)
    
    @staticmethod
    def expected_calibration_error(y_true, y_prob, n_bins=10):
        y = BaseClassifier._to_int(y_true)
        conf = y_prob.max(1)
        correct = (y_prob.argmax(1) == y).astype(float)
        edges = np.linspace(0.0, 1.0, n_bins + 1)
        ece, n, counts = 0.0, len(conf), []
        for lo, hi in zip(edges[:-1], edges[1:]):
            m = (conf > lo) & (conf <= hi)
            counts.append(int(m.sum()))
            if m.sum():
                ece += (m.sum() / n) * abs(conf[m].mean() - correct[m].mean())
        return float(ece), counts

    @staticmethod
    def brier_score(y_true, y_prob):
        y = BaseClassifier._to_int(y_true)
        onehot = np.eye(y_prob.shape[1])[y]
        return float(((y_prob - onehot) ** 2).sum(1).mean())

    @staticmethod
    def negative_log_likelihood(y_true, y_prob):
        y = BaseClassifier._to_int(y_true)
        p = y_prob[np.arange(len(y)), y]
        return float(-np.log(np.clip(p, 1e-12, 1.0)).mean())

    # ── modified: 10 bins, and return per-bin counts ────────────────

    def _labels_to_int(self, labels):
        idx = {c: i for i, c in enumerate(self.class_names)}
        return np.array([idx[l] for l in labels], dtype=int)
    
    # ── extras ──────────────────────────────────────────────────
    def _check_model_exists(self, model=None, model_path=None):
        if model is None:
            if model_path is None:
                raise ValueError("Provide model or model_path.")
            model = keras.models.load_model(model_path)

        return model
