import cv2
import cvzone
from cvzone.FaceMeshModule import FaceMeshDetector
import threading
import time
from datetime import datetime

class EyeDistanceMonitor:
    def __init__(self, on_distance_update=None, measurement_interval=5):
        """
        Initialize Eye Distance Monitor

        Args:
            on_distance_update: Callback function when new eye distance data is available
            measurement_interval: Time interval between measurements (seconds)
        """
        self.on_distance_update = on_distance_update
        self.measurement_interval = measurement_interval


        # Initialize cvzone FaceMeshDetector
        self.detector = FaceMeshDetector(maxFaces=1)

        # Camera and threading
        self.cap = None
        self.is_running = False
        self.monitor_thread = None

        # Calibration parameters
        self.FOCAL_LENGTH = 700  # Camera focal length (may need adjustment)
        self.REAL_EYE_DISTANCE = 6.3  # Real distance between eyes (cm)


        # Eye landmark indices for cvzone (145, 374 are eye corners)
        self.LEFT_EYE_POINT = 145
        self.RIGHT_EYE_POINT = 374

        # Buffer for smoothing data
        self.distance_buffer = []
        self.buffer_size = 5

        # Logging
        self.last_measurement_time = None
        self.total_measurements = 0
        self.successful_measurements = 0

    def start(self):
        """Start monitoring"""
        if self.is_running:
            return False

        try:
            # Initialize camera
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Cannot open camera")

            # Camera configuration
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            self.is_running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()

            print("Eye distance monitor started successfully")
            return True

        except Exception as e:
            print(f"Failed to start eye distance monitor: {e}")
            return False

    def stop(self):
        """Stop monitoring"""
        self.is_running = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)

        if self.cap:
            self.cap.release()
            self.cap = None

        print("Eye distance monitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        last_measurement = 0

        while self.is_running:
            current_time = time.time()

            # Measure distance at interval
            if current_time - last_measurement >= self.measurement_interval:
                distance = self._measure_distance()

                if distance > 0:
                    # Add to buffer for smoothing
                    self.distance_buffer.append(distance)
                    if len(self.distance_buffer) > self.buffer_size:
                        self.distance_buffer.pop(0)

                    # Calculate average
                    smoothed_distance = sum(self.distance_buffer) / len(self.distance_buffer)

                    # Call callback
                    if self.on_distance_update:
                        self.on_distance_update(smoothed_distance)

                    self.last_measurement_time = datetime.now()
                    self.successful_measurements += 1

                    print(f"Distance: {smoothed_distance:.1f}cm")

                self.total_measurements += 1
                last_measurement = current_time

            time.sleep(0.1)  # Avoid high CPU usage

    def _measure_distance(self):
        """Measure eye-to-camera distance using cvzone FaceMeshDetector"""
        if not self.cap:
            return 0

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return 0

        img, faces = self.detector.findFaceMesh(frame, draw=False)
        if faces:
            face = faces[0]
            pointLeft = face[self.LEFT_EYE_POINT]
            pointRight = face[self.RIGHT_EYE_POINT]
            w, _ = self.detector.findDistance(pointLeft, pointRight)
            W = self.REAL_EYE_DISTANCE  # cm
            f = self.FOCAL_LENGTH  # calibrated focal length
            if w > 0:
                d = (W * f) / w
                return d
        return 0

    def calibrate_focal_length(self, known_distance_cm):
        """Calibrate camera focal length with known distance"""
        print(f"Calibrating with known distance: {known_distance_cm}cm")
        print("Please sit at the specified distance and press Enter...")
        input()

        # Measure pixel distance at known distance
        measurements = []
        for i in range(10):
            ret, frame = self.cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_mesh.process(rgb_frame)

                if results.multi_face_landmarks:
                    face_landmarks = results.multi_face_landmarks[0]
                    landmarks = face_landmarks.landmark
                    h, w = frame.shape[:2]

                    left_eye_outer = landmarks[self.LEFT_EYE_OUTER]
                    right_eye_outer = landmarks[self.RIGHT_EYE_OUTER]

                    left_point = np.array([left_eye_outer.x * w, left_eye_outer.y * h])
                    right_point = np.array([right_eye_outer.x * w, right_eye_outer.y * h])

                    pixel_distance = np.linalg.norm(left_point - right_point)
                    measurements.append(pixel_distance)

            time.sleep(0.1)

        if measurements:
            avg_pixel_distance = sum(measurements) / len(measurements)
            # Focal length = (pixel_distance * real_distance) / real_eye_distance
            self.FOCAL_LENGTH = (avg_pixel_distance * known_distance_cm) / self.REAL_EYE_DISTANCE
            print(f"Calibrated focal length: {self.FOCAL_LENGTH:.1f}")
            return self.FOCAL_LENGTH
        else:
            print("Calibration failed - no face detected")
            return None

    def get_statistics(self):
        """Get monitoring statistics"""
        success_rate = 0
        if self.total_measurements > 0:
            success_rate = (self.successful_measurements / self.total_measurements) * 100

        return {
            'total_measurements': self.total_measurements,
            'successful_measurements': self.successful_measurements,
            'success_rate': success_rate,
            'last_measurement': self.last_measurement_time,
            'current_buffer_size': len(self.distance_buffer),
            'focal_length': self.FOCAL_LENGTH
        }

    def reset_statistics(self):
        """Reset statistics"""
        self.total_measurements = 0
        self.successful_measurements = 0
        self.last_measurement_time = None
        self.distance_buffer.clear()

# Utility functions

def test_camera():
    """Test camera and show preview"""
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Cannot open camera")
        return False

    print("Camera test - press 'q' to exit")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            break
        cv2.imshow('Camera Preview', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()