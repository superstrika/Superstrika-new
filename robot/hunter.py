import sys
import robot.components.servo as servo
from time import sleep
import time
import math
import gpiozero
import robot.processes.EdgeLineDetection as EdgeLineDetection
import robot.components.gyro as gyro
import robot.components.dribbler as dribbler
import robot.consts.data as data
from robot.components.vcnl import VCNL4040 as VCNL
import logging
import robot.components.webcamera as webCamera
from robot.processes.pidCalc import PidCalc
import robot.processes.gyroMovement as gyroMovement
import robot.processes.multipleMotors as multipleMotors
import threading
from robot.consts.enum import GoalStatus, BallStatus, Object

try:
    from machine import I2C
except ImportError:
    from smbus2 import SMBus as I2C  # For RPI compatibility

logging.basicConfig(filename=data.LOG_PATH, filemode='w', level=logging.DEBUG, format=data.LOG_FORMAT)

class Hunt:
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
        self.camera = webCamera.WebCamera(f"/home/admin/Superstrika/robot/models/best-V2.1.onnx",
                  {
                      "Ball": Object.Ball,
                      "Blue Goal": Object.BlueGoal,
                      "Yellow goal": Object.YellowGoal
                  },
                  594.8065824286882)

        # vcnl
        self.vcnl = VCNL()
        self.vcnl.led_current = self.vcnl.LED_100MA
        self.vcnl.proximity_high_definition = True
        self.vcnl.proximity_integration_time = self.vcnl.PS_8T

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

        self.toggle_pause()

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

    def check_pause(self, timeout=None):
        return self.running_gate.wait(timeout=timeout)

    def camSearch(self, obj: Object = Object.Ball) -> bool:
        """
        Changes camera angle until ball is found.
        :param delay: the delay each change of angle.
        :return: True for success or False for fail\
        """

        self.log.info("Initializing Camera Search...")

        for angle in range(data.MAX_ANGLE, data.MIN_ANGLE, -35):
            self.servo.angle = angle
            if self.camera.isObjectDetected(obj):
                return True
            
            time.sleep(0.2)
        
        return False

    def spinSearch(self, delay=0.6, right: bool = True, obj: Object = Object.Ball) -> bool | None:
        """
        Spins the robot 360 degrees or until ball is found.
        :param delay: the delay between the start of spinning to first angle check.
        :param right: the direction of the spinning
        :param obj: which object to search: ball, yellow goal or blue goal
        :return: True if found, False if failed. None if stopped by gate+.
        """

        self.log.info("Initializing Spin Search...")

        self.gyro.reset_theta()

        angle = self.gyro.get_z_angle()
        while abs(angle) < 360:
            if not self.running_gate.is_set():  # ------------------------------------------------------------------- Check if end button was pressed.
                return None
            
            if obj == Object.Ball and self.camSearch(obj):
                self.log.info(f"Object {obj.name} Found")
                return True
            elif (obj == Object.YellowGoal or obj == Object.BlueGoal) and (self.camera.getObjectsStatus()[obj] in (GoalStatus.FAR, GoalStatus.CLOSE)):
                self.log.info(f"Object {obj.name} Found")
                return True

            self.gyroMovement.spinToAngle(angle + 45)
            angle = self.gyro.get_z_angle()

            if (obj != Object.Ball):
                time.sleep(0.3)

        self.log.info("Spin search failed...")
        return False

    def goToBall(self, obj: Object = Object.Ball):
        pid = PidCalc(0.35, 0.2, 0.0, 100, True)
        pidDist = PidCalc(1, 0.3, 0.0, 100)
        error = self.camera.getObjects()[obj]
        try:
            while self.vcnl.proximity < 115 and error:
                print(error)

                correction = pid.pidCalc(-error.angle)
                speedY = pidDist.pidCalc(error.distance)

                self.motors.setSpeed(0, speedY, correction, back_only=(self.vcnl.proximity > 100))
                time.sleep(0.01)

                error = self.camera.getObjects()[obj]
        except Exception as e:
            self.log.error(f"{e}")
        finally:
            self.motors.stophard()

        if not self.camera.isObjectDetected(obj):
            self.motors.stop()
            self.tryBallDownSearch(obj)
            return None


    def tryBallDownSearch(self, obj: Object = Object.Ball) -> None:

        for angle in range(data.MAX_ANGLE, data.MIN_ANGLE, -20):
            self.servo.angle = angle
            if self.camera.isObjectDetected(obj):
                if angle <= data.MIN_ANGLE:
                    self.gyroMovement.move_forward_cm(20, (0, 40))
                self.servo.angle = angle - 15
                self.goToBall(obj=obj)
                return
    
    def goToGoal(self, obj: Object):
        error = self.camera.getObjects()[obj]

        self.log.debug(f"Found Ball at angle: {error.angle}. distance: {error.distance}")

        self.gyroMovement.spinToAngle(-error.distance)

        self.gyroMovement.move_until(speed=(0, 30), until=lambda: self.vcnl.proximity > 100)

    def hunt(self):
        while True:
            self.check_pause()
            status = self.camera.getObjectsStatus(self.vcnl.proximity)[Object.Ball]

            if status == BallStatus.CAM_DETECTED:
                self.log.info("Ball Detected!")
                self.dribbler.stop()
                self.goToBall()

            if status == BallStatus.NOT_FOUND:
                self.log.info("Ball Not Found!")
                self.servo.angle = data.GOOD_ANGLE
                self.dribbler.stop()
                if not self.spinSearch():
                    self.log.debug("Spin Search failed!")
                    self.gyroMovement.move_forward_cm(15, (0, 30), (0.4, 0.01, 0.1, 100))

            if status == BallStatus.VCNL_CLOSE:
                self.log.info("Ball is Close!")
                self.dribbler.start()
                self.gyroMovement.move_forward_cm(2, (0, 30), (0.4, 0.01, 0.1, 100))

            if status == BallStatus.VCNL_IN_KICKER:
                self.log.info("Ball in Kicker Position!")
                self.dribbler.start()
                obj: Object = Object.YellowGoal if data.SELF_IS_BLUE else Object.YellowGoal

                while True:
                    goalStatus = self.camera.getObjectsStatus()[obj]

                    if goalStatus == GoalStatus.NOT_FOUND:
                        self.log.info("Searching for goal!")
                        self.servo.angle = data.MAX_ANGLE
                        self.spinSearch(obj=obj)

                    if goalStatus == GoalStatus.FAR:
                        self.log.info("Going to Goal!")
                        self.goToBall(obj=obj)

                    if goalStatus == GoalStatus.CLOSE:
                        self.log.info("Kicked Ball!!!!!")
                        self.dribbler.counterStart()
                        sleep(0.4)
                        if self.camera.getObjectsStatus(self.vcnl.proximity)[Object.Ball] == BallStatus.CAM_DETECTED:
                            self.log.info("Goal!!!!! Game finished!")
                        else:
                            break
            self.motors.stop()

    def __del__(self):
        self.motors.stop()

if __name__ == "__main__":
    r = Hunt(debug=True)
    # r.hunt()
    r.goToBall()
    # while True:
    #     r.spinSearch()