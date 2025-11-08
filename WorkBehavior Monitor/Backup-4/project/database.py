import sqlite3
import os
from datetime import datetime, date
from contextlib import contextmanager

class Database:
    def __init__(self, db_path='work_monitor.db'):
        self.db_path = db_path
        
    def init_db(self):
        """Khởi tạo cơ sở dữ liệu và tạo bảng"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Bảng work_sessions: lưu thông tin phiên làm việc
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS work_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration INTEGER,  -- thời gian làm việc (giây)
                    avg_distance REAL,  -- khoảng cách trung bình (cm)
                    break_warnings INTEGER DEFAULT 0,  -- số lần nhắc nghỉ
                    created_date DATE DEFAULT CURRENT_DATE
                )
            ''')
            
            # Bảng distance_logs: lưu chi tiết khoảng cách theo thời gian
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS distance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    distance REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES work_sessions (id)
                )
            ''')
            
            # Bảng user_settings: cài đặt người dùng
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_name TEXT UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print("Database initialized successfully")
    
    @contextmanager
    def get_connection(self):
        """Context manager untuk kết nối database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Cho phép truy cập column bằng tên
        try:
            yield conn
        finally:
            conn.close()
    
    def save_work_session(self, start_time, end_time, duration, avg_distance, break_warnings=0):
        """Lưu phiên làm việc vào database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO work_sessions 
                (start_time, end_time, duration, avg_distance, break_warnings, created_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (start_time, end_time, duration, avg_distance, break_warnings, date.today()))
            
            session_id = cursor.lastrowid
            conn.commit()
            return session_id
    
    def save_distance_log(self, session_id, distance, timestamp=None):
        """Lưu log khoảng cách chi tiết"""
        if timestamp is None:
            timestamp = datetime.now()
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO distance_logs (session_id, distance, timestamp)
                VALUES (?, ?, ?)
            ''', (session_id, distance, timestamp))
            conn.commit()
    
    def get_sessions_by_date(self, target_date):
        """Lấy tất cả phiên làm việc trong ngày"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, start_time, end_time, duration, avg_distance, break_warnings
                FROM work_sessions
                WHERE created_date = ?
                ORDER BY start_time DESC
            ''', (target_date,))
            return cursor.fetchall()
    
    def get_session_details(self, session_id):
        """Lấy chi tiết một phiên làm việc"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM work_sessions WHERE id = ?
            ''', (session_id,))
            session = cursor.fetchone()
            
            if session:
                # Lấy thêm distance logs
                cursor.execute('''
                    SELECT distance, timestamp FROM distance_logs
                    WHERE session_id = ?
                    ORDER BY timestamp
                ''', (session_id,))
                distance_logs = cursor.fetchall()
                
                return {
                    'session': dict(session),
                    'distance_logs': [dict(log) for log in distance_logs]
                }
            return None
    
    def get_weekly_summary(self, start_date, end_date):
        """Lấy tổng kết tuần"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    DATE(created_date) as work_date,
                    COUNT(*) as session_count,
                    SUM(duration) as total_duration,
                    AVG(avg_distance) as avg_distance,
                    SUM(break_warnings) as total_warnings
                FROM work_sessions
                WHERE created_date BETWEEN ? AND ?
                GROUP BY DATE(created_date)
                ORDER BY created_date
            ''', (start_date, end_date))
            return cursor.fetchall()
    
    def get_distance_trend(self, days=7):
        """Lấy xu hướng khoảng cách trong N ngày gần nhất"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    DATE(created_date) as work_date,
                    AVG(avg_distance) as avg_distance,
                    MIN(avg_distance) as min_distance,
                    MAX(avg_distance) as max_distance
                FROM work_sessions
                WHERE created_date >= date('now', '-' || ? || ' days')
                GROUP BY DATE(created_date)
                ORDER BY created_date
            ''', (days,))
            return cursor.fetchall()
    
    def get_today_stats(self):
        """Lấy thống kê hôm nay"""
        today = date.today()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as session_count,
                    SUM(duration) as total_duration,
                    AVG(avg_distance) as avg_distance,
                    SUM(break_warnings) as total_warnings,
                    MIN(avg_distance) as min_distance,
                    MAX(avg_distance) as max_distance
                FROM work_sessions
                WHERE created_date = ?
            ''', (today,))
            return cursor.fetchone()
    
    def update_setting(self, setting_name, setting_value):
        """Cập nhật cài đặt người dùng"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_settings (setting_name, setting_value, updated_at)
                VALUES (?, ?, ?)
            ''', (setting_name, setting_value, datetime.now()))
            conn.commit()
    
    def get_setting(self, setting_name, default_value=None):
        """Lấy cài đặt người dùng"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT setting_value FROM user_settings WHERE setting_name = ?
            ''', (setting_name,))
            result = cursor.fetchone()
            return result[0] if result else default_value
    
    def delete_session(self, session_id):
        """Xóa phiên làm việc"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Xóa distance logs trước
            cursor.execute('DELETE FROM distance_logs WHERE session_id = ?', (session_id,))
            # Xóa session
            cursor.execute('DELETE FROM work_sessions WHERE id = ?', (session_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def cleanup_old_data(self, days_to_keep=30):
        """Dọn dẹp dữ liệu cũ"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM work_sessions 
                WHERE created_date < date('now', '-' || ? || ' days')
            ''', (days_to_keep,))
            deleted_sessions = cursor.rowcount
            
            cursor.execute('''
                DELETE FROM distance_logs 
                WHERE session_id NOT IN (SELECT id FROM work_sessions)
            ''')
            deleted_logs = cursor.rowcount
            
            conn.commit()
            return deleted_sessions, deleted_logs

# Utility functions
def format_duration(seconds):
    """Định dạng thời gian từ giây"""
    if seconds is None:
        return "00:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def get_work_quality_score(avg_distance, break_warnings, duration):
    """Tính điểm chất lượng làm việc"""
    score = 100
    
    # Trừ điểm nếu khoảng cách không đạt
    if avg_distance < 40:
        score -= 30
    elif avg_distance < 50:
        score -= 15
    elif avg_distance > 80:
        score -= 10
    
    # Trừ điểm nếu có nhiều cảnh báo nghỉ
    score -= min(break_warnings * 10, 40)
    
    # Cộng điểm nếu làm việc đủ lâu
    if duration >= 3600:  # >= 1 giờ
        score += 10
    
    return max(0, min(100, score))

if __name__ == '__main__':
    # Test database
    db = Database()
    db.init_db()
    print("Database setup completed!")