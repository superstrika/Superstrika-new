"""----------------------------------------------
                   GPIO
----------------------------------------------"""

MOTOR_PINS: list[int] = [23, 24, 21, 22, 25, 26, 19, 20]
TCRT_PINS: list[int] = [1, 0, 5]
SERVO_PIN: int = 6
RELAY_PIN: int = 7

DRIBBLER_PIN: tuple[int, int] = (13, 16)
START_BUTTON_PIN: int = 4

"""----------------------------------------------
              Chip configuration
----------------------------------------------"""
I2C_ID: int = 1
CHIP_ID: int = 0

"""----------------------------------------------
              Camera configuration
----------------------------------------------"""
MIN_ANGLE: int = 75
MAX_ANGLE: int = 180
GOOD_ANGLE: int = 150

"""----------------------------------------------
              Serial configuration
----------------------------------------------"""
SERIAL_FREQUENCY: int = 115200

"""----------------------------------------------
               Log configuration
----------------------------------------------"""
LOG_PATH: str = './logs/main.log'
LOG_FORMAT: str = "[%(levelname)s] %(cls)s: %(funcName)s: %(message)s"

"""----------------------------------------------
              Hunt Configuration
----------------------------------------------"""
ROTATION_SPEED: int = 30

SPIN_SEARCH_ERROR: float = 3
SPIN_TO_BALL_ERROR: float = 1.5
GO_TO_BALL_ERROR: float = 1.5
ROBOT_BALL_DISTANCE: tuple[float, float] = (1, 1)
ROBOT_GOAL_DISTANCE: tuple[float, float] = (25, 25)

VCNL_PROX_CLOSE = 20
VCNL_PROX_IN_KICKER = 1000
VCNL_PROX_NOT_DETECTED = 15

"""----------------------------------------------
              Game configuration
----------------------------------------------"""
SELF_IS_BLUE: bool = True

import socket

SELF_IS_HUNTER: bool = True if socket.gethostname() == "superstrika" else False

"""----------------------------------------------
              Enum configuration
----------------------------------------------"""

from enum import Enum

class BallStatus(Enum):
    NOT_FOUND = 0
    CAM_DETECTED = 1
    VCNL_CLOSE = 2
    CAM_DETECTED_AND_VCNL_CLOSE = 3
    VCNL_IN_KICKER = 4

class GoalStatus(Enum):
    NOT_FOUND = 0
    CLOSE = 1
    FAR = 2

class Object(Enum):
    Ball = 0
    BlueGoal = 1
    YellowGoal = 2
