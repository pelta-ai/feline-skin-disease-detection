"""MobileNetV3Small backbone for the shared classifier head."""

from keras.applications import MobileNetV3Small
from keras.applications.mobilenet_v3 import preprocess_input

from .base_classifier import BaseClassifier


class MobileNetV3SmallClassifier(BaseClassifier):
    def _load_base(self):
        return MobileNetV3Small(
            input_shape=self.img_size + (3,),
            include_top=False,
            weights="imagenet",
        )

    def _preprocess(self, x):
        return preprocess_input(x)
