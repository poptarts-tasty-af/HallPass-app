import os
from flask import Flask, render_template, request, jsonify
from pyzxing import BarCodeReader
from datetime import datetime

app = Flask(__name__)

# Initialize the BarCodeReader
reader = BarCodeReader()

# Set the path for file uploads
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file extensions for security
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check if the file is an allowed image type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to display the QR code scan page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle the scanning process
@app.route('/scan', methods=['POST'])
def scan_qr_code():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    # Save the uploaded image to a temporary location
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'scanned_qr.png')
    file.save(file_path)

    # Use pyzxing to decode the QR code from the image
    result = reader.decode(file_path)

    if not result or 'parsed' not in result[0]:
        return jsonify({'error': 'No QR code found'}), 400

    # Extract the URL from the decoded QR code
    qr_data = result[0]['parsed']

    # Parse the URL parameters (you can improve this to handle multiple QR codes)
    try:
        url_params = dict(param.split('=') for param in qr_data.split('?')[1].split('&'))
    except IndexError:
        return jsonify({'error': 'QR code is malformed'}), 400

    teacher = url_params.get('teacher', 'Unknown')
    classroom = url_params.get('classroom', 'Unknown')
    timestamp = url_params.get('timestamp', '0')

    # Convert timestamp to a human-readable date
    try:
        scan_time = datetime.utcfromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        scan_time = 'Invalid timestamp'

    # Return the scanned data and time
    return render_template('scan_result.html', teacher=teacher, classroom=classroom, timestamp=scan_time)

if __name__ == '__main__':
    context = ('cert.pem', 'key.pem')  # Path to your cert and key files
    app.run(host='0.0.0.0', port=8000, debug=True)

