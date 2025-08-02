import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.constants as constants

def create_empty_text_files(name, directory_path, starting_counter=1, ending_counter=50):
    for counter in range(starting_counter, ending_counter + 1):
        file_path = directory_path + '\\' + name + str(counter) + '.txt'
        with open(file_path, 'w') as f:
            pass

create_empty_text_files('healthy_', constants.DATA_LABELS_PATH + '\\healthy')