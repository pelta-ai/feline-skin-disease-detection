import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.constants as constants

def data_leakage_audit():
    train_path = os.path.join(constants.DATA_IMAGES_PATH, "train")
    test_path = os.path.join(constants.DATA_IMAGES_PATH, "test")
    val_path = os.path.join(constants.DATA_IMAGES_PATH, "val")

    train_images = []
    test_images = []
    val_images = []

    for class_name in os.listdir(train_path):
        train_images += os.listdir(os.path.join(train_path, class_name))

    for class_name in os.listdir(test_path):
        test_images += os.listdir(os.path.join(test_path, class_name))

    for class_name in os.listdir(val_path):
        val_images += os.listdir(os.path.join(val_path, class_name))

    leaks = set()
    train_set = set(train_images)
    test_set = set(test_images)
    val_set = set(val_images)

    leaks = (train_set & test_set) | (train_set & val_set) | (test_set & val_set)
    return leaks

if __name__ == "__main__":
    leaks = data_leakage_audit()
    if len(leaks) != 0:
            raise ValueError("There were " + str(len(leaks)) + " images that were duplicated across the train, test, and val datasets. This is a problem and can inflate performance. Please fix before continuing.")
    
    print("No leakages!")