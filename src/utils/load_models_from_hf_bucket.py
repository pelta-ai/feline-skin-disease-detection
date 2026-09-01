import os, sys

from dotenv import load_dotenv
from huggingface_hub import download_bucket_files
from huggingface_hub.errors import BucketNotFoundError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import src.utils.constants as constants

load_dotenv()
print("token loaded:", bool(os.environ.get("HF_TOKEN")))

# Resolve against the project root, not the CWD: ensemble.get_model_paths_ready()
# looks for the models under PROJECT_ROOT, so downloading to a CWD-relative folder
# would re-download on every run and still fail the lookup.
local_file_path = os.path.join(constants.PROJECT_ROOT, constants.TRAINED_MODELS_PATH)


def _bucket_id():
    """download_bucket_files() takes '<namespace>/<bucket>', not the hf:// handle."""
    uri = constants.HF_BUCKET_URI
    prefix = "hf://buckets/"

    if not uri.startswith(prefix):
        raise ValueError(
            f"HF_BUCKET_URI must look like {prefix}<namespace>/<bucket>, got '{uri}'"
        )

    return uri[len(prefix):].strip("/")


def load_models_from_hf_bucket(filename):
    os.makedirs(local_file_path, exist_ok=True)

    final_local_file_path = os.path.join(local_file_path, filename)

    if os.path.exists(final_local_file_path) and os.path.getsize(final_local_file_path) > 0:
        return

    # Download to a temporary name and rename only once it lands. A failed or
    # interrupted download must not leave a 0-byte file behind, otherwise the
    # cache check above would treat it as already downloaded and keras would
    # fail later on an empty model file.
    partial_path = final_local_file_path + ".partial"

    try:
        download_bucket_files(_bucket_id(), files=[(filename, partial_path)])

        # A missing file is not an error for download_bucket_files() - it warns
        # and skips it - so check that something actually arrived.
        if not os.path.exists(partial_path) or os.path.getsize(partial_path) == 0:
            raise FileNotFoundError(
                f"'{filename}' was not found in the bucket at {constants.HF_BUCKET_URI}. "
                "Check the filename against 'hf buckets ls "
                f"{_bucket_id()} -R'."
            )

        os.replace(partial_path, final_local_file_path)
        print(f"Successfully downloaded to {final_local_file_path}")
    except BucketNotFoundError:
        raise BucketNotFoundError(
            f"Bucket '{_bucket_id()}' was not found. Check HF_BUCKET_URI, and make "
            "sure HF_TOKEN is set with read access if the bucket is private."
        )
    finally:
        if os.path.exists(partial_path):
            os.remove(partial_path)
