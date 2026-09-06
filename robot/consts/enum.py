"""----------------------------------------------
              Enum configuration
----------------------------------------------"""

from enum import Enum

class BallStatus(Enum):
    NOT_FOUND = 0
    CAM_DETECTED = 1
    IN_KICKER = 2

class GoalStatus(Enum):
    NOT_FOUND = 0
    CLOSE = 1
    FAR = 2

class Object(Enum):
    Ball = 0
    BlueGoal = 1
    YellowGoal = 2
