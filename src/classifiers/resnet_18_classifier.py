"""ResNet18 backbone (via TensorFlow Hub) for the shared classifier head."""

from tensorflow import keras
from keras import layers, models

from .base_classifier import BaseClassifier


class ResNet18Classifier(BaseClassifier):
    def _residual_block(x, filters, stride=1):
        shortcut = x

        x = layers.Conv2D(filters=filters, kernel_size=3, strides=stride, padding="same", use_bias=False)(x)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)

        x = layers.Conv2D(filters=filters, kernel_size=3, strides=1, padding="same", use_bias=False)(x)
        x = layers.BatchNormalization()(x)

        if stride != 1 or shortcut.shape[-1] != filters:                                                           
            shortcut = layers.Conv2D(filters, 1, strides=stride, padding="same", use_bias=False)(shortcut)         
            shortcut = layers.BatchNormalization()(shortcut)           

        x = layers.Add()[x, shortcut]
        x = layers.ReLU()(x)

        return x
    
    def _build_model(self, input_shape):
        inputs = layers.Input(shape=input_shape)

        x = layers.Conv2D(filters=64, kernel_size=7, strides=2, padding="same", use_bias=False)
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
    
    def _load_base(self):
        return self._build_model(self.img_size + (3,))
    
    def _preprocess(self, x):
        return x / 255.0