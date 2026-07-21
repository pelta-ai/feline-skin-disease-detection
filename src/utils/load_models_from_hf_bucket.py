from huggingface_hub import HfFileSystem
import os, sys
from dotenv import load_dotenv
from huggingface_hub.errors import RepositoryNotFoundError, EntryNotFoundError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import src.utils.constants as constants

fs = HfFileSystem()

load_dotenv()
print("token loaded:", bool(os.environ.get("HF_TOKEN")))

remote_file_path = f"{constants.HF_BUCKET_URI}"
local_file_path = "./trained_models"

def load_models_from_hf_bucket(filename):
    os.makedirs("./trained_models", exist_ok=True)

    final_remote_file_path = f"{constants.HF_BUCKET_URI}/{filename}"
    final_local_file_path = os.path.join(local_file_path, filename)

    if os.path.exists(final_local_file_path):
        return
    
    try:
        fs.download(final_remote_file_path, final_local_file_path)
        print(f"Successfully downloaded to {local_file_path}")
    except RepositoryNotFoundError:
        raise RepositoryNotFoundError(
            f"Repository/Bucket was not found!"
            "Please check your spelling or run 'huggingface-cli login' if this is a private bucket."
        )
    except EntryNotFoundError:
        raise EntryNotFoundError(
            f"'{filename}' was not found inside the bucket!"
            f"The bucket exists, but '{os.path.basename(final_remote_file_path)}' was not found in it."
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            f"'{filename}' not found at {remote_file_path}. "
            "Check the filename and that HF_BUCKET_URI is hf://buckets/<namespace>/<bucket>. "
            "If the bucket is private, make sure HF_TOKEN is set."
        )
    except Exception as e:
        raise Exception(f"\n[ERROR] An unexpected error occurred: {e}")