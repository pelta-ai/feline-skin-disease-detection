"""ResNet18 backbone (via TensorFlow Hub) for the shared classifier head."""

import tensorflow_hub as hub
from tensorflow import keras
from keras import layers, models

from .base_classifier import BaseClassifier


class ResNet18Classifier(BaseClassifier):
    _HUB_URL = "https://tfhub.dev/google/imagenet/resnet_v2_18/feature_vector/4"

    def _load_base(self):
        return hub.KerasLayer(
            self._HUB_URL,
            input_shape=self.img_size + (3,),
            trainable=False,
        )

    def _preprocess(self, x):
        return x / 255.0

    def _build_model(self, learning_rate=1e-3, trainable_backbone=False, **kwargs):
        data_aug = keras.Sequential([
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.05),
            layers.RandomContrast(0.1),
        ])

        base = self._load_base()
        base.trainable = trainable_backbone

        inputs = layers.Input(shape=self.img_size + (3,))
        x = data_aug(inputs)
        x = self._preprocess(x)
        x = base(x, training=trainable_backbone)
        # Hub feature_vector already outputs a flat 1D vector, no pooling needed, hence removed GAP layer
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
