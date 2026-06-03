"""ResNet18 backbone (via TensorFlow Hub) for the shared classifier head."""

from tensorflow import keras
from keras import layers, models

from ..utils import constants
from .base_classifier import BaseClassifier


class ResNet18Classifier(BaseClassifier):
    def _residual_block(self, x, filters, stride=1):
        shortcut = x

        x = layers.Conv2D(filters=filters, kernel_size=3, strides=stride, padding="same", use_bias=False)(x)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)

        x = layers.Conv2D(filters=filters, kernel_size=3, strides=1, padding="same", use_bias=False)(x)
        x = layers.BatchNormalization()(x)

        input_channels = shortcut.shape[-1]

        if stride != 1 or input_channels != filters:                                                        
            shortcut = layers.Conv2D(filters, 1, strides=stride, padding="same", use_bias=False)(shortcut)         
            shortcut = layers.BatchNormalization()(shortcut)           

        x = layers.Add()([x, shortcut])
        x = layers.ReLU()(x)

        return x
    
    def _load_base(self):
        inputs = layers.Input(shape=self.img_size + (3,))

        x = layers.Conv2D(filters=64, kernel_size=7, strides=2, padding="same", use_bias=False)(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)
        x = layers.MaxPooling2D(3, strides=2, padding="same")(x)

        x = self._residual_block(x, 64)
        x = self._residual_block(x, 64)

        x = self._residual_block(x, 128, stride=2)
        x = self._residual_block(x, 128)

        x = self._residual_block(x, 256, stride=2)
        x = self._residual_block(x, 256)

        x = self._residual_block(x, 512, stride=2)
        x = self._residual_block(x, 512)

        return models.Model(inputs, x, name="resnet18")
    
    def _preprocess(self, x):
        return x / 255.0