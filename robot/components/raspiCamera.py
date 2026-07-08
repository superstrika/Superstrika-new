from robot.abstracts.ICamera import ICamera
from robot.consts.enum import Object, GoalStatus, BallStatus
from robot.consts.data import BALL_SIZE_CM, GOAL_SIZE_CM, CAMERA_HEIGHT_CM

import math
from ultralytics import YOLO
from picamera2 import Picamera2
import cv2
import time

class RaspiCamera(ICamera):
    _focalLength: float
    _imageSize: tuple[int]

    def __init__(self, modelPath: str,
                 objectNames: dict[str, Object] = {"Ball": Object.Ball, "BlueGoal": Object.BlueGoal, "YellowGoal": Object.YellowGoal},
                 focalLength: float = 0.0,
                 imageSize: tuple[int] = (256, 256)):
        
        _imageSize = imageSize
        self._objectNames = objectNames
        
        """
        holds the screen XY cordinates and size of the objects that are currently on screen
        Maps to:
        obj: ((sizeX, sizeY), (cordX, cordY))
        """
        self._objects: dict[Object, tuple[tuple[float | None, float | None], tuple[float | None, float | None]]] = {}
        self.clearObjects()

        _focalLength = focalLength

        # model configuration:
        self._model = YOLO(modelPath)

        # camera configuration:
        self._picam = Picamera2()
        previewConfig = self._picam.preview_configuration
        previewConfig.main.size = _imageSize
        previewConfig.main.format = "RGB888"
        self._picam.configure("preview")

        self._picam.start()
        
        # calibration:
        if self._focalLength == 0.0:
            self.calibrate()

    def clearObjects(self):
        """Clears all the object information"""

        self._objects = {
            Object.Ball: ((None, None), (None, None)),
            Object.BlueGoal: ((None, None), (None, None)),
            Object.YellowGoal: ((None, None), (None, None))
        }

    def calibrate(self, calibrationDistanceCM: int, timeoutSec: int = 15) -> None:
        """calibrates the focal length using an orange ball at a known distance.

        Args:
            calibrationDistanceCM (int): the distance between the camera and the ball (not it's projection!)
            timeoutSec (int, optional): the waiting time for a ball to "show up". Defaults to 15.
        """
        self.clearObjects()

        start = time.time()
        print(f"Calibration: place orange ball at {calibrationDistanceCM} cm.")

        while time.time() - start < timeoutSec and RaspiCamera._focalLength == 0:
            self.updateObjects()

            if not self.isObjectDetected(Object.Ball):
                continue

            ballInfo = self._objects[Object.Ball]

            preceivedSize = (ballInfo[0][0] + ballInfo[0][1]) / 2.0
            if preceivedSize > 0:
                RaspiCamera._focalLength = (preceivedSize * calibrationDistanceCM) / BALL_SIZE_CM
                print(f"Calibration complete. {RaspiCamera._focalLength=}")
                return
        
        print(f"Calibration ended. {RaspiCamera._focalLength=}")

    def updateObjects(self) -> None:
        """Updates the object information by capturing an image,
        and making the model look for the objects in it.
        """
        
        frame = self._picam.capture_array()
        bgrFrame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        results = self._model(bgrFrame, stream=True, conf=0.25)

        objects: dict[Object, dict] = {}

        for result in results:
            classTable = result.names

            for box in result.boxes:
                x, y, w, h = box.xywh[0].tolist()
                
                try:
                    obj = self._objectNames[classTable[int(box.cls)]]
                except Exception as e:
                    print(f"Foreign object detected! {e}")
                area = w * h

                if obj not in objects or area > objects[obj]['area']:
                    objects[obj] = {
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'area': area 
                    }
        
        for obj in [Object.Ball, Object.BlueGoal, Object.YellowGoal]:
            if obj in objects:
                info = objects[obj]
                self._objects[obj] = ((info['width'], info['height']), (info['x'], info['y']))
            else:
                self._objects[obj] = ((None, None), (None, None))

    @staticmethod
    def calculateDistance(objectInfo: tuple[float], obj: Object) -> tuple[float]:
        """calculates the distance and angle of the ball from the robot

        Args:
            objectInfo (tuple[float]): [0] - object size. [1] - screen XY cords.
            obj (Object): Ball / BlueGoal / YellowGoal

        Returns:
            tuple[float]: the displacement vector of the object:
            [0] - distance (cm).
            [1] - angle (deg).
        """
        
        actualSize: float = BALL_SIZE_CM if obj == Object.Ball else GOAL_SIZE_CM
        averageDetectedSize: float = (objectInfo[0][0] + objectInfo[0][1]) / 2.0
        directDistance: float = (actualSize * RaspiCamera._focalLength) / (averageDetectedSize)
        
        floorProjectionDistance: float = math.sqrt(max(directDistance**2 - CAMERA_HEIGHT_CM**2, 0.0))
        
        screenCenterXCord: int = RaspiCamera._imageSize[0] / 2.0
        ballCenteredXCord: float = objectInfo[1][0] - screenCenterXCord

        actualXDistance: float = ballCenteredXCord * actualSize / averageDetectedSize

        angle: float = math.degrees(math.asin(actualXDistance / floorProjectionDistance))
        return (floorProjectionDistance, angle)

    def getObjects(self) -> dict[Object, tuple[float | None, float | None]]:
        """calculates the distance and angle for all objects

        Returns:
            dict[Object, tuple[float | None, float | None]]: a dictinary holding all objects with the displacement vector for each object:
            [0] - distance (cm).
            [1] - angle (deg).
        """

        objects: dict = {}
        for obj in [Object.Ball, Object.BlueGoal, Object.YellowGoal]:
            if any(None in t for t in self._objects[obj]):
               objects[obj] = (None, None)
            else:
                objects[obj] = self.calculateDistance(self._objects[obj], obj) 
        
        return objects

    def isObjectDetected(self, obj: Object) -> bool:
        """checks if a given object is detected.

        Args:
            obj (Object): the object to look-for.

        Returns:
            bool: Returns wether the object was detected.
        """

        return not any(None in t for t in self._objects[obj])

    def getObjectsStatus(self) -> dict[Object, GoalStatus | BallStatus]:
        """Pure Virtual method; must be overriden"""
        pass