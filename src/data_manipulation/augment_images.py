import os
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

def _flip_image(input_path, output_path):
    img = Image.open(input_path)
    flip_img = ImageOps.mirror(img)
    flip_img.save(output_path)

def _rotate_image(input_path, output_path):
    img = Image.open(input_path)
    rotate_img = img.rotate(45)
    rotate_img.save(output_path)

def _brighten_image(input_path, output_path):
    img = Image.open(input_path)
    bright_img = ImageEnhance.Brightness(img).enhance(1.5)
    bright_img.save(output_path)

def _contrast_image(input_path, output_path):
    img = Image.open(input_path)
    contrast_img = ImageEnhance.Contrast(img).enhance(1.8)
    contrast_img.save(output_path)

def _blur_image(input_path, output_path):
    img = Image.open(input_path)
    blur_img = img.filter(ImageFilter.GaussianBlur(radius=2))
    blur_img.save(output_path)

def _get_files_in_directory(directory_path):
    files = []
    for item in os.listdir(directory_path):
        full_path = os.path.join(directory_path, item)
        if os.path.isfile(full_path):
            files.append(full_path)
    return files

def add_augmented_images_in_directory(directory_path):
    files = _get_files_in_directory(directory_path)

    for file in files:
        base_name, extension = os.path.splitext(file)
        _flip_image(file, base_name + '_flipped' + extension)
        _rotate_image(file, base_name + '_rotated' + extension)
        _brighten_image(file, base_name + '_brightened' + extension)
        _contrast_image(file, base_name + '_contrasted' + extension)
        _blur_image(file, base_name + '_blurred' + extension)

add_augmented_images_in_directory('data\\images\\scabies2')