import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.constants as constants

class_ids = {'acne': 0, 'flea_allergy': 1, 'lumps_and_bumps': 2, 'ringworm': 3, 'scabies': 4}

def change_class_id_in_labels(labels_directory_path):
    for folder in os.listdir(labels_directory_path):
        for file in os.listdir(labels_directory_path + '\\' + folder):
            file_path = labels_directory_path + '\\' + folder + '\\' + file

            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            updated_lines = ''
            for line in lines:
                parts = line.strip().split()

                if parts:
                    parts[0] = class_ids.get(folder)

                    updated_line = ''
                    for part in parts:
                        updated_line += str(part)
                        updated_line += ' '
                    
                updated_lines += updated_line.strip()
                updated_lines += '\n'
            
            with open(file_path, "w") as f:
                f.write(updated_lines)
            print(f"Updated {file}")
            

change_class_id_in_labels(constants.DATA_LABELS_PATH)