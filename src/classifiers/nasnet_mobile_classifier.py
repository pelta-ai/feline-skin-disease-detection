"""NASNetMobile backbone for the shared classifier head."""

from keras.applications import NASNetMobile
from keras.applications.nasnet import preprocess_input

from .base_classifier import BaseClassifier


class NASNetMobileClassifier(BaseClassifier):
    def _load_base(self):
        return NASNetMobile(
            input_shape=self.img_size + (3,),
            include_top=False,
            weights="imagenet",
        )

    def _preprocess(self, x):
        return preprocess_input(x)
