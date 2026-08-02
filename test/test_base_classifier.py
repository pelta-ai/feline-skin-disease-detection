"""
Unit tests for BaseClassifier.

Everything here runs on CPU in seconds: the abstract backbone hook is filled with
a small conv stack instead of a pretrained network, so _build_model and
train_one_run are exercised for real without downloading ImageNet weights.
"""

import os

# TensorFlow must be imported before pandas. Importing pandas first makes the
# native TF runtime fail to load on this Windows/Python 3.13 install:
#   ImportError: DLL load failed while importing _pywrap_tensorflow_internal
# base_classifier.py happens to get this right already (tf at module top, pandas
# only later via count_image_classes), so keep tf above pandas here too.
import tensorflow as tf
from tensorflow import keras
from keras import layers

import numpy as np
import pandas as pd
import pytest

from src.classifiers.base_classifier import BaseClassifier

TINY_IMG_SIZE = (32, 32)
CLASS_NAMES = ["dermatitis", "fungus", "ringworm"]


class TinyClassifier(BaseClassifier):
    """Concrete stand-in: a cheap backbone with enough layers to test unfreezing."""

    def _load_base(self):
        return keras.Sequential(
            [
                keras.Input(shape=self.img_size + (3,)),
                layers.Conv2D(4, 3, padding="same", name="block1"),
                layers.Conv2D(4, 3, padding="same", name="block2"),
                layers.Conv2D(4, 3, padding="same", name="block3"),
            ],
            name="tiny_backbone",
        )

    def _preprocess(self, x):
        return x / 255.0


@pytest.fixture
def classifier():
    clf = TinyClassifier(img_size=TINY_IMG_SIZE, batch_size=2, name="tiny")
    clf.class_names = list(CLASS_NAMES)
    clf.num_classes = len(CLASS_NAMES)

    return clf


class FakeModel:
    """Stands in for a Keras model in the predict path, recording what it saw."""

    def __init__(self, probs_per_batch):
        self.probs_per_batch = list(probs_per_batch)
        self.calls = 0

    def predict(self, x_batch, verbose=0):
        probs = self.probs_per_batch[self.calls]
        self.calls += 1

        return np.asarray(probs, dtype=np.float64)


class FakeBatch:
    """Mimics the tf tensor labels yielded by a tf.data pipeline."""

    def __init__(self, values):
        self.values = np.asarray(values)

    def numpy(self):
        return self.values


class RecordingModel:
    """Captures the kwargs train_one_run passes to fit, without training anything."""

    def __init__(self, num_classes):
        self.num_classes = num_classes
        self.fit_kwargs = None

    def fit(self, train_ds, **kwargs):
        self.fit_kwargs = kwargs

        class History:
            history = {"loss": [0.5]}

        return History()

    def predict(self, dataset, verbose=0):
        rows = sum(int(labels.shape[0]) for _, labels in dataset)

        return np.full((rows, self.num_classes), 1.0 / self.num_classes)

    def save(self, path):
        with open(path, "w") as handle:
            handle.write("stub")


def write_image(path, colour=(255, 0, 0), size=(40, 40)):
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, colour).save(path)

    return str(path)


def make_df(tmp_path, prefix, labels):
    """Builds a {path, label} frame backed by real image files on disk."""
    rows = []
    for i, label in enumerate(labels):
        path = write_image(tmp_path / prefix / f"{label}_{i}.png", colour=(i * 20 % 256, 80, 160))
        rows.append({"path": path, "label": label})

    return pd.DataFrame(rows)


# ── pure metric maths ────────────────────────────────────────────────


