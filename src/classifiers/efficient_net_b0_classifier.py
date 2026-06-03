"""EfficientNetB0 backbone for the shared classifier head."""

from keras.applications import EfficientNetB0
from keras.applications.efficientnet import preprocess_input

from .base_classifier import BaseClassifier


class EfficientNetB0Classifier(BaseClassifier):
    def _load_base(self):
        return EfficientNetB0(
            input_shape=self.img_size + (3,),
            include_top=False,
            weights="imagenet",
        )

    def _preprocess(self, x):
        return preprocess_input(x)
