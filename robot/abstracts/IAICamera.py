from abc import abstractmethod

from robot.abstracts.ICamera import ICamera, ObjectInfo, DisplacementVector
from robot.consts.enum import Object, GoalStatus, BallStatus
from robot.consts.data import BALL_SIZE_CM, GOAL_SIZE_CM, CAMERA_HEIGHT_CM

import math
from ultralytics import YOLO
import cv2
import time
import os

class IAICamera(ICamera):
    def __init__(self,
                 modelPath: str,
                 objectNames = None,
                 focalLength: float = 0.0,
                 imageRes: tuple[int, int] = (256, 256),
                 outputDir: str = "saved_frames"
                 ) -> None:

        # Folder to save output images
        self._outputDir = outputDir
        os.makedirs(self._outputDir, exist_ok=True)

        # Image Configuration:
        self._imageRes = imageRes
        self._focalLength = focalLength

        # Object Configuration:

        if objectNames is None:
            objectNames = {
                "Ball": Object.Ball,
                "Blue Goal": Object.BlueGoal,
                "Yellow goal": Object.YellowGoal
            }
        self._objectNames = objectNames

        self._objects: dict[Object, ObjectInfo] = {}
        self.clearObjects()

        # model configuration:
        self._model = YOLO(modelPath)

    def clearObjects(self) -> None:
        """Clears all the object information"""
        self._objects = {
            Object.Ball: ObjectInfo.empty(),
            Object.BlueGoal: ObjectInfo.empty(),
            Object.YellowGoal: ObjectInfo.empty()
        }

    def calibrate(self, calibrationDistanceCM: int, timeoutSec: int = 15) -> None:
        """Calibrates the focal length using an orange ball at a known distance."""
        input(f"Calibration needed! Put the ball {calibrationDistanceCM} cm away from the camera and click enter.")
        self.clearObjects()

        start = time.time()
        print(f"Calibration: place orange ball at {calibrationDistanceCM} cm.")

        while time.time() - start < timeoutSec and IAICamera._focalLength == 0:
            self.updateObjects()

            if not self.isObjectDetected(Object.Ball):
                continue

            ballInfo = self._objects[Object.Ball]

            perceivedSize = (ballInfo.width + ballInfo.height) / 2.0
            if perceivedSize > 0:
                self._focalLength = (perceivedSize * calibrationDistanceCM) / BALL_SIZE_CM
                print(f"Calibration complete. {self._focalLength=}")
                return

        print(f"Calibration ended. {self._focalLength=}")

    def updateObjects(self) -> None:
        """Updates the object information, overlays center crosshair, bounding boxes,
        and screen coordinates, then saves the image to a folder.
        """
        frame = self.captureFrame()

        frame_h, frame_w, _ = frame.shape
        center_x, center_y = frame_w // 2, frame_h // 2

        results = self._model(frame, stream=True, conf=0.25, imgsz=self._imageRes[0])
        objects: dict[Object, ObjectInfo] = {}

        for result in results:
            classTable = result.names

            for box in result.boxes:
                x, y, w, h = box.xywh[0].tolist()

                # Bounding box corners for drawing
                x1, y1 = int(x - w / 2), int(y - h / 2)
                x2, y2 = int(x + w / 2), int(y + h / 2)

                cls_idx = int(box.cls)
                class_name = classTable.get(cls_idx, "Unknown")

                try:
                    obj = self._objectNames[class_name]
                except KeyError:
                    print(f"Foreign object detected! {class_name}")
                    obj = None

                area = w * h

                if obj and (obj not in objects or area > objects[obj].area):
                    objects[obj] = ObjectInfo(h, w, x, y, area)

                # --- 1. Draw Bounding Box ---
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # --- 2. Draw Coordinates & Label ---
                label = f"{class_name} ({int(x)}, {int(y)})"
                cv2.putText(
                    frame,
                    label,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1,
                    cv2.LINE_AA
                )

        # Update detected internal state
        for obj in [Object.Ball, Object.BlueGoal, Object.YellowGoal]:
            if obj in objects:
                self._objects[obj] = objects[obj]
            else:
                self._objects[obj] = ObjectInfo.empty()

        # --- 3. Draw White Center Crosshair ---
        white_color = (255, 255, 255)
        # Horizontal line across the center
        cv2.line(frame, (0, center_y), (frame_w, center_y), white_color, 1)
        # Vertical line across the center
        cv2.line(frame, (center_x, 0), (center_x, frame_h), white_color, 1)

        # --- 4. Auto-Save Frame ---
        timestamp = time.strftime("%Y%m%d_%H%M%S_%f")
        save_path = os.path.join(self._outputDir, f"frame_{timestamp}.jpg")
        cv2.imwrite(save_path, frame)

    def calculateDistance(self, objectInfo: ObjectInfo, obj: Object) -> DisplacementVector:
        """Calculates distance and angle from camera."""

        actualSize: float = BALL_SIZE_CM if obj == Object.Ball else GOAL_SIZE_CM
        averageDetectedSize: float = (objectInfo.width + objectInfo.height) / 2.0
        # averageDetectedSize: float = objectInfo.width
        directDistance: float = (actualSize * self._focalLength) / (averageDetectedSize)

        floorProjectionDistance: float = math.sqrt(max(directDistance ** 2 - CAMERA_HEIGHT_CM ** 2, 0.0))

        screenCenterXCord: float = self._imageRes[0] / 2.0
        ballCenteredXCord: float = objectInfo.x - screenCenterXCord

        actualXDistance: float = ballCenteredXCord * actualSize / averageDetectedSize

        angle: float = math.degrees(math.asin(actualXDistance / floorProjectionDistance))
        return DisplacementVector(floorProjectionDistance, angle)

    @staticmethod
    def calculateMirrorAngle(objectInfo: ObjectInfo) -> DisplacementVector:
        angle = math.atan(objectInfo.x / objectInfo.y)
        return DisplacementVector(0, angle)

    def getObjects(self, mirror: bool = False) -> dict[Object, DisplacementVector | None]:
        """Calculates distance and angle for all objects."""
        self.updateObjects()

        objects: dict[Object, DisplacementVector | None] = {}
        for obj in [Object.Ball, Object.BlueGoal, Object.YellowGoal]:
            if any(value is None for value in self._objects[obj].__dict__.values()):
                objects[obj] = None
            elif mirror:
                objects[obj] = self.calculateMirrorAngle(self._objects[obj])
            else:
                objects[obj] = self.calculateDistance(self._objects[obj], obj)

        return objects

    def isObjectDetected(self, obj: Object) -> bool:
        """Checks if a given object is detected."""
        self.updateObjects()
        return not any(value is None for value in self._objects[obj].__dict__.values())

    @abstractmethod
    def captureFrame(self):
        """Pure Virtual method; must be overridden."""
        pass