class TestMetricsFromConfusionMatrix:
    def test_perfect_predictions(self, classifier):
        cm = np.diag([5, 3, 2])

        acc, precision, recall, f1, macro_f1 = classifier._metrics_from_confusion_matrix(cm)

        assert acc == pytest.approx(1.0)
        assert precision == pytest.approx([1.0, 1.0, 1.0], abs=1e-9)
        assert recall == pytest.approx([1.0, 1.0, 1.0], abs=1e-9)
        assert f1 == pytest.approx([1.0, 1.0, 1.0], abs=1e-9)
        assert macro_f1 == pytest.approx(1.0)

    def test_hand_computed_two_class_case(self, classifier):
        # rows = true, cols = predicted
        #   class 0: 2 correct, 1 predicted as class 1
        #   class 1: 3 correct
        cm = np.array([[2, 1], [0, 3]])

        acc, precision, recall, f1, macro_f1 = classifier._metrics_from_confusion_matrix(cm)

        assert acc == pytest.approx(5 / 6)
        assert precision == pytest.approx([1.0, 0.75], abs=1e-6)
        assert recall == pytest.approx([2 / 3, 1.0], abs=1e-6)
        assert f1 == pytest.approx([0.8, 6 / 7], abs=1e-6)
        assert macro_f1 == pytest.approx(np.mean([0.8, 6 / 7]), abs=1e-6)

    def test_macro_f1_is_the_unweighted_mean(self, classifier):
        cm = np.array([[10, 2, 0], [1, 4, 1], [0, 0, 1]])

        _, _, _, f1, macro_f1 = classifier._metrics_from_confusion_matrix(cm)

        assert macro_f1 == pytest.approx(float(np.mean(f1)))

    def test_absent_class_does_not_produce_nan(self, classifier):
        """A class with no true samples and no predictions divides 0/0 - the eps
        guard has to keep it finite, or macro_f1 silently becomes NaN."""
        cm = np.array([[4, 0, 0], [0, 3, 0], [0, 0, 0]])

        acc, precision, recall, f1, macro_f1 = classifier._metrics_from_confusion_matrix(cm)

        assert np.all(np.isfinite(precision))
        assert np.all(np.isfinite(recall))
        assert np.all(np.isfinite(f1))
        assert np.isfinite(macro_f1)
        assert f1[2] == pytest.approx(0.0)
        assert acc == pytest.approx(1.0)

    def test_all_predictions_wrong(self, classifier):
        cm = np.array([[0, 3], [2, 0]])

        acc, _, _, f1, macro_f1 = classifier._metrics_from_confusion_matrix(cm)

        assert acc == pytest.approx(0.0)
        assert f1 == pytest.approx([0.0, 0.0], abs=1e-9)
        assert macro_f1 == pytest.approx(0.0)


class TestConfusionMatrix:
    def test_counts_and_shape(self, classifier):
        y_true = np.array([0, 0, 1, 2, 2, 2])
        y_pred = np.array([0, 1, 1, 2, 2, 0])

        cm = classifier._confusion_matrix(y_true, y_pred)

        assert cm.shape == (3, 3)
        assert cm.sum() == len(y_true)
        assert cm[0, 0] == 1 and cm[0, 1] == 1
        assert cm[1, 1] == 1
        assert cm[2, 2] == 2 and cm[2, 0] == 1

    def test_uses_num_classes_even_when_a_class_is_unseen(self, classifier):
        cm = classifier._confusion_matrix(np.array([0, 0]), np.array([0, 0]))

        assert cm.shape == (3, 3)


# ── label coercion ───────────────────────────────────────────────────


class TestToInt:
    def test_one_hot_becomes_indices(self):
        one_hot = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]])

        assert BaseClassifier._to_int(one_hot).tolist() == [0, 2, 1]

    def test_flat_labels_pass_through(self):
        assert BaseClassifier._to_int(np.array([2, 0, 1])).tolist() == [2, 0, 1]

    def test_column_vector_is_flattened(self):
        assert BaseClassifier._to_int(np.array([[2], [0], [1]])).tolist() == [2, 0, 1]

    def test_float_labels_are_cast_to_int(self):
        result = BaseClassifier._to_int(np.array([2.0, 0.0, 1.0]))

        assert result.dtype.kind == "i"
        assert result.tolist() == [2, 0, 1]

    def test_accepts_a_plain_list(self):
        assert BaseClassifier._to_int([1, 2]).tolist() == [1, 2]


# ── temperature scaling ──────────────────────────────────────────────


