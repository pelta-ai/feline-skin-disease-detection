import os, sys
import uuid
import logging
import json
import tempfile
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# OpenTelemetry imports (basic tracing - OTLP export can be added later)
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Add lib directory to path for imports
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from lib.storage import get_storage_provider, StorageProvider

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_DIR))

from src.generate_final_image import generate_final_image, warm_up
import src.utils.constants as constants

app = Flask(__name__)

# Enable CORS for local development (Flutter web runs on different port)
CORS(app)

# ============================================
# OpenTelemetry Setup (basic tracing)
# ============================================
# TODO: Add OTLP exporter for production (Grafana Cloud, etc.)
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Auto-instrument Flask (tracks request timing automatically)
FlaskInstrumentor().instrument_app(app)

# ============================================
# Structured Logging Setup
# ============================================
class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON logs with request_id"""
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "request_id": getattr(g, 'request_id', 'N/A') if hasattr(g, 'request_id') else 'N/A',
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

# Configure app logger
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
app.logger.handlers = [handler]
app.logger.setLevel(logging.INFO)

# ============================================
# Request ID Middleware
# ============================================
@app.before_request
def add_request_id():
    """Extract or generate request ID for correlation"""
    g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    # Add to current span as attribute
    current_span = trace.get_current_span()
    if current_span:
        current_span.set_attribute("request.id", g.request_id)

@app.after_request
def log_request(response):
    """Log every request with request ID and add to response headers"""
    response.headers['X-Request-ID'] = g.request_id
    app.logger.info(f"{request.method} {request.path} → {response.status_code}")
    return response

# ============================================
# Storage Provider
# ============================================
# Initialize storage provider (can be overridden via STORAGE_PROVIDER env var for testing)
storage: StorageProvider = get_storage_provider()

@app.route('/list-objects', methods=['GET'])
def list_objects():
    prefix = request.args.get('prefix') or ""
    object_paths = storage.list_objects(prefix=prefix)
    return jsonify(object_paths)

@app.route('/folder-exists', methods=['GET'])
def check_folder_exists():
    path = request.args.get('path')
    exists = storage.folder_exists(path)
    return jsonify({'exists': exists})

@app.route('/create-user-folder', methods=['POST'])
def create_user_folder():
    user_id = request.json.get('user_id')
    storage.create_user_folder(user_id)
    return jsonify({'status': 'created'})

@app.route('/create-today-folder', methods=['POST'])
def create_today_folder():
    user_id = request.json.get('user_id')
    storage.create_today_folders(user_id)
    return jsonify({'status': 'created'})

@app.route('/add-file', methods=['POST'])
def upload_file():
    try:
        user_id = request.form.get('user_id')
        file = request.files.get('file')
        is_annotated_str = request.form.get('is_annotated')

        if not user_id or not file or not is_annotated_str:
            return jsonify({'error': 'user_id, is_annotated, and file are required'}), 400

        # Use a valid temp directory
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)

        # Convert string to boolean for the storage provider
        is_annotated = is_annotated_str.lower() == "true"
        storage.add_file(file.filename, temp_path, user_id, is_annotated)

        return jsonify({'status': 'uploaded', 'file': file.filename}), 200
    except Exception as e:
        app.logger.error(f"Error uploading file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-file-url', methods=['GET'])
def get_file_url():
    try:
        path = request.args.get('path')
        if not path:
            return jsonify({'error': 'Path is required'}), 400

        url = storage.get_file_url(path)
        return jsonify({'url': url})
    except Exception as e:
        app.logger.error(f"Error generating URL: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/serve-file', methods=['GET'])
def serve_file():
    """Serve a file from storage (for mock mode where URLs aren't real)."""
    from flask import Response
    try:
        path = request.args.get('path')
        if not path:
            return jsonify({'error': 'Path is required'}), 400

        # Get file content from mock storage
        if hasattr(storage, '_files') and path in storage._files:
            content = storage._files[path]

            # Determine content type based on extension
            ext = path.lower().split('.')[-1] if '.' in path else ''
            content_types = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp',
                'txt': 'text/plain',
                'json': 'application/json',
            }
            content_type = content_types.get(ext, 'application/octet-stream')

            return Response(content, mimetype=content_type)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        app.logger.error(f"Error serving file: {e}")
        return jsonify({'error': str(e)}), 500
    
@app.post("/download-file")
def download_from_s3_api():
    file_name = request.form["file_name"]
    s3_key = request.form["s3_key"]

    # Create temp directory for downloaded files
    local_dir = "temp_folder/raw_image"
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, file_name)

    result = storage.download_file(s3_key, local_path)

    if not result:
        return jsonify({"status": "error", "message": "download_failed"}), 500

    return jsonify({"status": "ok", "local_path": result}), 200

@app.get("/get-today-date")
def get_today_date_api():
    return {"date": StorageProvider.get_today_date()}

@app.post("/generate-ai-predictions")
def generate_ai_predictions():
    try:
        data = request.get_json(silent=True) or request.form

        user_id = data.get("user_id")
        file_name = data.get("file_name")
        s3_key = data.get("s3_key")

        if not (user_id and file_name and s3_key):
            return jsonify({"status": "error", "message": "user_id_file_name_s3_key_required"}), 400

        # 1) Download from storage into temp_folder/raw_image
        local_dir = "temp_folder/raw_image"
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, file_name)

        result_path = storage.download_file(s3_key, local_path)
        if not result_path:
            return jsonify({"status": "error", "message": "download_failed"}), 500

        # 2) Run YOLO + CNN on the downloaded image
        result = generate_final_image(result_path)
        if not result or "output_path" not in result:
            return jsonify({"status": "error", "message": "ai_prediction_generation_failed"}), 500

        label = result["label"]
        annotated_image_path = result["output_path"]

        # 3) Upload annotated image back to storage
        if not os.path.exists(annotated_image_path):
            return jsonify({"status": "error", "message": "annotated_image_missing"}), 500

        annotated_file_name = os.path.basename(annotated_image_path)
        storage.add_file(annotated_file_name, annotated_image_path, user_id, is_annotated=True)

        # Clean up temp folder
        try:
            shutil.rmtree(constants.TEMP_FOLDER_PATH)
            app.logger.info(f"Temp folder cleaned up")
        except OSError as e:
            app.logger.warning(f"Error deleting temp folder: {e}")

        today = StorageProvider.get_today_date()
        annotated_s3_key = f"{user_id}/{today}/annotated_images/{annotated_file_name}"
        url = storage.get_file_url(annotated_s3_key)

        return jsonify({
            "status": "ok",
            "label": label,
            "annotated_image_path": annotated_image_path,
            "annotated_s3_key": annotated_s3_key,
            "annotated_url": url,
        }), 200

    except Exception as e:
        app.logger.error(f"Error in AI predictions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for container orchestration."""
    return jsonify({
        "status": "healthy",
        "service": "pelta-ai-backend"
    }), 200


if __name__ == "__main__":
    # Configuration via environment variables (secure for production)
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')  # 0.0.0.0 for containers
    port = int(os.environ.get('FLASK_PORT', '5000'))

    # Load the CNN ensemble now so the first /generate-ai-predictions request
    # isn't slowed by a cold model load. Under gunicorn, use --preload (or call
    # warm_up() from a worker hook) to get the same benefit per worker.
    app.logger.info("Preloading CNN ensemble...")
    warm_up()
    app.logger.info("Ensemble loaded.")

    app.logger.info(f"Starting server on {host}:{port} (debug={debug_mode})")
    app.run(host=host, port=port, debug=debug_mode)