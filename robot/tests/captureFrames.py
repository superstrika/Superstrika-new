import cv2
import os
import time

# Directory where raw images will be saved
output_dir = "saved_frames_raw"
os.makedirs(output_dir, exist_ok=True)

# Initialize webcam (0 is usually the default built-in/USB camera)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print(f"Saving raw frames to '{output_dir}'. Press 'q' or 'Ctrl+C' to stop.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Generate a unique filename using timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S_%f")
        filename = os.path.join(output_dir, f"raw_frame_{timestamp}.jpg")

        # Save the unannotated frame
        cv2.imwrite(filename, frame)

        # Pause briefly to control frame capture rate (e.g., ~10 frames per second)
        input("Enter to capture frame...")

except KeyboardInterrupt:
    print("\nCapture stopped by user.")

finally:
    cap.release()
    cv2.destroyAllWindows()