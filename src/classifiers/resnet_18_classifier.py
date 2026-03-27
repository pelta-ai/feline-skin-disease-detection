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
    
    def _build_model(self, input_shape=constants.IMG_SIZE + (3,), trainable_backbone=False, train_from_block=None, **kwargs):
        inputs = layers.Input(shape=input_shape)

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

        x = layers.GlobalAveragePooling2D()(x)
        outputs = layers.Dense(6, activation="softmax")(x)

        model = models.Model(inputs, outputs, name="resnet18")

        if not trainable_backbone:
            model.trainable = False
        else:
            model.trainable = True
            if train_from_block is not None:
                for layer in model.layers[:train_from_block]:
                    layer.trainable = False
                    
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=kwargs.get('learning_rate', 1e-3)),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )

        return model
    
    def _load_base(self):
        return self._build_model(self.img_size + (3,))
    
    def _preprocess(self, x):
        return x / 255.0