class TestScale:
    def test_temperature_one_is_a_no_op(self):
        probs = np.array([[0.7, 0.2, 0.1], [0.1, 0.8, 0.1]])

        assert BaseClassifier.scale(probs, 1.0) == pytest.approx(probs, abs=1e-9)

    @pytest.mark.parametrize("temperature", [0.1, 0.5, 1.0, 2.0, 9.0])
    def test_rows_remain_a_distribution(self, temperature):
        probs = np.array([[0.6, 0.3, 0.1], [0.2, 0.2, 0.6]])

        scaled = BaseClassifier.scale(probs, temperature)

        assert scaled.sum(axis=1) == pytest.approx([1.0, 1.0])
        assert np.all(scaled >= 0.0)

    def test_high_temperature_softens_and_low_temperature_sharpens(self):
        probs = np.array([[0.7, 0.2, 0.1]])

        softened = BaseClassifier.scale(probs, 5.0).max()
        sharpened = BaseClassifier.scale(probs, 0.2).max()

        assert softened < probs.max() < sharpened

    def test_ranking_is_preserved(self):
        probs = np.array([[0.5, 0.3, 0.2], [0.1, 0.2, 0.7]])

        for temperature in (0.3, 1.0, 4.0):
            scaled = BaseClassifier.scale(probs, temperature)
            assert scaled.argmax(axis=1).tolist() == probs.argmax(axis=1).tolist()

    def test_zero_probabilities_do_not_produce_nan(self):
        """log(0) would be -inf without the clip."""
        probs = np.array([[1.0, 0.0, 0.0]])

        scaled = BaseClassifier.scale(probs, 2.0)

        assert np.all(np.isfinite(scaled))
        assert scaled.sum() == pytest.approx(1.0)


class TestFitTemperatureFromProbs:
    def test_returns_a_float_inside_the_search_bounds(self):
        rng = np.random.default_rng(0)
        probs = rng.dirichlet([2, 2, 2], size=50)
        y_true = probs.argmax(axis=1)

        temperature = BaseClassifier.fit_temperature_from_probs(y_true, probs)

        assert isinstance(temperature, float)
        assert 0.05 <= temperature <= 10.0

    def test_overconfident_model_gets_temperature_above_one(self):
        """Half the confident predictions are wrong, so the fit should soften them."""
        probs = np.array([[0.99, 0.01]] * 10 + [[0.01, 0.99]] * 10)
        y_true = np.array([0] * 5 + [1] * 5 + [1] * 5 + [0] * 5)

        assert BaseClassifier.fit_temperature_from_probs(y_true, probs) > 1.0

    def test_accepts_one_hot_labels(self):
        probs = np.array([[0.8, 0.2], [0.3, 0.7]])

        flat = BaseClassifier.fit_temperature_from_probs(np.array([0, 1]), probs)
        one_hot = BaseClassifier.fit_temperature_from_probs(np.array([[1, 0], [0, 1]]), probs)

        assert flat == pytest.approx(one_hot)

    def test_fitted_temperature_beats_no_scaling(self):
        probs = np.array([[0.97, 0.03]] * 12 + [[0.03, 0.97]] * 12)
        y_true = np.array([0] * 8 + [1] * 4 + [1] * 8 + [0] * 4)

        temperature = BaseClassifier.fit_temperature_from_probs(y_true, probs)

        def nll(t):
            scaled = BaseClassifier.scale(probs, t)
            return -np.mean(np.log(scaled[np.arange(len(y_true)), y_true]))

        assert nll(temperature) <= nll(1.0)


class TestExpectedCalibrationError:
    def test_confident_and_always_right_is_perfectly_calibrated(self):
        probs = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]])

        assert BaseClassifier.expected_calibration_error(np.array([0, 1, 0]), probs) == pytest.approx(0.0)

    def test_confident_and_always_wrong_is_maximally_miscalibrated(self):
        probs = np.array([[1.0, 0.0], [1.0, 0.0]])

        assert BaseClassifier.expected_calibration_error(np.array([1, 1]), probs) == pytest.approx(1.0)

    def test_hand_computed_single_bin(self):
        # Four samples all at confidence 0.9 -> one bin; half correct.
        # ECE = 1.0 * |0.9 - 0.5| = 0.4
        probs = np.array([[0.9, 0.1]] * 4)

        assert BaseClassifier.expected_calibration_error(np.array([0, 0, 1, 1]), probs) == pytest.approx(0.4)

    def test_stays_within_zero_and_one(self):
        rng = np.random.default_rng(1)
        probs = rng.dirichlet([1, 1, 1], size=200)
        y_true = rng.integers(0, 3, size=200)

        assert 0.0 <= BaseClassifier.expected_calibration_error(y_true, probs) <= 1.0

    def test_accepts_one_hot_labels(self):
        probs = np.array([[0.9, 0.1], [0.2, 0.8]])

        flat = BaseClassifier.expected_calibration_error(np.array([0, 1]), probs)
        one_hot = BaseClassifier.expected_calibration_error(np.array([[1, 0], [0, 1]]), probs)

        assert flat == pytest.approx(one_hot)


