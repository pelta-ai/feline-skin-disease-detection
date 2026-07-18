import os, sys, gc
import numpy as np
import keras

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils.constants as constants
from utils.paths import abs_path


# Models are expensive to load (seconds each), so cache them across calls keyed
# by the resolved path tuple. Behind Flask this means the ensemble loads once on
# the first request and is reused for every prediction after that.
_MODEL_CACHE = {}

def get_model_paths_ready(model_paths=None):
    if model_paths is None:
        model_paths = constants.ENSEMBLE_MODEL_PATHS

    model_paths_full = [abs_path(p) for p in model_paths]

    if not model_paths_full:
        raise ValueError("No ensemble models provided")

    for p in model_paths_full:
        if not p.endswith(".keras"):
            raise ValueError(f"Ensemble model must be a .keras model: {p}")
        if not os.path.exists(p):
            raise FileNotFoundError(f"CNN model file not found: {p}")
        
    return model_paths_full

def load_ensemble(model_paths_full):
    cache_key = tuple(model_paths_full)

    if cache_key not in _MODEL_CACHE:
        _MODEL_CACHE[cache_key] = [keras.models.load_model(p) for p in model_paths_full]
        
    return _MODEL_CACHE[cache_key]

def ensemble_predict(arr, model_paths=None, low_mem=False):
    paths = get_model_paths_ready(model_paths)

    if low_mem:
        return _avg_probs_low_mem(arr, paths)
    
    models = load_ensemble(paths)
    return np.mean([np.array(m(arr, training=False)) for m in models], axis=0)

def _avg_probs_low_mem(arr, model_paths):
    """Average ensemble probabilities while holding only one model in memory at
    a time: load, predict, free, repeat. Peak RAM stays at ~one model instead of
    the whole ensemble, which avoids swap thrashing on low-RAM machines. Slower
    (re-reads each model from disk) but the only way to run the ensemble when
    free RAM is smaller than the loaded ensemble."""
    total = None
    for p in model_paths:
        model = keras.models.load_model(p)
        probs = np.array(model(arr, training=False))
        total = probs if total is None else total + probs
        del model
        keras.backend.clear_session()
        gc.collect()
    return total / len(model_paths)