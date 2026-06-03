"""EfficientNetV2B0 backbone for the shared classifier head."""

from keras.applications import EfficientNetV2B0
from keras.applications.efficientnet_v2 import preprocess_input

from .base_classifier import BaseClassifier


class EfficientNetV2B0Classifier(BaseClassifier):
    def _load_base(self):
        return EfficientNetV2B0(
            input_shape=self.img_size + (3,),
            include_top=False,
            weights="imagenet",
        )

    def _preprocess(self, x):
        return preprocess_input(x)
