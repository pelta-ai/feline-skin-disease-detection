import os, sys
import numpy as np
import tensorflow as tf

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.classifiers.classifier_factory import ClassifierFactory

ARCHS = ["mobilenet_v2", "mobilenet_v3_small", "resnet50", "efficientnet_b0",
         "efficientnet_v2_b0", "nasnet_mobile", "convnext_tiny"]

# a tensor spanning the full 0-255 range your datasets produce
probe = tf.constant(np.linspace(0, 255, 224*224*3, dtype="float32").reshape(1, 224, 224, 3))

for arch in ARCHS:
    clf = ClassifierFactory.create(arch, name=arch)
    out = clf._preprocess(probe).numpy()
    print(f"{arch:22s} in [0.0, 255.0] -> out [{out.min():8.3f}, {out.max():8.3f}]")
    tf.keras.backend.clear_session()