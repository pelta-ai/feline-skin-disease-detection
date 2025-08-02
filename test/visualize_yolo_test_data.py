import sys, os
import cv2
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import src.utils.constants as constants
from src.utils.yolo_and_regular_coordinates_conversion import*

def visualize_yolo_test_data(image_path, file_path):
    image = cv2.imread(image_path)

    words = None
    with open(file_path, 'r') as file:
        content = file.read()
        words = content.split()
        print(words)

    x_center = float(words[1])
    y_center = float(words[2])
    width = float(words[3])
    height = float(words[4])

    image_w, image_h, _ = image.shape
    x1b, y1b, x2b, y2b = from_yolo_format(x_center, y_center, width, height, image_w, image_h)
    print(x1b, y1b, x2b, y2b)
    
    cv2.rectangle(image, (x1b, y1b), (x2b, y2b), (0, 255, 0), 2)
    output_path = constants.TEST_RESULTS_PATH + "\\visualized_yolo_test_data.jpg"
    cv2.imwrite(output_path, image)
    image_array = plt.imread(output_path)
    plt.imshow(image_array)
    plt.show()

visualize_yolo_test_data(constants.DATA_IMAGES_PATH + '\\acne\\acne_1.jpg', constants.DATA_LABELS_PATH + '\\acne\\acne_1.txt')