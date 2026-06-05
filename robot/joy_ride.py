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

try:
    from machine import I2C
except ImportError:
    from smbus2 import SMBus as I2C  # For RPI compatibility

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

    def goToBall(self, delay=0.005, obj: data.Object = data.Object.Ball) -> None:
        self.log.info("Going to Ball...")
        sp = data.ROBOT_BALL_DISTANCE if obj == data.Object.Ball else data.ROBOT_GOAL_DISTANCE

        pidY = PidCalc(0.6, 0, 0, 100, verbose=False)
        pidX = PidCalc(0.01, 0, 0.1, 100, verbose=False)

        pv = self.getObjectLocation(obj)  # distance
        self.log.debug(f"{pv=}")

        if pv[0] is None or pv[1] is None:
            print("Ball Lost")
            self.motors.stop()
            return None

        while (abs(pv[0] - sp[0]) > data.GO_TO_BALL_ERROR) or (abs(pv[1] - sp[1]) > data.GO_TO_BALL_ERROR):
            # if not self.running_gate.is_set():  # ------------------------------------------------------------------- Check if end button was pressed.
            #     return None

            speedX = pidX.pidCalc(pv[0] - sp[0])
            speedY = max(pidY.pidCalc(pv[1] - sp[1]), 25)

            self.log.debug(f"Vx: {speedX}, Vy: {speedY}")

            self.motors.setSpeed(speedX, speedY, 0)

            pv = self.getObjectLocation(obj)

            if pv[0] is None or pv[1] is None:
                self.motors.stop()
                return None

        self.log.info(f"Got to Object {obj.name} successfully... e: {pv[0] - sp[0]}, {pv[1] - sp[1]}")
        return None
    
    def getObjectLocation(self, obj: data.Object) -> tuple[float | None, float | None] | tuple[None, None]:
        if obj == data.Object.Ball:
            return self.camera.getBallLocation()
        elif obj == data.Object.YellowGoal:
            return self.camera.getYellowGoalLocation()
        elif obj == data.Object.BlueGoal:
            return self.camera.getBlueGoalLocation()
        return None, None

if __name__ == "__main__":
    j = Ride()
    j.joyRide()

