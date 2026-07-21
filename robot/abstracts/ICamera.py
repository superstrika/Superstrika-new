from robot.consts.enum import Object, GoalStatus, BallStatus
from robot.consts.data import VCNL_PROX_IN_KICKER, VCNL_PROX_CLOSE, ROBOT_GOAl_DISTANCE

from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ObjectInfo:
    """Struct of Object size metrics and screen location:
    1. height, width: float | None - the object's size in centimeters.
    2. x, y: float | None - the object's location in screen (in captured image) in pixels.
    3. area: float - the object's area in pixel^2.
    """

    height: float | None = None
    width: float | None = None
    x: float | None = None
    y: float | None = None
    area: float | None = None

    @classmethod
    def empty(cls) -> "ObjectInfo":
        return cls()

@dataclass
class DisplacementVector: 
    """Struct of Object displacement vector:
    1. distance: float - the distance in centimeters.
    2. angle: float - the angle in degress.
    """

    distance: float = 0.0
    angle: float = 0.0

    @classmethod
    def empty(cls) -> "DisplacementVector":
        return cls()

class ICamera(ABC):

    @abstractmethod
    def getObjects(self) -> dict[Object, DisplacementVector]:
        """Pure Virtual method; must be overriden"""
        pass

    @abstractmethod
    def isObjectDetected(self, obj: Object) -> bool:
        """Pure Virtual method; must be overriden"""
        pass

    def getObjectsStatus(self, vcnlProximity: int = 0) -> dict[Object, GoalStatus | BallStatus]:
        distances = self.getObjects()
        statuses: dict[Object, GoalStatus | BallStatus] = {}

        for goal in [Object.BlueGoal, Object.YellowGoal]:
            if not distances[goal]:
                statuses[goal] = GoalStatus.NOT_FOUND
            elif distances[goal].distance < ROBOT_GOAl_DISTANCE:
                statuses[goal] = GoalStatus.CLOSE
            else:
                statuses[goal] = GoalStatus.FAR

        camFound = True if distances[Object.Ball] else False

        if not camFound and vcnlProximity < VCNL_PROX_CLOSE:
            statuses[Object.Ball] = BallStatus.NOT_FOUND
        elif camFound and vcnlProximity < VCNL_PROX_CLOSE:
            statuses[Object.Ball] = BallStatus.CAM_DETECTED
        elif not camFound and VCNL_PROX_CLOSE < vcnlProximity < VCNL_PROX_IN_KICKER:
            statuses[Object.Ball] = BallStatus.VCNL_CLOSE
        elif not camFound and VCNL_PROX_IN_KICKER < vcnlProximity:
            statuses[Object.Ball] = BallStatus.VCNL_IN_KICKER
        else:
            statuses[Object.Ball] = BallStatus.CAM_DETECTED_AND_VCNL_CLOSE
        
        return statuses
    