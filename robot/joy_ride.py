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
import robot.components.camera as camera
from robot.processes.pidCalc import PidCalc
import robot.processes.gyroMovement as gyroMovement
import robot.processes.multipleMotors as multipleMotors
import threading

class Ride:
    def __init__(self, debug=False):
        # race conditions of motors
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        self.priority_active = False

        # exit gate
        self.running_gate = threading.Event()
        self.running_gate.clear()

        # motors
        self.i2c = I2C(data.I2C_ID)
        self.servo = servo.Servo(data.SERVO_PIN)
        self.motors = multipleMotors.multipleMotors(data.MOTOR_PINS, parent=self)
        self.dribbler = dribbler.Dribbler(data.DRIBBLER_PIN)

        # sensors
        self.gyro = gyro.MPU6050(self.i2c)
        self.camera = camera.Camera7046(data.SERIAL_FREQUENCY)

        # vcnl
        # self.vcnl = VCNL()
        # self.vcnl.led_current = self.vcnl.LED_100MA
        # self.vcnl.proximity_high_definition = True
        # self.vcnl.proximity_integration_time = self.vcnl.PS_8T

        # processes
        # self.lineDetection = EdgeLineDetection.EdgeLineDetection(pins=data.TCRT_PINS, motors=self.motors, parent=self)
        self.gyroMovement = gyroMovement.GyroMovement(self.i2c, self.gyro, self.motors)

        # main switch
        self.startSwitch = gpiozero.Button(data.START_BUTTON_PIN, bounce_time=0.05)
        self.startSwitch.when_activated = self.toggle_pause

        self.log = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'cls': self.__class__.__name__}
        )

        if debug:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter(data.LOG_FORMAT))
            self.log.logger.addHandler(console_handler)

    def toggle_pause(self):
        if self.running_gate.is_set():
            self.log.info("[!] PAUSING")
            self.running_gate.clear()
            self.motors.stop()

        else:
            self.log.info("[>] RESUMING")
            self.running_gate.set()

    def joyRide(self):

        self.gyroMovement.move_forward_cm(30, (0, 40))

        input()

        self.gyroMovement.move_forward_cm(30, (0, -40))

        input()

        self.gyroMovement.move_forward_cm(30, (30, 30))

        input()

