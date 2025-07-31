import os

def remove_label_studio_prefixes_in_directory(directory_path, prefix_length=9):
    for item in os.listdir(directory_path):
        full_path = os.path.join(directory_path, item)

        if os.path.isfile(full_path):
            base_name, extension = os.path.splitext(item)
            new_name = base_name[prefix_length:] + extension
            new_full_path = os.path.join(directory_path, new_name)
            os.rename(full_path, new_full_path)

remove_label_studio_prefixes_in_directory('data\\labels\\acne')