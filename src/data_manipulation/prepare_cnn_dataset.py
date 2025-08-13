import os, sys
import cv2
import numpy as np
from PIL import Image

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.constants as constants

def change_image_resolution(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return None
    resized_img = cv2.resize(img, (224, 224))
    resized_rgb_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
    return resized_rgb_img

def get_image_and_label_arrays():
    output = []
    labels = []

    for folder in os.listdir(constants.DATA_IMAGES_PATH):
        full_folder_path = os.path.join(constants.DATA_IMAGES_PATH, folder)
        if not os.path.isdir(full_folder_path):
            continue  # skip non-directories
        base_name = folder  # use folder name as label

        for image in os.listdir(full_folder_path):
            full_image_path = os.path.join(full_folder_path, image)
            # skip non-image files
            if not os.path.isfile(full_image_path):
                continue
            arr = change_image_resolution(full_image_path)
            if arr is None:
                print(f"Warning: Could not read image {full_image_path}, skipping.")
                continue
            output.append(arr)
            labels.append(base_name)

    if not output:
        raise ValueError("No images found in dataset. Please check your data directory.")
    return np.array(output), np.array(labels)
            
def create_final_data():
    images, labels = get_image_and_label_arrays()
    np.savez(constants.DATA_PATH + '\\' + constants.CNN_DATA_NPZ_NAME + '.npz', images=images, labels=labels)

    print("Data file successfully created.")


def load_data():
    try:
        loaded = np.load(constants.DATA_PATH + '\\' + constants.CNN_DATA_NPZ_NAME + '.npz')
        images = loaded['images']
        labels = loaded['labels']
        return images,labels
    except Exception as e:
        raise FileNotFoundError('The data file:' + constants.DATA_PATH + '\\' + constants.CNN_DATA_NPZ_NAME + '.npz does not exist. Error: ' + e)

create_final_data()