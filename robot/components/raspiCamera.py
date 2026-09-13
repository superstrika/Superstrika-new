from robot.abstracts.IAICamera import IAICamera
from robot.abstracts.ICamera import ObjectInfo, DisplacementVector
from robot.consts.enum import Object, GoalStatus, BallStatus
from robot.consts.data import BALL_SIZE_CM, GOAL_SIZE_CM, CAMERA_HEIGHT_CM

import math
from ultralytics import YOLO
from picamera2 import Picamera2
import cv2
import time
        
class RaspiCamera(IAICamera):

    def __init__(self,
                 modelPath: str,
                 objectNames = None,
                 focalLength: float = 0.0,
                 imageRes: tuple[int, int] = (256, 256),
                 outputDir: str = "saved_frames",
                 ):

        super().__init__(modelPath, imageRes, focalLength, objectNames, outputDir)

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
        
        frame = self._picam.capture_array()
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

