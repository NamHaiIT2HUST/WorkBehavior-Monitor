from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
from distance_utils import DistanceCamera  

app = Flask(__name__)

DB_PATH = 'work_sessions.db'
SAFE_DISTANCE_CM = 50

camera = DistanceCamera(cam_id=0)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration TEXT,
            avg_distance TEXT,
            break_warnings INTEGER DEFAULT 0,
            distance_warning BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

current_session = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/api/history')
def api_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sessions ORDER BY id DESC')
    sessions = cursor.fetchall()
    conn.close()
    history_data = []
    for s in sessions:
        history_data.append({
            'id': s[0],
            'start_time': s[1],
            'end_time': s[2],
            'duration': s[3],
            'avg_distance': s[4],
            'break_warnings': s[5],
            'distance_warning': bool(s[6])
        })
    return jsonify(history_data)

@app.route('/start_work', methods=['POST'])
def start_work():
    global current_session
    if current_session is not None:
        return jsonify({'success': False, 'error': 'Work session already started'})
    current_session = {
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'distances': [],
        'break_warnings': 0
    }
    return jsonify({'success': True, 'start_time': current_session['start_time']})

@app.route('/stop_work', methods=['POST'])
def stop_work():
    global current_session
    if current_session is None:
        return jsonify({'success': False, 'error': 'No active work session'})
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    start_dt = datetime.strptime(current_session['start_time'], '%Y-%m-%d %H:%M:%S')
    end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    duration_seconds = (end_dt - start_dt).total_seconds()
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    avg_distance = 0
    if current_session['distances']:
        avg_distance = sum(current_session['distances']) / len(current_session['distances'])
    avg_distance_str = f"{avg_distance:.1f}cm"
    distance_warning = any(d < SAFE_DISTANCE_CM for d in current_session['distances'])
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sessions (start_time, end_time, duration, avg_distance, break_warnings, distance_warning)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_session['start_time'], end_time, duration_str, avg_distance_str,
          current_session['break_warnings'], distance_warning))
    conn.commit()
    conn.close()
    result = {
        'success': True,
        'duration': duration_str,
        'avg_distance': avg_distance_str,
        'break_warnings': current_session['break_warnings'],
        'distance_warning': distance_warning
    }
    current_session = None
    return jsonify(result)

@app.route('/add_distance', methods=['POST'])
def add_distance():
    global current_session
    if current_session is None:
        return jsonify({'success': False, 'error': 'No active session'})
    data = request.get_json()
    distance = data.get('distance')
    if distance is not None:
        current_session['distances'].append(float(distance))
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'No distance provided'})

@app.route('/add_break_warning', methods=['POST'])
def add_break_warning():
    global current_session
    if current_session is None:
        return jsonify({'success': False, 'error': 'No active session'})
    current_session['break_warnings'] += 1
    return jsonify({'success': True})

@app.route('/check_distance')
def check_distance():
    global current_session
    too_close, distance = camera.is_too_close()
    if current_session and distance > 0:
        current_session['distances'].append(distance)
    return jsonify({
        'distance': distance,
        'warning': too_close
    })

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)