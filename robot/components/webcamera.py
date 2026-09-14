from robot.abstracts.IAICamera import IAICamera
import cv2

class WebCamera(IAICamera):

    def __init__(self,
                 modelPath: str,
                 objectNames = None,
                 focalLength: float = 0.0,
                 imageRes: tuple[int, int] = (256, 256),
                 outputDir: str = "saved_frames"
                 ) -> None:

        super().__init__(modelPath, imageRes, focalLength, objectNames, outputDir)

        # Camera configuration
        self._webcam = cv2.VideoCapture(0)

        # Calibration
        if self._focalLength == 0.0:
            self.calibrate(50)

    def captureFrame(self) -> None:
        ret, frame = self._webcam.read()
        if not ret:
            return None

        # Frame dimensions
        frame_h, frame_w, _ = frame.shape

        min_dim = min(frame_h, frame_w)
        start_x = (frame_w - min_dim) // 2
        start_y = (frame_h - min_dim) // 2

        return cv2.resize(frame[start_y:start_y + min_dim, start_x:start_x + min_dim], self._imageRes,
                          interpolation=cv2.INTER_AREA)

if __name__ == "__main__":
    import time

    VERSION = 3.0
    c = WebCamera(f"/home/admin/Superstrika/robot/models/best-V{VERSION}.onnx",
                  focalLength=594.8065824286882)
    
    while True:
        distances = c.getObjects()
        print(distances)
        time.sleep(0.05)  # Slight pause between captures to control saved image rate
