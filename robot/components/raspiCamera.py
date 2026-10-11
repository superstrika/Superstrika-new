import time

from robot.abstracts.IAICamera import IAICamera
from picamera2 import Picamera2
import cv2

class RaspiCamera(IAICamera):

    def __init__(self,
                 modelPath: str,
                 objectNames = None,
                 focalLength: float = 0.0,
                 imageRes: tuple[int, int] = (256, 256),
                 outputDir: str = "saved_frames",
                 ):

        super().__init__(modelPath=modelPath, imageRes=imageRes, focalLength=focalLength, objectNames=objectNames, outputDir=outputDir)

        # camera configuration:
        self._picam = Picamera2()
        previewConfig = self._picam.preview_configuration
        previewConfig.main.size = imageRes
        previewConfig.main.format = "RGB888"
        self._picam.configure("preview")

        self._picam.start()
        
        # calibration:
        if self._focalLength == 0.0:
            self.calibrate(50)

    def captureFrame(self) -> None:
        """Updates the object information by capturing an image,
        and making the model look for the objects in it.
        """
        
        # Picamera2's "RGB888" format is stored in memory as B,G,R per pixel,
        # which is already the channel order OpenCV expects - no conversion needed.
        return self._picam.capture_array()


if __name__ == "__main__":
    cam = RaspiCamera("robot/models/best-V3.0.onnx")

    while True:
        print(cam.getObjects())
        time.sleep(1)

