import os, sys
import uuid
import ipaddress
import logging
import json
import tempfile
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, g, send_from_directory, has_app_context
from flask_cors import CORS
from flask_limiter import Limiter
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# OpenTelemetry imports (basic tracing - OTLP export can be added later)
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Keep the CNN model directory alongside the app so the HF download and
# inference-time loading resolve to the same place regardless of the process
# working directory. Must be set BEFORE importing src.utils.constants, which
# reads MODEL_DIR once at import time. setdefault lets an explicit external
# MODEL_DIR (e.g. a mounted volume in a container) still win.
os.environ.setdefault(
    "MODEL_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "trained_models"),
)

# Add lib directory to path for imports
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from lib.storage import get_storage_provider, StorageProvider

_APP_FILE = Path(__file__).resolve()
PROJECT_ROOT = (
    _APP_FILE.parent
    if (_APP_FILE.parent / "src").is_dir()
    else _APP_FILE.parents[2]
)
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_DIR))

from src.generate_final_image import generate_final_image
import src.ensemble as ensemble
import src.utils.constants as constants

app = Flask(__name__, static_folder="static", static_url_path="")

# ============================================
# CORS
# ============================================
# Only the origins we actually ship from may read API responses. Once the web
# build is served from a CDN (Cloudflare Pages) instead of this Flask app, the
# frontend is a different origin and needs to be named here explicitly.
#
# Note this is a browser-side control only: it stops other sites' JavaScript
# from reading responses, and does nothing against a direct client (curl). It is
# not a substitute for authentication on the endpoints below.
#
# flask-cors treats an origin as a regex if it contains any of * \ ] ? $ ^ [ ( ),
# and matches with re.match(), which is NOT anchored at the end. A pattern like
# "http://localhost:*" would therefore also match "http://localhost.evil.com",
# so the dev default is spelled as an explicitly anchored regex. Origins passed
# via ALLOWED_ORIGINS contain no regex characters in practice (e.g.
# "https://pelta-ai.com") and so are compared as case-insensitive literals.
_DEV_ORIGIN_PATTERN = r"^http://(localhost|127\.0\.0\.1)(:[0-9]+)?$"

_configured_origins = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
ALLOWED_ORIGINS = _configured_origins or [_DEV_ORIGIN_PATTERN]
CORS(app, origins=ALLOWED_ORIGINS)

# ============================================
# Rate Limiting (per-client-IP)
# ============================================
# Throttle the compute-heavy prediction endpoint and storage mutations to blunt
# abuse/DoS once the app is publicly reachable. Behind the HF Spaces proxy the
# real client IP is in X-Forwarded-For (request.remote_addr is the proxy), so we
# key on that. In-memory storage is fine: the app runs as a single gunicorn
# worker, so there is one shared counter.
def _client_ip():
    """Best-effort real client IP, resistant to X-Forwarded-For spoofing.

    X-Forwarded-For is a client-supplied header that each proxy *appends* to, so
    the leftmost entry is whatever the caller invented and the rightmost entries
    were added by infrastructure we trust. Keying on the leftmost entry lets a
    caller rotate a fake value per request and bypass every limit below, so walk
    from the right instead and take the first routable address: any spoofed
    prefix sits to the left of the address the edge appended and is never
    reached. Private/loopback hops (the Space's own ingress) are skipped.
    """
    xff = request.headers.get("X-Forwarded-For", "")
    for candidate in reversed(xff.split(",")):
        candidate = candidate.strip()
        if not candidate:
            continue
        try:
            parsed = ipaddress.ip_address(candidate)
        except ValueError:
            continue  # not an IP at all — ignore rather than trust it
        if parsed.is_private or parsed.is_loopback or parsed.is_link_local:
            continue
        return candidate
    return request.remote_addr or "127.0.0.1"

limiter = Limiter(
    key_func=_client_ip,
    app=app,
    storage_uri="memory://",
    default_limits=[],  # no global limit — static assets and /health stay unthrottled
)

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
            "request_id": (g.request_id if has_app_context() and hasattr(g, "request_id") else "N/A"),
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

# ============================================
# Model Warm-up
# ============================================
# Load the CNN ensemble into the resident cache when this module is imported, so
# the first scan doesn't pay the multi-second per-model load cost. This runs both
# under `python app.py` and when a WSGI server (gunicorn/uwsgi) imports the app.
try:
    app.logger.info("Warming up CNN ensemble...")
    ensemble.warm_up()
    app.logger.info("CNN ensemble ready")
except Exception as e:
    # Don't block startup if warm-up fails — models will lazily load on first
    # scan instead, and the error surfaces there.
    app.logger.error(f"Model warm-up failed (will load lazily on first scan): {e}")

