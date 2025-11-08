from flask import Flask, render_template, request, jsonify, redirect, url_for
import threading
import time
from datetime import datetime, timedelta
import requests
from database import Database
from distance_utils import EyeDistanceMonitor
from session_monitor import SessionMonitor

app = Flask(__name__)

# Configuration
ESP32_IP = "192.168.1.100"  # Replace with actual ESP32 IP
ESP32_PORT = 80
BREAK_REMINDER_MINUTES = 45
SAFE_DISTANCE_CM = 50

# Global variables
db = Database()
eye_monitor = None
session_monitor = None
current_session = None
is_working = False

class WorkSession:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.distances = []
        self.break_warnings = 0
        self.last_break_warning = None

    def start(self):
        self.start_time = datetime.now()
        self.distances = []
        self.break_warnings = 0
        self.last_break_warning = None

    def stop(self):
        self.end_time = datetime.now()

    def add_distance(self, distance):
        self.distances.append({
            'distance': distance,
            'timestamp': datetime.now()
        })

    def get_average_distance(self):
        if not self.distances:
            return 0
        return sum(d['distance'] for d in self.distances) / len(self.distances)

    def get_work_duration(self):
        if not self.start_time:
            return 0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_work', methods=['POST'])
def start_work():
    global current_session, is_working, eye_monitor, session_monitor

    if is_working:
        return jsonify({'error': 'Already working'})

    # Start a new work session
    current_session = WorkSession()
    current_session.start()
    is_working = True

    # Start camera monitor
    try:
        eye_monitor = EyeDistanceMonitor(on_distance_update=on_distance_update)
        eye_monitor.start()

        # Start session monitor for break reminders
        session_monitor = SessionMonitor(
            break_interval=BREAK_REMINDER_MINUTES * 60,
            on_break_reminder=on_break_reminder
        )
        session_monitor.start()

        return jsonify({
            'success': True,
            'message': 'Work session started',
            'start_time': current_session.start_time.strftime('%H:%M:%S')
        })
    except Exception as e:
        is_working = False
        return jsonify({'error': f'Failed to start camera: {str(e)}'})

@app.route('/stop_work', methods=['POST'])
def stop_work():
    global current_session, is_working, eye_monitor, session_monitor

    if not is_working:
        return jsonify({'error': 'Not working'})

    # Stop monitoring
    if eye_monitor:
        eye_monitor.stop()
        eye_monitor = None

    if session_monitor:
        session_monitor.stop()
        session_monitor = None

    # End work session
    current_session.stop()
    is_working = False

    # Save to database
    work_duration = current_session.get_work_duration()
    avg_distance = current_session.get_average_distance()

    session_id = db.save_work_session(
        start_time=current_session.start_time,
        end_time=current_session.end_time,
        duration=work_duration,
        avg_distance=avg_distance,
        break_warnings=current_session.break_warnings
    )

    return jsonify({
        'success': True,
        'message': 'Work session stopped',
        'duration': f'{int(work_duration // 60)}:{int(work_duration % 60):02d}',
        'avg_distance': f'{avg_distance:.1f}cm',
        'break_warnings': current_session.break_warnings
    })

@app.route('/current_status')
def current_status():
    if not is_working or not current_session:
        return jsonify({'working': False})

    duration = current_session.get_work_duration()
    avg_distance = current_session.get_average_distance()

    return jsonify({
        'working': True,
        'start_time': current_session.start_time.strftime('%H:%M:%S'),
        'duration': f'{int(duration // 60)}:{int(duration % 60):02d}',
        'avg_distance': f'{avg_distance:.1f}cm' if avg_distance > 0 else 'N/A',
        'total_measurements': len(current_session.distances),
        'break_warnings': current_session.break_warnings
    })

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/api/history')
def api_history():
    today = datetime.now().date()
    sessions = db.get_sessions_by_date(today)

    history_data = []
    for session in sessions:
        history_data.append({
            'id': session[0],
            'start_time': session[1],
            'end_time': session[2],
            'duration': format_duration(session[3]),
            'avg_distance': f'{session[4]:.1f}cm',
            'break_warnings': session[5],
            'distance_warning': session[4] < SAFE_DISTANCE_CM
        })

    return jsonify(history_data)

@app.route('/check_distance')
def check_distance():
    """API endpoint to check current eye distance"""
    if not is_working or not current_session or not current_session.distances:
        return jsonify({'distance': 0, 'warning': False})

    # Get latest distance
    latest_distance = current_session.distances[-1]['distance']

    return jsonify({
        'distance': latest_distance,
        'warning': latest_distance < SAFE_DISTANCE_CM
    })

def on_distance_update(distance):
    """Callback when new eye distance data is available"""
    global current_session

    if current_session and is_working:
        current_session.add_distance(distance)

        # Send warning to ESP32 if too close
        if distance < SAFE_DISTANCE_CM:
            send_warning_to_esp32(distance, True)
        else:
            send_warning_to_esp32(distance, False)

def on_break_reminder():
    """Callback for break reminder"""
    global current_session

    if current_session and is_working:
        current_session.break_warnings += 1
        current_session.last_break_warning = datetime.now()

        # Send break reminder to ESP32
        send_break_reminder_to_esp32()

def send_warning_to_esp32(distance, is_warning):
    """Send eye distance warning to ESP32"""
    try:
        url = f"http://{ESP32_IP}:{ESP32_PORT}/distance_warning"
        data = {
            'distance': int(distance),
            'warning': is_warning
        }
        requests.post(url, json=data, timeout=1)
    except Exception as e:
        print(f"Error sending distance warning to ESP32: {e}")

def send_break_reminder_to_esp32():
    """Send break reminder to ESP32"""
    try:
        url = f"http://{ESP32_IP}:{ESP32_PORT}/break_reminder"
        requests.post(url, timeout=1)
    except Exception as e:
        print(f"Error sending break reminder to ESP32: {e}")

def format_duration(seconds):
    """Format seconds to HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

if __name__ == '__main__':
    # Initialize database
    db.init_db()

    # Run Flask server
    app.run(host='0.0.0.0', port=5000, debug=True)