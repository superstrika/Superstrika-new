from abs import ABC, abstractmethod
from robot.consts.enum import Object, GoalStatus, BallStatus

class ICamera(ABC):

    @abstractmethod
    def getObjects(self) -> dict[Object, tuple[float | None, float | None]]:
        """Pure Virtual method; must be overriden"""
        pass

    @abstractmethod
    def isObjectDetected(self, obj: Object) -> bool:
        """Pure Virtual method; must be overriden"""
        pass

    @abstractmethod
    def getObjectsStatus(self) -> dict[Object, GoalStatus | BallStatus]:
        """Pure Virtual method; must be overriden"""
        pass
    