import os, sys
import random
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.constants as constants

train_images = os.path.join(constants.DATA_IMAGES_PATH, "train")
val_images = os.path.join(constants.DATA_IMAGES_PATH, "val")
train_labels = os.path.join(constants.DATA_LABELS_PATH, "train")
val_labels = os.path.join(constants.DATA_LABELS_PATH, "val")

image_files = []
for item in os.listdir(constants.DATA_IMAGES_PATH):
    full_path = os.path.join(constants.DATA_IMAGES_PATH, item)
    if os.path.isdir(full_path) and item != 'train' and item != 'val':
        for file in os.listdir(full_path):
            image_files.append(os.path.join(full_path, file))

random.shuffle(image_files)
split_ratio = 0.8
split_idx = int(len(image_files) * split_ratio)
train_files = image_files[:split_idx]
val_files = image_files[split_idx:]

def copy_pairs(files, image_dest, label_dest):
    for image_path in files:
        label_path = image_path.replace('\images', '\labels')
        base_name, extension = os.path.splitext(label_path)
        label_path = base_name + '.txt'
        
        shutil.copy(image_path, image_dest)
        shutil.copy(label_path, label_dest)

copy_pairs(train_files, train_images, train_labels)
copy_pairs(val_files, val_images, val_labels)

print(f"Split complete! {len(train_files)} train and {len(val_files)} val images.")