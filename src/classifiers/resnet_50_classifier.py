"""ResNet50 backbone for the shared classifier head."""

from keras.applications import ResNet50
from keras.applications.resnet50 import preprocess_input

from .base_classifier import BaseClassifier


class ResNet50Classifier(BaseClassifier):
    def _load_base(self):
        return ResNet50(
            input_shape=self.img_size + (3,),
            include_top=False,
            weights="imagenet",
        )

    def _preprocess(self, x):
        return preprocess_input(x)
