import os
import tempfile
from flask import Flask, request, jsonify
from lib.aws_storage import aws_s3 as s3

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)