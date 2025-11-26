import os, sys, tempfile
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.constants as constants
from src.convolutional_neural_network import ConvolutionNeuralNetwork as cnn


def generate_final_image(image_path, output_dir=constants.TEMP_FOLDER_ANNOTATED_PATH, cnn_model_path=constants.CNN_MODEL_PATH, yolo_model_path=constants.YOLO_MODEL_PATH):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _abs(path):
        return path if os.path.isabs(path) else os.path.join(project_root, path)

    yolo_model_full = _abs(yolo_model_path)
    cnn_model_full = _abs(cnn_model_path)
    output_dir_full = _abs(output_dir)

    if not os.path.exists(yolo_model_full):
        raise FileNotFoundError(f"YOLO model file not found: {yolo_model_full}")

    if not os.path.exists(cnn_model_full):
        raise FileNotFoundError(f"CNN model file not found: {cnn_model_full}")

    if not cnn_model_full.endswith(".keras"):
        raise ValueError("CNN model must be a .keras model")

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Input image not found: {image_path}")


    model = YOLO(yolo_model_full)
    cnn_model = cnn()
    cnn_model.load_model(model_path=cnn_model_full)
    
    # validate input image
    if not os.path.exists(image_path):
        raise FileNotFoundError(f'Input image not found: {image_path}')
    image = cv2.imread(str(image_path))
    if image is None:
        raise RuntimeError(f'cv2 failed to load image: {image_path}')
    
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    results = model(image_path)
    if len(results) == 0 or results[0].boxes is None or len(results[0].boxes) == 0:
        boxes = np.array([])
    else:
        boxes = results[0].boxes.xyxy.cpu().numpy()

    labels = []

    if boxes.size > 0:
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)


            cropped = img_rgb[y1:y2, x1:x2]
            if cropped.size == 0:
                continue

            img_pil = Image.fromarray(cropped).resize((224, 224)).convert('RGB')
            arr = np.array(img_pil)

            label = predict_from_image_array(arr, cnn_model)
            labels.append(label)


            if label in constants.DISEASE_COLORS:
                cv2.rectangle(image, (x1, y1), (x2, y2), constants.DISEASE_COLORS[label], 10)
    else:
        labels.append("healthy")

    if not labels:
        labels.append("healthy")

    base_name = os.path.basename(image_path)
    base_name_without_extension = os.path.splitext(base_name)[0]
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, base_name_without_extension + ".jpg")

    cv2.imwrite(output_path, image)
    print(f"Saved annotated image to: {output_path}")

    if labels:
        main_label = max(set(labels), key=labels.count)
    else:
        main_label = "healthy"

    print(main_label)

    return {
        "label": main_label,
        "output_path": output_path,
    }


def predict_from_image_array(arr, model):
    # arr should be (224, 224, 3)
    label = model.predict_label(arr)
    return label

# generate_final_image(constants.TEST_IMAGES_PATH + '\\sample_acne_1.jpg')