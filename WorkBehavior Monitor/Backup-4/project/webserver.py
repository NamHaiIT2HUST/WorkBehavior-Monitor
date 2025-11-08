from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
from distance_utils import DistanceCamera
import atexit

app = Flask(__name__)

DB_PATH = 'work_sessions.db'
SAFE_DISTANCE_CM = 50

# Khởi tạo camera
camera = DistanceCamera(cam_id=0, safe_distance=SAFE_DISTANCE_CM)

def init_db():
    """Khởi tạo database"""
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

# Biến lưu trữ session hiện tại
current_session = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/api/history')
def api_history():
    """API lấy lịch sử làm việc"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sessions ORDER BY start_time DESC')
    sessions = cursor.fetchall()
    conn.close()
    
    history_data = []
    for s in sessions:
        history_data.append({
            'id': s[0],
            'start_time': s[1],
            'end_time': s[2] if s[2] else '',
            'duration': s[3] if s[3] else '',
            'avg_distance': s[4] if s[4] else '0cm',
            'break_warnings': s[5] if s[5] else 0,
            'distance_warning': bool(s[6]) if s[6] is not None else False
        })
    
    return jsonify(history_data)

@app.route('/start_work', methods=['POST'])
def start_work():
    """Bắt đầu phiên làm việc"""
    global current_session
    
    if current_session is not None:
        return jsonify({'success': False, 'error': 'Work session already started'})
    
    # Tạo session mới
    current_session = {
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'distances': [],
        'break_warnings': 0
    }
    
    # Bắt đầu giám sát camera
    try:
        camera.start_monitoring(server_url="http://localhost:5000", interval=3)
        print("🎥 Bắt đầu giám sát camera")
    except Exception as e:
        print(f"⚠️ Không thể khởi động camera: {e}")
    
    return jsonify({
        'success': True, 
        'start_time': current_session['start_time']
    })

@app.route('/stop_work', methods=['POST'])
def stop_work():
    """Kết thúc phiên làm việc"""
    global current_session
    
    if current_session is None:
        return jsonify({'success': False, 'error': 'No active work session'})
    
    # Dừng giám sát camera
    camera.stop_monitoring()
    print("🔚 Dừng giám sát camera")
    
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Tính toán duration
    start_dt = datetime.strptime(current_session['start_time'], '%Y-%m-%d %H:%M:%S')
    end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    duration_seconds = (end_dt - start_dt).total_seconds()
    
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    
    # Tính toán average distance
    avg_distance = 0
    if current_session['distances']:
        avg_distance = sum(current_session['distances']) / len(current_session['distances'])
    
    avg_distance_str = f"{avg_distance:.1f}cm"
    
    # Kiểm tra distance warning
    distance_warning = any(d < SAFE_DISTANCE_CM for d in current_session['distances'])
    
    # Lưu vào database
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
    
    # Reset session
    current_session = None
    
    return jsonify(result)

@app.route('/add_distance', methods=['POST'])
def add_distance():
    """Thêm dữ liệu khoảng cách từ camera"""
    global current_session
    
    if current_session is None:
        return jsonify({'success': False, 'error': 'No active session'})
    
    data = request.get_json()
    distance = data.get('distance')
    
    if distance is not None and distance > 0:
        current_session['distances'].append(float(distance))
        print(f"📊 Nhận dữ liệu khoảng cách: {distance:.1f}cm")
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid distance data'})

@app.route('/add_break_warning', methods=['POST'])
def add_break_warning():
    """Thêm cảnh báo nghỉ giải lao"""
    global current_session
    
    if current_session is None:
        return jsonify({'success': False, 'error': 'No active session'})
    
    current_session['break_warnings'] += 1
    print(f"⚠️ Cảnh báo nghỉ giải lao #{current_session['break_warnings']}")
    
    return jsonify({'success': True, 'warning_count': current_session['break_warnings']})

@app.route('/check_distance')
def check_distance():
    """Kiểm tra khoảng cách hiện tại"""
    global current_session
    
    try:
        too_close, distance = camera.is_too_close()
        
        # Nếu có session đang hoạt động, lưu dữ liệu
        if current_session and distance > 0:
            current_session['distances'].append(distance)
        
        return jsonify({
            'distance': distance,
            'warning': too_close,
            'safe_distance': SAFE_DISTANCE_CM
        })
    
    except Exception as e:
        print(f"❌ Lỗi kiểm tra khoảng cách: {e}")
        return jsonify({
            'distance': 0,
            'warning': False,
            'error': str(e)
        })

@app.route('/api/current_session')
def current_session_info():
    """Lấy thông tin session hiện tại"""
    global current_session
    
    if current_session is None:
        return jsonify({'active': False})
    
    return jsonify({
        'active': True,
        'start_time': current_session['start_time'],
        'distance_count': len(current_session['distances']),
        'break_warnings': current_session['break_warnings'],
        'avg_distance': sum(current_session['distances']) / len(current_session['distances']) if current_session['distances'] else 0
    })

@app.route('/api/save_distance_image')
def save_distance_image():
    """Lưu ảnh với thông tin khoảng cách"""
    try:
        success, message = camera.save_image_with_distance("./static/images/")
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Lỗi: {str(e)}"
        })

# Cleanup khi tắt server
def cleanup():
    """Dọn dẹp khi tắt server"""
    print("🔚 Đang dọn dẹp...")
    camera.stop_monitoring()
    camera.stop_camera()

atexit.register(cleanup)

if __name__ == '__main__':
    print("🚀 Khởi động Work Session Monitor...")
    
    # Khởi tạo database
    init_db()
    
    # Tạo thư mục lưu ảnh nếu chưa có
    import os
    os.makedirs("./static/images/", exist_ok=True)
    
    print("✅ Hệ thống sẵn sàng!")
    print("📱 Truy cập: http://localhost:5000")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("⏹️ Dừng server...")
        cleanup()