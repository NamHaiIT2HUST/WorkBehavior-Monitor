# distance_utils.py
import cv2
import mediapipe as mp
import numpy as np
import time

class DistanceCamera:
    def __init__(self, cam_id=0, buffer_size=5):
        self.cap = cv2.VideoCapture(cam_id)
        self.buffer = []
        self.buffer_size = buffer_size

        # Khoảng cách thật giữa 2 mắt (cm)
        self.REAL_EYE_DISTANCE = 6.3

        # Focal length (nên calibrate sau)
        self.FOCAL_LENGTH = 840

        # Khởi tạo MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)

    def get_distance(self):
        ret, frame = self.cap.read()
        if not ret:
            print("❌ Không lấy được frame từ camera")
            return 0

        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            face = results.multi_face_landmarks[0]
            left_eye = face.landmark[33]
            right_eye = face.landmark[263]

            x1 = int(left_eye.x * w)
            y1 = int(left_eye.y * h)
            x2 = int(right_eye.x * w)
            y2 = int(right_eye.y * h)

            pixel_distance = np.linalg.norm(np.array([x1, y1]) - np.array([x2, y2]))

            if pixel_distance > 0:
                distance_cm = (self.REAL_EYE_DISTANCE * self.FOCAL_LENGTH) / pixel_distance
                self.buffer.append(distance_cm)
                if len(self.buffer) > self.buffer_size:
                    self.buffer.pop(0)

                avg = sum(self.buffer) / len(self.buffer)
                print(f"✅ Measured Distance: {avg:.1f} cm")
                return avg
        else:
            print("⚠️ Không nhận diện được khuôn mặt")
        return 0

    def is_too_close(self, threshold=35):
        dist = self.get_distance()
        return dist < threshold, dist
