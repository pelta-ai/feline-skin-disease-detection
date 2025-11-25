import os
import numpy as np
import joblib

from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
import keras # type: ignore
from keras.models import Sequential
from keras.layers import Dense, Conv2D
from keras.layers import Activation, MaxPooling2D, Dropout, Flatten, Reshape
from keras.utils import to_categorical
from sklearn.preprocessing import LabelEncoder

import utils.constants as constants

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _abs(path):
    return path if os.path.isabs(path) else os.path.join(PROJECT_ROOT, path)

class ConvolutionNeuralNetwork:
    def __init__(self, num_epochs=30, layers=4, dropout=0.5):
        self.num_epochs = num_epochs
        self.layers = layers
        self.dropout = dropout
        self.label_encoder = LabelEncoder()
        self.label_path = _abs(os.path.join(constants.TRAINED_MODELS_PATH, 'sample_cnn_label_encoder.pkl'))
        self.model_path = _abs(os.path.join(constants.TRAINED_MODELS_PATH, 'sample_cnn.keras'))
        self.history = None
        self.model = None
        
    def build_model(self):
        model = Sequential()
        # Set input_shape in the first Conv2D layer
        model.add(Conv2D(filters=32, kernel_size=(3, 3), padding='same', input_shape=(224, 224, 3)))
        model.add(Activation('relu'))

        for _ in range(self.layers - 1):
            model.add(Conv2D(filters=32, kernel_size=(3, 3), padding='same'))
            model.add(Activation('relu'))

        model.add(Conv2D(32, (3, 3)))
        model.add(Activation('relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(self.dropout))

        model.add(Conv2D(64, (3, 3), padding='same'))
        model.add(Activation('relu'))
        model.add(Conv2D(64, (3, 3)))
        model.add(Activation('relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(self.dropout))

        model.add(Flatten())
        model.add(Dense(512))
        model.add(Activation('relu'))
        model.add(Dropout(self.dropout))
        model.add(Dense(6))
        model.add(Activation('softmax'))

        opt = keras.optimizers.RMSprop(learning_rate=0.0001)
        model.compile(loss='categorical_crossentropy', optimizer=opt, metrics=['accuracy'])
        self.model = model
        return model

    def load_and_preprocess(self):
        from data_manipulation.prepare_cnn_dataset import load_data  # avoid circular import
        data, labels = load_data()
        X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.1)

        y_train_encoded = self.label_encoder.fit_transform(y_train)
        y_test_encoded = self.label_encoder.transform(y_test)

        y_train_onehot = to_categorical(y_train_encoded)
        y_test_onehot = to_categorical(y_test_encoded)

        return X_train, X_test, y_train_encoded, y_test_encoded, y_train_onehot, y_test_onehot

    def train(self):
        X_train, X_test, y_train_encoded, y_test_encoded, y_train_onehot, y_test_onehot = self.load_and_preprocess()
        self.history = self.model.fit(X_train, y_train_onehot, epochs=self.num_epochs, batch_size=1, verbose=2) # type: ignore
        accuracy = self.get_accuracy_score(X_test, y_test_encoded)
        self.save_model()
        return accuracy

    def save_model(self, model_path=None, label_path=None):
        model_path = model_path or self.model_path
        label_path = label_path or self.label_path
        self.model.save(model_path) # type: ignore
        joblib.dump(self.label_encoder, label_path)

    def load_model(self, model_path=None, label_path=None):
        model_path = model_path or self.model_path
        label_path = label_path or self.label_path
        self.model = keras.models.load_model(model_path)
        print(self.model)
        self.label_encoder = joblib.load(label_path)

    def predict(self, X):
        return self.model.predict(X) # type: ignore

    def get_accuracy_score(self, X, y_true_encoded):
        y_pred_probs = self.predict(X)
        y_pred_labels = np.argmax(y_pred_probs, axis=1)
        return accuracy_score(y_true_encoded, y_pred_labels)

    def predict_label(self, image_array):
        image_array = np.expand_dims(image_array, axis=0)
        probs = self.model.predict(image_array)
        pred_index = np.argmax(probs, axis=1)[0]
        return self.label_encoder.inverse_transform([pred_index])[0]