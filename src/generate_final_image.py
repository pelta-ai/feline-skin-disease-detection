import os, sys
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.constants as constants
from src.convolutional_neural_network import ConvolutionNeuralNetwork as cnn

def generate_final_image(image_path, cnn_model_path=constants.CNN_MODEL_PATH, yolo_model_path=constants.YOLO_MODEL_PATH):
    model = YOLO(yolo_model_path)
    if not os.path.exists(cnn_model_path):
        raise FileNotFoundError(f'CNN model file not found: {cnn_model_path}')
    if not cnn_model_path.endswith('.keras'):
        raise ValueError(f'CNN model file must be a .keras file (full model). Got: {cnn_model_path}')
    cnn_model = cnn()
    try:
        cnn_model.load_model(model_path=cnn_model_path)
    except Exception as e:
        raise RuntimeError(f'Failed to load full Keras model from {cnn_model_path}. Make sure it was saved with model.save(...). Error: {e}')

    image = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
 
    results = model(image_path)
    boxes = results[0].boxes.xyxy.cpu().numpy()  # (x1, y1, x2, y2)

    for box in boxes:
        x1, y1, x2, y2 = map(int, box)

        cropped = img_rgb[y1:y2, x1:x2]
        if cropped.size == 0:
            continue

        img_pil = Image.fromarray(cropped).resize((224, 224)).convert('RGB')
        arr = np.array(img_pil)
        label = predict_from_image_array(arr, cnn_model)

        cv2.rectangle(image, (x1, y1), (x2, y2), constants.DISEASE_COLORS[label], 2)

    base_name = os.path.basename(image_path)
    base_name_without_extension = os.path.splitext(base_name)[0]
    output_path = constants.TEST_RESULTS_PATH + '\\' + base_name_without_extension + '.jpg'
    cv2.imwrite(output_path, image)
    print(f'Saved: {output_path}')

    return label

def predict_from_image_array(arr, model):
    # arr should be (224, 224, 3)
    label = model.predict_label(arr)
    return label

generate_final_image(constants.TEST_IMAGES_PATH + '\\sample_acne_1.jpg')