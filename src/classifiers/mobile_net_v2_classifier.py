"""MobileNetV2 backbone for the shared classifier head."""

from keras.applications import MobileNetV2
from keras.applications.mobilenet_v2 import preprocess_input

from src.classifiers.base_classifier import BaseClassifier


class MobileNetV2Classifier(BaseClassifier):
    def _load_base(self):
        return MobileNetV2(
            input_shape=self.img_size + (3,),
            include_top=False,
            weights="imagenet",
        )

    def _preprocess(self, x):
        return preprocess_input(x)
