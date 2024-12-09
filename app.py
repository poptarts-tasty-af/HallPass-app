import os
import json
from flask import Flask, render_template, request, jsonify
from pyzxing import BarCodeReader
from datetime import datetime

app = Flask(__name__)

BASE_UPLOAD_FOLDER = 'hallpasses'
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)

reader = BarCodeReader()

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CURRENT_STATUS_FOLDER = 'Current_Status'
os.makedirs(CURRENT_STATUS_FOLDER, exist_ok=True)

STUDENTS_FILE_PATH = os.path.join(CURRENT_STATUS_FOLDER, 'students.json')


# Allowed file extensions for QR code image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check if a file extension is valid
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Read student status from students.json
def read_student_status():
    if os.path.exists(STUDENTS_FILE_PATH):
        with open(STUDENTS_FILE_PATH, 'r') as file:
            return json.load(file)
    return {}

# Save student status to students.json
def save_student_status(student_status):
    with open(STUDENTS_FILE_PATH, 'w') as file:
        json.dump(student_status, file, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan_qr_code():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'scanned_qr.png')
    file.save(file_path)

    result = reader.decode(file_path)

    if not result or 'parsed' not in result[0]:
        return jsonify({'error': 'No QR code found'}), 400

    qr_data = result[0]['parsed']

    try:
        url_params = dict(param.split('=') for param in qr_data.split('?')[1].split('&'))
    except IndexError:
        return jsonify({'error': 'QR code is malformed'}), 400

    teacher = url_params.get('teacher', 'Unknown')
    classroom = url_params.get('classroom', 'Unknown')
    timestamp = url_params.get('timestamp', '0')

    try:
        scan_time = datetime.utcfromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        scan_time = 'Invalid timestamp'

    return render_template('scan_result.html', teacher=teacher, classroom=classroom, timestamp=scan_time)

# Function to handle hall pass data and update the student status
def save_hallpass_data(student_number, data):
    today_date = datetime.now().strftime('%m-%d-%Y')
    date_folder = os.path.join(BASE_UPLOAD_FOLDER, today_date)
    os.makedirs(date_folder, exist_ok=True)
    file_path = os.path.join(date_folder, f'{student_number}.json')

    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

@app.route('/submit', methods=['POST'])
def submit_hallpass():
    data = request.get_json()

    student_number = data.get('studentNumber')
    teacher_name = data.get('teacherName')
    teacher_room = data.get('teacherRoom')
    arrival_departure = data.get('arrivalDeparture')
    qr_scan_data = data.get('qrScanData')

    hallpass_data = {
        'qrScanData': qr_scan_data,
        'arrivalDeparture': arrival_departure,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Handle the arrival or departure logic
    student_status = read_student_status()

    if arrival_departure == 'departure':
        # Add the student number to the departure list
        student_status[student_number] = 'departed'
    elif arrival_departure == 'arrival':
        # Remove the student number from the departure list
        if student_number in student_status:
            del student_status[student_number]

    # Save updated student status
    save_student_status(student_status)

    # Save hall pass data
    save_hallpass_data(student_number, hallpass_data)

    return jsonify({"status": "success", "message": "Hall pass data saved."})


if __name__ == '__main__':
    context = ('cert.pem', 'key.pem')
    app.run(host='0.0.0.0', port=8000, debug=True)
