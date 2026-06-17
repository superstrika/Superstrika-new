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
import robot.components.camera as camera
from robot.processes.pidCalc import PidCalc
import robot.processes.gyroMovement as gyroMovement
import robot.processes.multipleMotors as multipleMotors
import threading

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
        self.camera = camera.Camera7046(data.SERIAL_FREQUENCY)

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

    def camSearch(self, obj: data.Object = data.Object.Ball) -> bool:
        """
        Changes camera angle until ball is found.
        :param delay: the delay each change of angle.
        :return: [0] - X coordinate of the returned object. [1] - Y coordinate of the returned object. None if not found.
        """

        self.log.info("Initializing Camera Search...")

        pv = self.getObjectLocation(obj)

        for angle in range(data.MAX_ANGLE, data.MIN_ANGLE, -35):
            self.servo.angle = angle
            pv = self.getObjectLocation(obj)
            if pv[0] is not None and pv[1] is not None:
                return True
            time.sleep(0.2)
        
        return False

    def spinSearch(self, delay=0.6, right: bool = True, obj: data.Object = data.Object.Ball) -> bool | None:
        """
        Spins the robot 360 degrees or until ball is found.
        :param delay: the delay between the start of spinning to first angle check.
        :param right: the direction of the spinning
        :param obj: which object to search: ball, yellow goal or blue goal
        :return: [0] - X coordinate of the returned object. [1] - Y coordinate of the returned object. None if not found.
        """

        self.log.info("Initializing Spin Search...")

        self.gyro.reset_theta()

        angle = self.gyro.get_z_angle()
        while abs(angle) < 360:
            if not self.running_gate.is_set():  # ------------------------------------------------------------------- Check if end button was pressed.
                return None
            
            print(f"{self.getGoalStatus(obj)}")

            if obj == data.Object.Ball and self.camSearch(obj):
                self.log.info(f"Object {obj.name} Found")
                return True
            elif (obj == data.Object.YellowGoal or obj == data.Object.BlueGoal) and (self.getGoalStatus(obj) == data.GoalStatus.FAR or self.getGoalStatus(obj) == data.GoalStatus.CLOSE):
                self.log.info(f"Object {obj.name} Found")
                return True

            self.gyroMovement.spinToAngle(angle + 45)
            angle = self.gyro.get_z_angle()

            if (obj != data.Object.Ball):
                time.sleep(0.3)

        self.log.info("Spin search failed...")
        return False

    # def goToBall(self, delay=0.005, obj: data.Object = data.Object.Ball) -> None:
    #     self.log.info("Going to Ball...")
    #     sp = data.ROBOT_BALL_DISTANCE if obj == data.Object.Ball else data.ROBOT_GOAL_DISTANCE

    #     pv = self.getObjectLocation(obj)  # distance

    #     pidY = PidCalc(0, 0, 0, 100, verbose=False, startError=pv[1])
    #     pidX = PidCalc(0.15, 0.001, 0.15, 100, verbose=True, startError=pv[0])

    #     time.sleep(1)

    #     if pv[0] is None or pv[1] is None:
    #         self.motors.stop()
    #         return None

    #     while (abs(pv[0] - sp[0]) > data.GO_TO_BALL_ERROR) or (abs(pv[1] - sp[1]) > data.GO_TO_BALL_ERROR):
    #         if not self.running_gate.is_set():  # ------------------------------------------------------------------- Check if end button was pressed.
    #             return None
            
    #         self.log.debug(f"{pv=}")

    #         speedX = pidX.pidCalc(pv[0] - sp[0])
    #         speedY = max(pidY.pidCalc(pv[1] - sp[1]), 25)

    #         self.log.debug(f"Vx: {speedX}, Vy: {speedY}")

    #         self.motors.setSpeed(speedX, speedY, 0)

    #         sleep(delay)

    #         pv = self.getObjectLocation(obj)

    #         if pv[0] is None or pv[1] is None:
    #             self.motors.stop()
    #             self.tryBallDownSearch(obj)
    #             return None

    #     self.log.info(f"Got to Object {obj.name} successfully... e: {pv[0] - sp[0]}, {pv[1] - sp[1]}")
    #     return None

    def goToBall(self, obj: data.Object = data.Object.Ball):
        pid = PidCalc(0.3, 0.3, 0.1, 100, True)
        pidDist = PidCalc(0.5, 0.3, 0.1, 100)
        xy = (0, 0)
        try:
            while self.vcnl.proximity < 115 and xy[0] is not None and xy[1] is not None:
                xy: list = self.getObjectLocation(obj)
                angle = math.degrees(math.atan(xy[0] / xy[1]))


                correction = pid.pidCalc(-angle)
                speedY = pidDist.pidCalc(math.sqrt(xy[0] ** 2 + xy[1] ** 2))

                self.motors.setSpeed(0, speedY, correction)
                time.sleep(0.01)
        except Exception as e:
            print(e)
        finally:
            self.motors.stophard()

        if xy[0] is None or xy[1] is None:
            self.motors.stop()
            self.tryBallDownSearch(obj)
            return None


    def tryBallDownSearch(self, obj: data.Object = data.Object.Ball) -> None:
        pv = self.getObjectLocation(obj)

        for angle in range(data.MAX_ANGLE, data.MIN_ANGLE, -20):
            self.servo.angle = angle
            pv = self.getObjectLocation(obj)
            if pv[0] is not None and pv[1] is not None:
                if angle <= data.MIN_ANGLE:
                    self.gyroMovement.move_forward_cm(20, (0, 40))
                self.servo.angle = angle - 15
                self.goToBall(obj=obj)
                return None

    def getBallStatus(self) -> data.BallStatus:
        vcnl_prox = self.vcnl.proximity
        cam_dist = self.camera.getBallLocation()
        self.log.debug(f"{cam_dist=}, {vcnl_prox=}")

        cam_found = True if cam_dist[0] and cam_dist[1] else False
        if vcnl_prox < data.VCNL_PROX_CLOSE and not cam_found:
            return data.BallStatus.NOT_FOUND

        if cam_found and vcnl_prox < data.VCNL_PROX_CLOSE:
            return data.BallStatus.CAM_DETECTED

        if not cam_found and data.VCNL_PROX_IN_KICKER > vcnl_prox > data.VCNL_PROX_CLOSE:
            return data.BallStatus.VCNL_CLOSE

        if not cam_found and data.VCNL_PROX_IN_KICKER < vcnl_prox:
            return data.BallStatus.VCNL_IN_KICKER

        return data.BallStatus.CAM_DETECTED_AND_VCNL_CLOSE

    def getGoalStatus(self, obj: data.Object) -> data.GoalStatus:
        dis: tuple = self.getObjectLocation(obj)
        print(f"{dis=}")

        if not dis[0] or not dis[1]:
            return data.GoalStatus.NOT_FOUND

        if dis[0] < data.ROBOT_GOAL_DISTANCE[0] and dis[1] < data.ROBOT_GOAL_DISTANCE[1]:
            return data.GoalStatus.CLOSE

        return data.GoalStatus.FAR

    def getObjectLocation(self, obj: data.Object) -> tuple[float | None, float | None] | tuple[None, None]:
        if obj == data.Object.Ball:
            return self.camera.getBallLocation()
        elif obj == data.Object.YellowGoal:
            return self.camera.getYellowGoalLocation()
        elif obj == data.Object.BlueGoal:
            return self.camera.getBlueGoalLocation()
        return None, None
    
    def goToGoal(self, obj: data.Object):
        xy: list = self.getObjectLocation(obj)
        angle = math.degrees(math.atan(xy[0] / xy[1]))

        self.log.debug(f"Found Ball at angle: {angle}. x: {xy[0]}, y: {xy[1]}")

        self.gyroMovement.spinToAngle(-angle)

        self.gyroMovement.move_until(speed=(0, 30), until=lambda: self.vcnl.proximity > 100)

    def hunt(self):
        while True:
            self.check_pause()
            status = self.getBallStatus()

            if status == data.BallStatus.CAM_DETECTED:
                self.log.info("Ball Detected!")
                self.dribbler.stop()
                self.goToBall()

            if status == data.BallStatus.NOT_FOUND:
                self.log.info("Ball Not Found!")
                self.servo.angle = data.GOOD_ANGLE
                self.dribbler.stop()
                if not self.spinSearch():
                    self.log.debug("Spin Search failed!")
                    self.gyroMovement.move_forward_cm(15, (0, 30), (0.4, 0.01, 0.1, 100))

            if status == data.BallStatus.VCNL_CLOSE:
                self.log.info("Ball is Close!")
                self.dribbler.start()
                self.gyroMovement.move_forward_cm(2, (0, 30), (0.4, 0.01, 0.1, 100))

            if status == data.BallStatus.VCNL_IN_KICKER:
                self.log.info("Ball in Kicker Position!")
                self.dribbler.start()
                obj: data.Object = data.Object.YellowGoal if data.SELF_IS_BLUE else data.Object.YellowGoal

                while True:
                    goalStatus = self.getGoalStatus(obj)

                    if goalStatus == data.GoalStatus.NOT_FOUND:
                        self.log.info("Searching for goal!")
                        self.servo.angle = data.MAX_ANGLE
                        self.spinSearch(obj=obj)

                    if goalStatus == data.GoalStatus.FAR:
                        self.log.info("Going to Goal!")
                        self.goToBall(obj=obj)

                    if goalStatus == data.GoalStatus.CLOSE:
                        self.log.info("Kicked Ball!!!!!")
                        self.dribbler.counterStart()
                        sleep(0.4)
                        if self.getBallStatus() == data.BallStatus.CAM_DETECTED:
                            self.log.info("Goal!!!!! Game finished!")
                        else:
                            break
            self.motors.stop()

    def __del__(self):
        self.motors.stop()

if __name__ == "__main__":
    r = Hunt(debug=True)
    r.hunt()