# ── prediction collection ────────────────────────────────────────────


class TestCollectYTrueYPredProbs:
    def test_concatenates_batches_in_order(self):
        model = FakeModel([[[0.9, 0.1], [0.2, 0.8]], [[0.4, 0.6]]])
        dataset = [(object(), FakeBatch([0, 1])), (object(), FakeBatch([1]))]

        y_true, y_pred, y_prob = BaseClassifier.collect_y_true_y_pred_probs(model, dataset)

        assert y_true.tolist() == [0, 1, 1]
        assert y_pred.tolist() == [0, 1, 1]
        assert y_prob.shape == (3, 2)
        assert model.calls == 2

    def test_y_pred_is_the_argmax_of_the_probabilities(self):
        model = FakeModel([[[0.1, 0.7, 0.2], [0.5, 0.3, 0.2]]])
        dataset = [(object(), FakeBatch([2, 2]))]

        y_true, y_pred, _ = BaseClassifier.collect_y_true_y_pred_probs(model, dataset)

        assert y_pred.tolist() == [1, 0]
        assert y_true.tolist() == [2, 2]


# ── dataset construction ─────────────────────────────────────────────


class TestSetClassNames:
    def test_names_are_sorted_and_deduplicated(self, classifier):
        df = pd.DataFrame({"label": ["ringworm", "fungus", "ringworm", "dermatitis"]})

        classifier.set_class_names(df)

        assert classifier.class_names == ["dermatitis", "fungus", "ringworm"]
        assert classifier.num_classes == 3


class TestMakeDatasetFromDf:
    def test_requires_class_names_first(self, classifier):
        classifier.class_names = None

        with pytest.raises(ValueError, match="set_class_names"):
            classifier.make_dataset_from_df(pd.DataFrame({"path": [], "label": []}))

    def test_produces_batches_of_the_configured_shape(self, classifier, tmp_path):
        df = make_df(tmp_path, "ds", ["fungus", "dermatitis", "ringworm", "fungus"])

        images, labels = next(iter(classifier.make_dataset_from_df(df)))

        assert images.shape == (2, 32, 32, 3)  # batch_size=2
        assert images.dtype == tf.float32
        assert labels.shape == (2,)

    def test_labels_map_through_sorted_class_name_order(self, classifier, tmp_path):
        df = make_df(tmp_path, "ds", ["ringworm", "dermatitis", "fungus"])
        classifier.batch_size = 3

        _, labels = next(iter(classifier.make_dataset_from_df(df)))

        # class_names == ["dermatitis", "fungus", "ringworm"] -> indices 2, 0, 1
        assert labels.numpy().tolist() == [2, 0, 1]

    def test_every_row_is_emitted_exactly_once(self, classifier, tmp_path):
        df = make_df(tmp_path, "ds", ["fungus"] * 5)

        total = sum(int(labels.shape[0]) for _, labels in classifier.make_dataset_from_df(df))

        assert total == 5

    def test_images_are_resized_to_img_size(self, classifier, tmp_path):
        path = write_image(tmp_path / "big.png", size=(200, 150))
        df = pd.DataFrame([{"path": path, "label": "fungus"}])

        images, _ = next(iter(classifier.make_dataset_from_df(df)))

        assert tuple(images.shape[1:3]) == TINY_IMG_SIZE

    def test_shuffle_is_reproducible_for_a_fixed_seed(self, classifier, tmp_path):
        df = make_df(tmp_path, "ds", ["fungus", "dermatitis", "ringworm"] * 2)
        classifier.batch_size = 6

        def first_batch_labels():
            _, labels = next(iter(classifier.make_dataset_from_df(df, shuffle=True, seed=3)))
            return labels.numpy().tolist()

        assert first_batch_labels() == first_batch_labels()


