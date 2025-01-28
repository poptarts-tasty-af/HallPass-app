import os
import json
import json
from flask import Flask, render_template, request, jsonify
from pyzxing import BarCodeReader
from datetime import datetime

app = Flask(__name__)

BASE_UPLOAD_FOLDER = 'hallpasses'
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)

BASE_UPLOAD_FOLDER = 'hallpasses'
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)

reader = BarCodeReader()

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CURRENT_STATUS_FOLDER = 'Current_Status'
os.makedirs(CURRENT_STATUS_FOLDER, exist_ok=True)

STUDENTS_FILE_PATH = os.path.join(CURRENT_STATUS_FOLDER, 'students.json')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_student_status():
    if os.path.exists(STUDENTS_FILE_PATH):
        try:
            with open(STUDENTS_FILE_PATH, 'r') as file:
                if file.read():
                    file.seek(0)
                    return json.load(file)
                else:
                    return {}
        except json.JSONDecodeError:
            print(f"Error: JSON in {STUDENTS_FILE_PATH} is corrupted.")
            return {}
    return {}

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

def save_hallpass_data(student_number, data):
    today_date = datetime.now().strftime('%m-%d-%Y')
    date_folder = os.path.join(BASE_UPLOAD_FOLDER, today_date)
    os.makedirs(date_folder, exist_ok=True)
    file_path = os.path.join(date_folder, f'{student_number}.json')

    # Check if the file exists
    if os.path.exists(file_path):
        with open(file_path, 'r') as json_file:
            try:
                # Attempt to load the existing data
                existing_data = json.load(json_file)

                # If the existing data is not a list, make it a list
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]
            except json.JSONDecodeError:
                # If JSON is corrupted or empty, initialize as an empty list
                existing_data = []
    else:
        # If the file doesn't exist, initialize it as an empty list
        existing_data = []

    # Append the new data to the existing data
    existing_data.append(data)

    # Save the updated data back to the file
    with open(file_path, 'w') as json_file:
        json.dump(existing_data, json_file, indent=4)

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

    # Read the existing student status from the students.json file
    student_status = read_student_status()

    if arrival_departure == 'departure':
        # Add the student to the status as 'departed'
        student_status[student_number] = 'departed'

        # Save the updated student status
        save_student_status(student_status)

        # Save the hallpass data for the departure
        save_hallpass_data(student_number, {
            'teacherName': teacher_name,
            'teacherRoom': teacher_room,
            'departureTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'qrScanData': qr_scan_data
        })
        
    elif arrival_departure == 'arrival':
        # Remove the student from the status if they are arriving
        if student_number in student_status:
            del student_status[student_number]
            # Save the updated student status after removal
            save_student_status(student_status)

        # Save the hallpass data for the arrival
        save_hallpass_data(student_number, {
            'teacherName': teacher_name,
            'teacherRoom': teacher_room,
            'arrivalTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'qrScanData': qr_scan_data
        })

    return jsonify({"status": "success", "message": "Hall pass data saved."})

if __name__ == '__main__':
    context = ('cert.pem', 'key.pem')
    context = ('cert.pem', 'key.pem')
    app.run(host='0.0.0.0', port=8000, debug=True)