# ============================================
# Upload path safety
# ============================================
def _safe_upload_path(base_dir, filename):
    """Resolve an uploaded file's name to a path guaranteed to sit in base_dir.

    Returns (path, None) on success or (None, error_message) if the name is
    unusable. `filename` comes straight off the wire and cannot be trusted:
    os.path.join() silently discards its prefix when handed an absolute path
    (so "/app/final_design/app.py" would overwrite this very file), and "../"
    segments walk out of the directory. secure_filename() strips both, and the
    containment re-check catches anything it lets through.
    """
    safe_filename = secure_filename(filename or "")
    if not safe_filename:
        return None, "invalid_filename"

    resolved_base = Path(base_dir).resolve()
    candidate = (resolved_base / safe_filename).resolve()
    if resolved_base != candidate.parent and resolved_base not in candidate.parents:
        return None, "invalid_file_path"

    return candidate, None

@app.route('/list-objects', methods=['GET'])
@limiter.limit("30 per minute")
def list_objects():
    prefix = request.args.get('prefix') or ""
    object_paths = storage.list_objects(prefix=prefix)
    return jsonify(object_paths)

@app.route('/folder-exists', methods=['GET'])
@limiter.limit("60 per minute")
def check_folder_exists():
    path = request.args.get('path')
    exists = storage.folder_exists(path)
    return jsonify({'exists': exists})

@app.route('/create-user-folder', methods=['POST'])
@limiter.limit("30 per minute")
def create_user_folder():
    user_id = request.json.get('user_id')
    storage.create_user_folder(user_id)
    return jsonify({'status': 'created'})

@app.route('/create-today-folder', methods=['POST'])
@limiter.limit("30 per minute")
def create_today_folder():
    user_id = request.json.get('user_id')
    storage.create_today_folders(user_id)
    return jsonify({'status': 'created'})

@app.route('/add-file', methods=['POST'])
@limiter.limit("30 per minute")
def upload_file():
    try:
        user_id = request.form.get('user_id')
        file = request.files.get('file')
        is_annotated_str = request.form.get('is_annotated')

        if not user_id or not file or not is_annotated_str:
            return jsonify({'error': 'user_id, is_annotated, and file are required'}), 400

        # Use a valid temp directory. The staging path is derived from the
        # sanitized name, never from the raw one.
        temp_path_obj, path_error = _safe_upload_path(tempfile.gettempdir(), file.filename)
        if path_error:
            return jsonify({'error': path_error}), 400

        temp_path = str(temp_path_obj)
        safe_filename = temp_path_obj.name
        file.save(temp_path)

        # Convert string to boolean for the storage provider
        is_annotated = is_annotated_str.lower() == "true"
        storage.add_file(safe_filename, temp_path, user_id, is_annotated)

        return jsonify({'status': 'uploaded', 'file': safe_filename}), 200
    except Exception as e:
        app.logger.error(f"Error uploading file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-file-url', methods=['GET'])
@limiter.limit("60 per minute")
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
@limiter.limit("60 per minute")
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
@limiter.limit("30 per minute")
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
@limiter.limit("6 per minute; 60 per hour")
def generate_ai_predictions():
    try:
        user_id = request.form.get("user_id")
        file = request.files.get("file")

        if not (user_id and file):
            return jsonify({"status": "error", "message": "user_id_and_file_required"}), 400

        # 1) Save the image supplied in the request to a local temp file.
        #    The image is processed in-place and never stored in the cloud.
        local_dir = constants.TEMP_FOLDER_RAW_PATH
        os.makedirs(local_dir, exist_ok=True)
        local_path_obj, path_error = _safe_upload_path(local_dir, file.filename)
        if path_error:
            return jsonify({"status": "error", "message": path_error}), 400

        local_path = str(local_path_obj)
        file.save(local_path)

        # 2) Run the CNN ensemble on the image
        result = generate_final_image(local_path)
        if not result or "label" not in result:
            return jsonify({"status": "error", "message": "ai_prediction_generation_failed"}), 500

        label = result["label"]
        confidence = result.get("confidence")

        # Clean up temp folder
        try:
            shutil.rmtree(constants.TEMP_FOLDER_PATH)
            app.logger.info(f"Temp folder cleaned up")
        except OSError as e:
            app.logger.warning(f"Error deleting temp folder: {e}")

        return jsonify({
            "status": "ok",
            # generate_final_image returns the top-3 classes; expose the top
            # prediction as `label` and the full ranked list as `labels`.
            "label": label[0] if isinstance(label, list) and label else label,
            "labels": label,
            "confidence": confidence,
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

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

if __name__ == "__main__":
    # Configuration via environment variables (secure for production)
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')  # 0.0.0.0 for containers
    port = int(os.environ.get('FLASK_PORT', '5000'))

    app.logger.info(f"Starting server on {host}:{port} (debug={debug_mode})")
    app.run(host=host, port=port, debug=debug_mode, use_reloader=False)