# ── model building ───────────────────────────────────────────────────


class TestBuildModel:
    def test_input_and_output_shapes(self, classifier):
        model = classifier._build_model()

        assert tuple(model.input_shape[1:]) == TINY_IMG_SIZE + (3,)
        assert model.output_shape[-1] == classifier.num_classes

    def test_outputs_are_a_probability_distribution(self, classifier):
        model = classifier._build_model()
        batch = np.random.default_rng(0).uniform(0, 255, size=(2,) + TINY_IMG_SIZE + (3,))

        probs = model.predict(batch, verbose=0)

        assert probs.shape == (2, 3)
        assert probs.sum(axis=1) == pytest.approx([1.0, 1.0], abs=1e-5)
        assert np.all(probs >= 0.0)

    def test_backbone_is_frozen_by_default(self, classifier):
        assert classifier._build_model().get_layer("tiny_backbone").trainable is False

    def test_trainable_backbone_unfreezes_everything(self, classifier):
        base = classifier._build_model(trainable_backbone=True).get_layer("tiny_backbone")

        assert base.trainable is True
        assert all(layer.trainable for layer in base.layers)

    def test_unfreeze_last_n_layers_leaves_earlier_layers_frozen(self, classifier):
        model = classifier._build_model(trainable_backbone=True, unfreeze_last_n_layers=1)
        base = model.get_layer("tiny_backbone")

        assert [layer.trainable for layer in base.layers] == [False, False, True]

    def test_unfreeze_is_ignored_when_backbone_stays_frozen(self, classifier):
        model = classifier._build_model(trainable_backbone=False, unfreeze_last_n_layers=2)

        assert model.get_layer("tiny_backbone").trainable is False

    def test_learning_rate_reaches_the_optimizer(self, classifier):
        model = classifier._build_model(learning_rate=5e-4)

        assert model.optimizer is not None
        assert float(model.optimizer.learning_rate.numpy()) == pytest.approx(5e-4)

    def test_same_seed_gives_identical_initial_weights(self, classifier):
        classifier._set_all_seeds(7)
        first = classifier._build_model()
        classifier._set_all_seeds(7)
        second = classifier._build_model()

        for a, b in zip(first.get_weights(), second.get_weights()):
            assert np.allclose(a, b)


# ── training orchestration ───────────────────────────────────────────


