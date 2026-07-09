import sys
import robot.components.servo as servo
from time import sleep
import gpiozero
import robot.processes.EdgeLineDetection as EdgeLineDetection
import robot.components.gyro as gyro
import robot.components.dribbler as dribbler
import robot.consts.data as data
# from robot.components.vcnl import VCNL4040 as VCNL
import logging
import robot.components.openmvCamera as openmvCamera
from robot.processes.pidCalc import PidCalc
import robot.processes.gyroMovement as gyroMovement
import robot.processes.multipleMotors as multipleMotors
import threading
from robot.hunter import Hunt

try:
    from machine import I2C
except ImportError:
    from smbus2 import SMBus as I2C  # For RPI compatibility

class Ride(Hunt):
    def __init__(self, debug=False):
        super().__init__(debug=debug)

        self.log = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'cls': self.__class__.__name__}
        )

    def joyRide(self):

        self.gyroMovement.move_forward_cm(20, (0, 30))

        input()

        self.gyroMovement.move_forward_cm(20, (0, -30))

        input()

        self.gyroMovement.move_forward_cm(10, (30, 30))

        input()

        self.gyroMovement.move_forward_cm(20, (-30, 0))

        input()

        self.gyroMovement.move_forward_cm(20, (0, -30))

        input()

        self.goToBall()

if __name__ == "__main__":
    j = Ride()
    j.joyRide()

