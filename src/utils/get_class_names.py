import os, sys
import utils.constants as constants

def get_class_names(directory=os.path.join(constants.DATA_PATH, "train")):
    try:
        return os.listdir(directory)
    except FileNotFoundError:
        print("The specified directory does not exist.")