class TestTrainOneRun:
    @pytest.fixture
    def splits(self, tmp_path):
        return (
            make_df(tmp_path, "train", CLASS_NAMES * 2),
            make_df(tmp_path, "val", list(CLASS_NAMES)),
            make_df(tmp_path, "test", list(CLASS_NAMES)),
        )

    def test_returns_a_run_summary(self, classifier, splits, tmp_path):
        train_df, val_df, test_df = splits

        result = classifier.train_one_run(
            train_df, val_df, test_df, seed=1, strategy="frozen", fold=0, epochs=1,
            keep_models=False, model_save_path=str(tmp_path / "models"),
            probs_save_path=str(tmp_path / "probs"),
        )

        assert result == {
            "arch": "tiny", "strategy": "frozen", "fold": 0, "seed": 1,
            "epochs_run": 1, "n_train": 6, "n_test": 3,
        }

    def test_saves_test_and_val_probability_arrays(self, classifier, splits, tmp_path):
        train_df, val_df, test_df = splits
        probs_dir = tmp_path / "probs"

        classifier.train_one_run(
            train_df, val_df, test_df, seed=2, strategy="frozen", fold=1, epochs=1,
            keep_models=False, model_save_path=str(tmp_path / "models"),
            probs_save_path=str(probs_dir),
        )

        test_probs = np.load(probs_dir / "preds_tiny_frozen_f1_s2.npy")
        val_probs = np.load(probs_dir / "preds_val_tiny_frozen_f1_s2.npy")

        assert test_probs.shape == (3, 3)
        assert val_probs.shape == (3, 3)
        assert test_probs.sum(axis=1) == pytest.approx([1.0] * 3, abs=1e-5)

    def test_keep_models_controls_whether_the_model_is_written(self, classifier, splits, tmp_path):
        train_df, val_df, test_df = splits
        models_dir = tmp_path / "models"

        classifier.train_one_run(
            train_df, val_df, test_df, seed=3, strategy="frozen", fold=None, epochs=1,
            keep_models=True, model_save_path=str(models_dir),
            probs_save_path=str(tmp_path / "probs"),
        )

        assert (models_dir / "tiny_frozen_fNone_s3.keras").exists()

    def test_no_model_written_when_keep_models_is_false(self, classifier, splits, tmp_path):
        train_df, val_df, test_df = splits
        models_dir = tmp_path / "models"

        classifier.train_one_run(
            train_df, val_df, test_df, seed=4, strategy="frozen", fold=0, epochs=1,
            keep_models=False, model_save_path=str(models_dir),
            probs_save_path=str(tmp_path / "probs"),
        )

        assert not models_dir.exists()

    def test_class_weights_balance_present_classes_and_neutralise_absent_ones(
        self, classifier, tmp_path, monkeypatch
    ):
        """dermatitis x1, fungus x5, ringworm absent.
        total=6, present k=2 -> dermatitis 6/(2*1)=3.0, fungus max(6/(2*5), 1)=1.0,
        ringworm neutral 1.0 because no sample can carry its label."""
        train_df = make_df(tmp_path, "train", ["dermatitis"] + ["fungus"] * 5)
        val_df = make_df(tmp_path, "val", list(CLASS_NAMES))
        test_df = make_df(tmp_path, "test", list(CLASS_NAMES))

        recorder = RecordingModel(classifier.num_classes)
        monkeypatch.setattr(classifier, "_build_model", lambda **kwargs: recorder)

        classifier.train_one_run(
            train_df, val_df, test_df, seed=8, strategy="frozen", fold=0, epochs=1,
            keep_models=False, model_save_path=str(tmp_path / "models"),
            probs_save_path=str(tmp_path / "probs"),
        )

        assert recorder.fit_kwargs["class_weight"] == pytest.approx({0: 3.0, 1: 1.0, 2: 1.0})

    def test_survives_a_class_missing_from_the_train_split(self, classifier, tmp_path):
        """A fold can drop a rare class from train entirely. Looking that class up
        in the value_counts dict used to raise KeyError before training started."""
        train_df = make_df(tmp_path, "train", ["dermatitis", "dermatitis", "fungus", "fungus"])
        val_df = make_df(tmp_path, "val", list(CLASS_NAMES))
        test_df = make_df(tmp_path, "test", list(CLASS_NAMES))

        result = classifier.train_one_run(
            train_df, val_df, test_df, seed=6, strategy="frozen", fold=0, epochs=1,
            keep_models=False, model_save_path=str(tmp_path / "models"),
            probs_save_path=str(tmp_path / "probs"),
        )

        assert result["n_train"] == 4

    def test_survives_a_single_class_train_split(self, classifier, tmp_path):
        """Two of three classes absent - k must not collapse to a divide-by-zero."""
        train_df = make_df(tmp_path, "train", ["fungus", "fungus", "fungus"])
        val_df = make_df(tmp_path, "val", list(CLASS_NAMES))
        test_df = make_df(tmp_path, "test", list(CLASS_NAMES))

        result = classifier.train_one_run(
            train_df, val_df, test_df, seed=7, strategy="frozen", fold=0, epochs=1,
            keep_models=False, model_save_path=str(tmp_path / "models"),
            probs_save_path=str(tmp_path / "probs"),
        )

        assert result["n_train"] == 3

    def test_creates_output_directories(self, classifier, splits, tmp_path):
        train_df, val_df, test_df = splits
        probs_dir = tmp_path / "deep" / "probs"

        classifier.train_one_run(
            train_df, val_df, test_df, seed=5, strategy="frozen", fold=0, epochs=1,
            keep_models=False, model_save_path=str(tmp_path / "models"),
            probs_save_path=str(probs_dir),
        )

        assert probs_dir.is_dir()


# ── guard clauses ────────────────────────────────────────────────────


