import cv2
import mediapipe as mp
import time

# Khởi tạo Face Mesh từ Mediapipe
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)

# Thông số khoảng cách thực giữa hai mắt (cm)
REAL_EYE_DISTANCE = 6.3  # cm

# Tiêu cự ảo (focal length), cần tinh chỉnh để phù hợp camera
FOCAL_LENGTH = 840  # có thể calibrate lại

# Khởi động camera
cap = cv2.VideoCapture(0)

# Vòng lặp đọc frame và xử lý
frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Không lấy được frame từ camera.")
        break

    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

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
                distance_cm = (REAL_EYE_DISTANCE * FOCAL_LENGTH) / pixel_distance
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"output_{timestamp}.jpg"

                # Ghi thông tin vào ảnh
                cv2.putText(frame, f"Distance: {distance_cm:.2f} cm", (30, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Vẽ mắt
                cv2.circle(frame, (x1, y1), 3, (255, 0, 0), -1)
                cv2.circle(frame, (x2, y2), 3, (0, 0, 255), -1)

                # Lưu ảnh có chú thích
                cv2.imwrite(filename, frame)
                print(f"✅ Đã lưu ảnh: {filename} (khoảng cách: {distance_cm:.2f} cm)")

    frame_count += 1

    if frame_count >= 10:
        break  # Chạy 10 frame rồi dừng lại (có thể thay đổi nếu cần)

cap.release()