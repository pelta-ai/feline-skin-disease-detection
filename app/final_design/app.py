import os, sys
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify
from lib.aws_storage import aws_s3 as s3

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_DIR))

from src.generate_final_image import generate_final_image
import src.utils.constants as constants

app = Flask(__name__)

@app.route('/list-objects', methods=['GET'])
def list_objects():
    prefix = request.args.get('prefix')
    object_paths = s3.list_object_paths(prefix=prefix)
    return jsonify(object_paths)

@app.route('/folder-exists', methods=['GET'])
def check_folder_exists():
    path = request.args.get('path')
    exists = s3.folder_exists(path)
    return jsonify({'exists': exists})

@app.route('/create-user-folder', methods=['POST'])
def create_user_folder():
    user_id = request.json.get('user_id')
    s3.create_user_folder(user_id)
    return jsonify({'status': 'created'})

@app.route('/create-today-folder', methods=['POST'])
def create_today_folder():
    user_id = request.json.get('user_id')
    s3.create_today_folder(user_id)
    return jsonify({'status': 'created'})

@app.route('/add-file', methods=['POST'])
def upload_file():
    try:
        user_id = request.form.get('user_id')
        file = request.files.get('file')

        if not user_id or not file:
            return jsonify({'error': 'user_id and file are required'}), 400

        # Use a valid temp directory
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)

        s3.add_file(file.filename, temp_path, user_id)

        return jsonify({'status': 'uploaded', 'file': file.filename}), 200
    except Exception as e:
        print(f"Error uploading file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-file-url', methods=['GET'])
def get_file_url():
    try:
        path = request.args.get('path')
        if not path:
            return jsonify({'error': 'Path is required'}), 400
        
        url = s3.get_file_url(path)
        return jsonify({'url': url})
    except Exception as e:
        print(f"Error generating URL: {e}")
        return jsonify({'error': str(e)}), 500
    
@app.post("/download-file")
def download_from_s3_api():
    #user_id = request.form["user_id"]    
    file_name = request.form["file_name"]
    s3_key = request.form["s3_key"]      

    local_path = s3.download_file(file_name, s3_key)

    if not local_path:
        return jsonify({"status": "error", "message": "download_failed"}), 500

    return jsonify({"status": "ok", "local_path": local_path}), 200

@app.get("/get-today-date")
def get_today_date_api():
    return {"date": s3.get_today_date()}

@app.post("/generate-ai-predictions")
def generate_ai_predictions():
    raw_files = os.listdir(constants.TEMP_FOLDER_RAW_PATH)
    if not raw_files:
        return jsonify({"status": "error", "message": "ai_prediction_generation_failed"}), 500
    
    raw_image = os.path.join(constants.TEMP_FOLDER_RAW_PATH, raw_files[0])
    if not raw_image:
        return jsonify({"status": "error", "message": "ai_prediction_generation_failed"}), 500
    
    label = generate_final_image(raw_image)
    if not label:
        return jsonify({"status": "error", "message": "ai_prediction_generation_failed"}), 500
    
    annotated_files = os.listdir(constants.TEMP_FOLDER_ANNOTATED_PATH)
    if not annotated_files:
        return jsonify({"status": "error", "message": "ai_prediction_generation_failed"}), 500
    
    annotated_image_path = os.path.join(constants.TEMP_FOLDER_ANNOTATED_PATH, annotated_files[0])
    
    return jsonify({"status": "ok", "label": label, "annotated_image_path": annotated_image_path}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)