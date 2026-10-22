import time
import os
import sys
from picamera2 import Picamera2, controls
import cv2

# Roboflow API
API_KEY = ""
WORKSPACE_NAME = ""
PROJECT_NAME = ""

# Camera configuration - low resolution as requested
IMAGE_RES = (256, 256)

# Directory where captured frames will be saved
output_dir = "saved_frames"
os.makedirs(output_dir, exist_ok=True)

def upload_to_roboflow(api_key, workspace_name, project_name, project_version=None):
    """
    Upload all saved frames to Roboflow.
    
    Args:
        api_key: Your Roboflow API key
        workspace_name: Your Roboflow workspace name
        project_name: Name of the Roboflow project
        project_version: (optional) Version number to upload to
    
    Usage:
        1. Install roboflow: pip install roboflow
        2. Get your API key from https://app.roboflow.com/?ref=code
        3. Call this function with your credentials
    """
    try:
        from roboflow import Roboflow
    except ImportError:
        print("Error: roboflow package not installed.")
        print("Install it with: pip install roboflow")
        return False
    
    try:
        # Initialize Roboflow
        rf = Roboflow(api_key=api_key)
        workspace = rf.workspace(workspace_name)
        project = workspace.project(project_name)
        
        # Get list of all jpg files in output directory
        image_files = [f for f in os.listdir(output_dir) if f.endswith('.jpg')]
        
        if not image_files:
            print(f"No images found in {output_dir}/")
            return False
        
        print(f"\nUploading {len(image_files)} images to Roboflow project: {project_name}")
        
        # Upload each image
        uploaded_count = 0
        for img_file in image_files:
            img_path = os.path.join(output_dir, img_file)
            try:
                project.upload(img_path)
                uploaded_count += 1
                print(f"  Uploaded: {img_file}")
            except Exception as e:
                print(f"  Failed to upload {img_file}: {e}")
        
        print(f"\nUpload complete: {uploaded_count}/{len(image_files)} images uploaded successfully.")
        
        # If version specified, generate annotation
        if project_version:
            print(f"Generating annotations for version {project_version}...")
            # This would typically be done via Roboflow web interface or API
            print("Note: You may need to generate a new version in the Roboflow web interface.")
        
        return True
        
    except Exception as e:
        print(f"Error uploading to Roboflow: {e}")
        return False

def main() -> None:

    # Initialize PiCamera 2
    picam = Picamera2()
    previewConfig = picam.preview_configuration
    previewConfig.main.size = IMAGE_RES
    previewConfig.main.format = "RGB888"
    picam.configure("preview")

    picam.start()

    # Set manual focus to infinity
    picam.set_controls({
        "AfMode": 0,  # manual focus
        "LensPosition": 5.0,  # focus to infinity
    })

    print(f"Camera started. Resolution: {IMAGE_RES[0]}x{IMAGE_RES[1]}")
    print(f"Captured frames will be saved to '{output_dir}/' directory.")
    print("Press 'Enter' to capture and save the current frame.")
    print("Press 'q' to quit.")
    print("Press 'u' to upload all saved frames to Roboflow (requires roboflow package).")

    frame_count = 0

    try:
        while True:
            # Capture the current frame
            frame = picam.capture_array()

            # Display the live feed
            cv2.imshow("Raspberry Pi Camera - Press Enter to Capture", frame)

            # Check for key press (non-blocking with 1ms delay)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                # Quit
                break
            elif key == 13:  # Enter key (carriage return)
                # Capture and save frame
                frame_count += 1
                timestamp = time.strftime("%Y%m%d_%H%M%S_%f")
                filename = os.path.join(output_dir, f"frame_{timestamp}.jpg")

                cv2.imwrite(filename, frame)
                print(f"[{frame_count}] Saved: {filename}")
            elif key == ord('u'):
                # Upload to Roboflow
                print("\n" + "="*60)
                print("ROBOFLOW UPLOAD")
                print("="*60)
                print("\nTo upload images to Roboflow, you need:")
                print("  1. A Roboflow account: https://app.roboflow.com")
                print("  2. Your API key from: https://app.roboflow.com/?ref=code")
                print("  3. A project created in Roboflow")
                print("\nExample usage:")
                print("  upload_to_roboflow('YOUR_API_KEY', 'workspace', 'project-name')")
                print("\nOr you can upload manually via the Roboflow web interface.")
                print("="*60)

                # Optional: interactive upload
                upload_choice = input("\nDo you want to upload now? (y/n): ").strip().lower()
                if upload_choice == 'y':
                    upload_to_roboflow(API_KEY, WORKSPACE_NAME, PROJECT_NAME)

    except KeyboardInterrupt:
        print("\nCapture stopped by user (Ctrl+C).")

    finally:
        picam.close()
        cv2.destroyAllWindows()
        print(f"\nSession complete. Total frames captured: {frame_count}")
        print(f"Frames saved in: {os.path.abspath(output_dir)}/")
