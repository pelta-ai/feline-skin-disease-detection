"""ConvNeXtTiny backbone for the shared classifier head."""

from keras.applications import ConvNeXtTiny
from keras.applications.convnext import preprocess_input

from .base_classifier import BaseClassifier


class ConvNeXtTinyClassifier(BaseClassifier):
    def _load_base(self):
        return ConvNeXtTiny(
            input_shape=self.img_size + (3,),
            include_top=False,
            weights="imagenet",
        )

    def _preprocess(self, x):
        return preprocess_input(x)
