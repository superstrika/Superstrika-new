"""----------------------------------------------
                   GPIO
----------------------------------------------"""

MOTOR_PINS: list[int] = [23, 24, 19, 20, 25, 26, 21, 22]
TCRT_PINS: list[int] = [1, 0, 5]
SERVO_PIN: int = 6
RELAY_PIN: int = 7

DRIBBLER_PIN: tuple[int, int] = (13, 16)
KICKER_PIN: tuple[int, int] = (13, 16)
START_BUTTON_PIN: int = 4

"""----------------------------------------------
              Chip configuration
----------------------------------------------"""
I2C_ID: int = 1
CHIP_ID: int = 0

"""----------------------------------------------
              Camera configuration
----------------------------------------------"""
MIN_ANGLE: int = 40
MID_ANGLE: int = 100
MAX_ANGLE: int = 180
GOOD_ANGLE: int = 160

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
              Camera size configuration
----------------------------------------------"""

BALL_SIZE_CM: float = 4.3
GOAL_SIZE_CM: float = 64.0
CAMERA_HEIGHT_CM: float = 14.5

"""----------------------------------------------
              Hunt Configuration
----------------------------------------------"""
ROTATION_SPEED: int = 25

SPIN_SEARCH_ERROR: float = 3
SPIN_TO_BALL_ERROR: float = 1.5
GO_TO_BALL_ERROR: float = 1
# ROBOT_BALL_DISTANCE: tuple[float, float] = (0, 0)
ROBOT_GOAl_DISTANCE: int = 25

VCNL_PROX_CLOSE: int = 115
VCNL_PROX_IN_KICKER: int = 140

"""----------------------------------------------
              Game configuration
----------------------------------------------"""
SELF_IS_BLUE: bool = True

import socket

SELF_IS_HUNTER: bool = True if socket.gethostname() == "superstrika" else False