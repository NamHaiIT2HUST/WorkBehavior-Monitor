import cv2

# Try all video indices from 0 to 3 (typical for laptop webcams)
for i in range(0, 4):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera found at index {i}. Showing preview. Press 'q' to quit.")
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame")
                break
            cv2.imshow(f'Camera {i}', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
    else:
        print(f"No camera at index {i}")