class TestCheckModelExists:
    def test_raises_when_neither_model_nor_path_given(self, classifier):
        with pytest.raises(ValueError, match="Provide model or model_path"):
            classifier._check_model_exists()

    def test_returns_the_model_it_was_handed(self, classifier):
        model = FakeModel([])

        assert classifier._check_model_exists(model=model) is model

    def test_loads_from_disk_when_only_a_path_is_given(self, classifier, tmp_path):
        path = tmp_path / "tiny.keras"
        classifier._build_model().save(path)

        loaded = classifier._check_model_exists(model_path=str(path))

        assert loaded.output_shape[-1] == classifier.num_classes


class TestFitTemperature:
    def test_requires_a_validation_dataset(self, classifier):
        with pytest.raises(ValueError, match="already built"):
            classifier.fit_temperature(None, model=FakeModel([]))

    def test_requires_a_model_or_path(self, classifier):
        with pytest.raises(ValueError, match="Provide model or model_path"):
            classifier.fit_temperature([])

    def test_fits_from_a_validation_dataset(self, classifier):
        val_ds = [(object(), FakeBatch([0, 1]))]
        model = FakeModel([[[0.9, 0.05, 0.05], [0.1, 0.8, 0.1]]])

        temperature = classifier.fit_temperature(val_ds, model=model)

        assert 0.05 <= temperature <= 10.0


# ── end-to-end calibration on a fake model ───────────────────────────


class TestCalibrateAndEvaluate:
    def test_returns_the_full_metric_bundle(self, classifier):
        test_ds = [(object(), FakeBatch([0, 1]))]
        val_ds = [(object(), FakeBatch([0, 1]))]
        model = FakeModel([
            [[0.8, 0.1, 0.1], [0.2, 0.7, 0.1]],   # test pass
            [[0.9, 0.05, 0.05], [0.1, 0.8, 0.1]],  # val pass, for temperature
        ])

        results = classifier.calibrate_and_evaluate(test_ds, val_ds, model=model)

        assert set(results) == {
            "accuracy", "macro_f1", "per_class_precision", "per_class_recall",
            "per_class_f1", "confusion_matrix", "temperature",
            "expected_calibration_error_before_calibration",
            "expected_calibration_error_after_calibration",
            "y_true", "y_prob", "y_prob_cal",
        }
        assert results["accuracy"] == pytest.approx(1.0)
        assert results["confusion_matrix"].shape == (3, 3)
        assert results["y_prob_cal"].sum(axis=1) == pytest.approx([1.0, 1.0])
        assert 0.05 <= results["temperature"] <= 10.0

    def test_calibrated_probabilities_keep_the_same_predictions(self, classifier):
        test_ds = [(object(), FakeBatch([0, 1]))]
        val_ds = [(object(), FakeBatch([0, 1]))]
        model = FakeModel([
            [[0.8, 0.1, 0.1], [0.2, 0.7, 0.1]],
            [[0.9, 0.05, 0.05], [0.1, 0.8, 0.1]],
        ])

        results = classifier.calibrate_and_evaluate(test_ds, val_ds, model=model)

        assert (results["y_prob"].argmax(1) == results["y_prob_cal"].argmax(1)).all()

    def test_requires_a_model_or_path(self, classifier):
        with pytest.raises(ValueError, match="Provide model or model_path"):
            classifier.calibrate_and_evaluate([], [])


class TestDisplayHelpers:
    def test_confusion_matrix_display_needs_class_names(self, classifier):
        classifier.class_names = None

        with pytest.raises(ValueError, match="class names"):
            classifier.display_confusion_matrix(np.array([[1, 0], [0, 1]]))

    def test_confusion_matrix_display_accepts_integer_counts(self, classifier):
        import matplotlib.pyplot as plt

        classifier.display_confusion_matrix(np.diag([2, 3, 1]), title="counts")
        plt.close("all")

    def test_confusion_matrix_display_accepts_float_rates(self, classifier):
        import matplotlib.pyplot as plt

        classifier.display_confusion_matrix(np.eye(3) * 0.5)
        plt.close("all")

    def test_reliability_diagram_ignores_none(self):
        assert BaseClassifier.display_reliability_diagram(None) is None
