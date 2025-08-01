import os

def rename_files_in_directory(directory_path, new_name_prefix, counter_start_value=1):
    counter = counter_start_value

    for item in os.listdir(directory_path):
        full_path = os.path.join(directory_path, item)

        if os.path.isfile(full_path):
            base_name, extension = os.path.splitext(item)
            new_name = new_name_prefix + str(counter) + extension
            new_full_path = os.path.join(directory_path, new_name)
            os.rename(full_path, new_full_path)
            counter += 1

rename_files_in_directory('data\\images\\healthy', 'healthy_', 1)