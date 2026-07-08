from robot.abstracts.ICamera import ICamera
from robot.consts.enum import Object, GoalStatus, BallStatus
from robot.consts.data import BALL_SIZE_CM, GOAL_SIZE_CM, CAMERA_HEIGHT_CM

import math

class RaspiCamera(ICamera):
    _focalLength: float = 0.0
    _imageSize: tuple[int] = (0, 0)

    def __init__(self, modelPath: str,
                 objectNames: tuple[str] = ("Ball", "BlueGoal", "YellowGoal"),
                 focalLength: float = 0.0,
                 imageSize: tuple[int] = (256, 256)):
        
        _imageSize = imageSize
        
        """
        holds the screen XY cordinates and size of the objects that are currently on screen
        Maps to:
        obj: ((sizeX, sizeY), (cordX, cordY))
        """
        self._objects: dict[Object, tuple[tuple[float | None, float | None], tuple[float | None, float | None]]] = {
            Object.Ball: ((None, None), (None, None)),
            Object.BlueGoal: ((None, None), (None, None)),
            Object.YellowGoal: ((None, None), (None, None))
        }

        _focalLength = focalLength
        
        # calibration:
        if self._focalLength == 0.0:
            self.calibrate()

    def calibrate(self):
        ...

    def updateObjects(self):
        ...

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