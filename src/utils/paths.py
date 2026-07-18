import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.constants as constants

def abs_path(path):
    return path if os.path.isabs(path) else os.path.join(constants.PROJECT_ROOT, path)