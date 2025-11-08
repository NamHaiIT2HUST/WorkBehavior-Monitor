import cv2
import mediapipe as mp
import time
import requests
import threading
from datetime import datetime

class DistanceCamera:
    def __init__(self, cam_id=0, focal_length=840, real_eye_distance=6.3, safe_distance=50):
        """
        Khởi tạo camera đo khoảng cách
        
        Args:
            cam_id: ID của camera (mặc định 0)
            focal_length: Tiêu cự ảo của camera
            real_eye_distance: Khoảng cách thực giữa hai mắt (cm)
            safe_distance: Khoảng cách an toàn tối thiểu (cm)
        """
        self.cam_id = cam_id
        self.focal_length = focal_length
        self.real_eye_distance = real_eye_distance
        self.safe_distance = safe_distance
        
        # Khởi tạo Face Mesh từ Mediapipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False, 
            max_num_faces=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # Khởi tạo camera
        self.cap = None
        self.is_monitoring = False
        self.monitoring_thread = None
        self.last_distance = 0
        
    def start_camera(self):
        """Khởi động camera"""
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.cam_id)
            if not self.cap.isOpened():
                raise Exception(f"Không thể mở camera {self.cam_id}")
        return True
    
    def stop_camera(self):
        """Dừng camera"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def get_distance(self):
        """
        Đo khoảng cách một lần
        
        Returns:
            tuple: (distance_cm, success)
        """
        if not self.start_camera():
            return 0, False
        
        ret, frame = self.cap.read()
        if not ret:
            return 0, False
        
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if results.multi_face_landmarks:
            for face in results.multi_face_landmarks:
                # Mắt trái: landmark 33, mắt phải: 263
                left_eye = face.landmark[33]
                right_eye = face.landmark[263]
                
                x1 = int(left_eye.x * w)
                y1 = int(left_eye.y * h)
                x2 = int(right_eye.x * w)
                y2 = int(right_eye.y * h)
                
                # Tính khoảng cách pixel giữa 2 mắt
                pixel_distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                
                if pixel_distance > 0:
                    distance_cm = (self.real_eye_distance * self.focal_length) / pixel_distance
                    self.last_distance = distance_cm
                    return distance_cm, True
        
        return 0, False
    
    def is_too_close(self):
        """
        Kiểm tra xem người dùng có ngồi quá gần không
        
        Returns:
            tuple: (is_too_close, distance_cm)
        """
        distance, success = self.get_distance()
        if success and distance > 0:
            return distance < self.safe_distance, distance
        return False, 0
    
    def start_monitoring(self, server_url="http://localhost:5000", interval=5):
        """
        Bắt đầu giám sát liên tục và gửi dữ liệu lên server
        
        Args:
            server_url: URL của web server
            interval: Khoảng thời gian giữa các lần đo (giây)
        """
        if self.is_monitoring:
            return False
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, 
            args=(server_url, interval)
        )
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        return True
    
    def stop_monitoring(self):
        """Dừng giám sát"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        self.stop_camera()
    
    def _monitoring_loop(self, server_url, interval):
        """Vòng lặp giám sát chạy trong thread riêng"""
        consecutive_warnings = 0
        
        while self.is_monitoring:
            try:
                too_close, distance = self.is_too_close()
                
                if distance > 0:
                    # Gửi dữ liệu khoảng cách lên server
                    self._send_distance_to_server(server_url, distance)
                    
                    # Kiểm tra cảnh báo liên tục
                    if too_close:
                        consecutive_warnings += 1
                        print(f"⚠️ Cảnh báo: Khoảng cách {distance:.1f}cm quá gần! ({consecutive_warnings})")
                        
                        # Gửi cảnh báo break nếu quá gần liên tục
                        if consecutive_warnings >= 3:  # 3 lần liên tục
                            self._send_break_warning_to_server(server_url)
                            consecutive_warnings = 0
                    else:
                        consecutive_warnings = 0
                        print(f"✅ Khoảng cách an toàn: {distance:.1f}cm")
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"❌ Lỗi trong quá trình giám sát: {e}")
                time.sleep(1)
    
    def _send_distance_to_server(self, server_url, distance):
        """Gửi dữ liệu khoảng cách lên server"""
        try:
            response = requests.post(
                f"{server_url}/add_distance",
                json={"distance": distance},
                timeout=5
            )
            if response.status_code == 200:
                print(f"📤 Đã gửi khoảng cách: {distance:.1f}cm")
            else:
                print(f"⚠️ Không thể gửi khoảng cách: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi kết nối server khi gửi khoảng cách: {e}")
    
    def _send_break_warning_to_server(self, server_url):
        """Gửi cảnh báo nghỉ giải lao lên server"""
        try:
            response = requests.post(
                f"{server_url}/add_break_warning",
                timeout=5
            )
            if response.status_code == 200:
                print("📤 Đã gửi cảnh báo nghỉ giải lao")
            else:
                print(f"⚠️ Không thể gửi cảnh báo: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi kết nối server khi gửi cảnh báo: {e}")
    
    def save_image_with_distance(self, save_path="./"):
        """Lưu ảnh với thông tin khoảng cách"""
        if not self.start_camera():
            return False, "Không thể khởi động camera"
        
        ret, frame = self.cap.read()
        if not ret:
            return False, "Không thể lấy frame từ camera"
        
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if results.multi_face_landmarks:
            for face in results.multi_face_landmarks:
                left_eye = face.landmark[33]
                right_eye = face.landmark[263]
                
                x1 = int(left_eye.x * w)
                y1 = int(left_eye.y * h)
                x2 = int(right_eye.x * w)
                y2 = int(right_eye.y * h)
                
                pixel_distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                
                if pixel_distance > 0:
                    distance_cm = (self.real_eye_distance * self.focal_length) / pixel_distance
                    
                    # Ghi thông tin lên ảnh
                    color = (0, 255, 0) if distance_cm >= self.safe_distance else (0, 0, 255)
                    cv2.putText(frame, f"Distance: {distance_cm:.2f} cm", (30, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                    
                    # Vẽ mắt
                    cv2.circle(frame, (x1, y1), 5, (255, 0, 0), -1)
                    cv2.circle(frame, (x2, y2), 5, (0, 0, 255), -1)
                    cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
                    
                    # Lưu ảnh
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{save_path}/distance_{timestamp}_{distance_cm:.1f}cm.jpg"
                    cv2.imwrite(filename, frame)
                    
                    return True, f"Đã lưu ảnh: {filename}"
        
        return False, "Không phát hiện khuôn mặt"

# Hàm test độc lập
def test_distance_camera():
    """Hàm test camera đo khoảng cách"""
    camera = DistanceCamera()
    
    try:
        print("🎥 Bắt đầu test camera...")
        
        for i in range(10):
            too_close, distance = camera.is_too_close()
            if distance > 0:
                status = "⚠️ QUÁ GẦN" if too_close else "✅ AN TOÀN"
                print(f"Lần {i+1}: {distance:.1f}cm - {status}")
            else:
                print(f"Lần {i+1}: Không phát hiện khuôn mặt")
            
            time.sleep(1)
        
        # Test lưu ảnh
        success, message = camera.save_image_with_distance()
        print(f"Lưu ảnh: {message}")
        
    finally:
        camera.stop_camera()
        print("🔚 Kết thúc test")

if __name__ == "__main__":
    test_distance_camera()