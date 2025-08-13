import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import src.convolutional_neural_network as cnn

cnn_model = cnn.ConvolutionNeuralNetwork(num_epochs=30)
cnn_model.build_model()
cnn_model.train()
