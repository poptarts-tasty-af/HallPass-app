import os
import time
from flask import Flask, render_template, request
import cv2
from pyzbar.pyzbar import decode
from datetime import datetime

app = Flask(__name__)

# Route to display the QR code scan page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle the scanning process
@app.route('/scan', methods=['POST'])
def scan_qr_code():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    # Save the uploaded image to a temporary location
    file_path = os.path.join('uploads', 'scanned_qr.png')
    file.save(file_path)

    # Read the image using OpenCV
    img = cv2.imread(file_path)

    # Decode QR code(s) from the image
    decoded_objects = decode(img)

    if len(decoded_objects) == 0:
        return "No QR code found", 400

    # Extract the URL from the decoded QR code
    qr_data = decoded_objects[0].data.decode('utf-8')

    # Parse the URL parameters (you can improve this to handle multiple QR codes)
    url_params = dict(param.split('=') for param in qr_data.split('?')[1].split('&'))

    teacher = url_params.get('teacher', 'Unknown')
    classroom = url_params.get('classroom', 'Unknown')
    timestamp = url_params.get('timestamp', '0')

    # Convert timestamp to a human-readable date
    scan_time = datetime.utcfromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

    # Return the scanned data and time
    return render_template('scan_result.html', teacher=teacher, classroom=classroom, timestamp=scan_time)

if __name__ == '__main__':
    # Create directories for uploads and static files if they don't exist
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)