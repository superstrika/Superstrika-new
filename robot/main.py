import components.servo as servo
import components.motor as motor
from time import sleep
import processes.EdgeLineDetection as EdgeLineDetection
import components.gyro as gyro
import components.dribbler as dribbler
# import input7046
import consts.data as data
from components.vcnl import VCNL4040 as VCNL
import logging
import components.camera as camera
from processes.pidCalc import PidCalc
import processes.gyroMovement as gyroMovement
import processes.multipleMotors as multipleMotors
import threading
import math

try:
    from machine import I2C
except ImportError:
    from smbus2 import SMBus as I2C  # For RPI compatibility

logging.basicConfig(filename=data.LOG_PATH, filemode='w', level=logging.DEBUG, format=data.LOG_FORMAT)


class Hunt:
    def __init__(self):
        # race conditions of motors
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        self.priority_active = False

        # exit gate
        self.running_gate = threading.Event()
        self.running_gate.clear()

        # motors
        self.i2c = I2C(data.I2C_ID)
        self.servo = servo.Servo(data.SERVO_PIN, data.CHIP_ID)
        self.motors = multipleMotors.multipleMotors(data.MOTOR_PINS, parent=self)
        self.dribbler = dribbler.Dribbler(data.DRIBBLER_PIN)

        # sensors
        self.gyro = gyro.MPU6050(self.i2c)
        self.serial = camera.Camera7046(data.SERIAL_FREQUENCY)

        # vcnl
        self.vcnl = VCNL()
        self.vcnl.led_current = self.vcnl.LED_100MA
        self.vcnl.proximity_high_definition = True
        self.vcnl.proximity_integration_time = self.vcnl.PS_8T

        # processes
        # self.lineDetection = edgeLineDetection.EdgeLineDetection(pins=data.TCRT_PINS, chipID=data.CHIP_ID, motors=self.motors, parent=self)
        self.gyroMovement = gyroMovement.GyroMovement(self.i2c, self.gyro, self.motors)
        mainSwitch7046.Switch7046(self, data.START_BUTTON_PIN)

        self.log = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'cls': self.__class__.__name__}
        )

    def check_pause(self, timeout=None):
        return self.running_gate.wait(timeout=timeout)

    def camSearch(self, delay=0.3) -> tuple[float, float] | None:
        """
        Changes camera angle until ball is found.
        :param delay: the delay each change of angle.
        :return: [0] - X coordinate of the returned object. [1] - Y coordinate of the returned object. None if not found.
        """

        self.log.info("Initializing Camera Search...")
        print("Initializing Camera Search...")

        self.servo.angle = data.MAX_ANGLE

        for angle in range(data.MAX_ANGLE, data.MIN_ANGLE, -10):

            self.servo.setAngle(angle, delay * ((data.MAX_ANGLE - angle) / data.MIN_ANGLE))

            ballX, ballY = self.serial.getBallLocation()
            if ballX != 0 or ballY != 0:
                self.log.info(f"Ball Found: {ballX}, {ballY}")
                print(f"Ball Found: {ballX}, {ballY}")
                return ballX, ballY

        self.log.info("Camera Search failed...")
        print("Camera Search failed...")
        return None

    def spinSearch(self, delay=0.25, right: bool = True, obj: data.Object = data.Object.Ball) -> bool | None:
        """
        Spins the robot 360 degrees or until ball is found.
        :param delay: the delay between the start of spinning to first angle check.
        :param right: the direction of the spinning
        :param obj: which object to search: ball, yellow goal or blue goal
        :return: [0] - X coordinate of the returned object. [1] - Y coordinate of the returned object. None if not found.
        """
        speed = data.ROTATION_SPEED if right else -data.ROTATION_SPEED

        self.log.info("Initializing Spin Search...")
        print("Initializing Spin Search...")

        self.gyro.reset_theta()

        startAngle = self.gyro.get_z_angle()
        speeds = motor.motor7046.calculate_rotation_speed(speed)
        self.motors.setSpeed(*tuple(speeds))
        sleep(delay)
        self.motors.stop()
        print(f"DEBUG: start Angle: {startAngle}")

        angle = self.gyro.get_z_angle()
        # print(f"DEBUG: Start angle: {angle}")
        # print(f"DEBUG: startAngle: {startAngle}")
        # print(f"DEBUG: error: {data.SPIN_SEARCH_ERROR}")
        while abs(angle) < 360:
            if not self.running_gate.is_set():  # ------------------------------------------------------------------- Check if end button was pressed.
                return None

                # input(f"Stopped... {self.serial.getBallLocation()}")
            if obj == data.Object.Ball:
                end = self.getBallStatus() != data.BallStatus.NOT_FOUND
            else:
                end = self.getGoalStatus(obj) != data.GoalStatus.NOT_FOUND

            if end:
                self.log.info(f"Object {obj.name} Found")
                print(f"Object {obj.name} Found")
                return True

            self.motors.setSpeed(*tuple(speeds))
            sleep(delay)

            angle = self.gyro.get_z_angle()
            print(f"The angle: {angle}")

            self.motors.stop()

        self.log.info("Spin search failed...")
        print("Spin search failed...")
        return False

    def goToBall(self, delay=0.3, obj: data.Object = data.Object.Ball) -> None:
        self.log.info("Going to Ball...")
        print("Going to Ball...")
        sp = data.ROBOT_BALL_DISTANCE if obj == data.Object.Ball else data.ROBOT_GOAL_DISTANCE

        pidY = PidCalc(0.6, 0, 0, 100, 100, 500, verbose=False)
        pidX = PidCalc(0.01, 0, 0.1, 100, 100, 500, verbose=False)

        pv = self.getObjectLocation(obj)  # distance
        print(f"{pv=}")

        if not pv[0] or not pv[1]:
            self.motors.stop()
            return None
            # pv = self.serial.getBallLocation()

        while (abs(pv[0] - sp[0]) > data.GO_TO_BALL_ERROR) or (abs(pv[1] - sp[1]) > data.GO_TO_BALL_ERROR):
            if not self.running_gate.is_set():  # ------------------------------------------------------------------- Check if end button was pressed.
                return None

            speedX = pidX.pidCalc(pv[0] - sp[0])
            speedY = max(pidY.pidCalc(pv[1] - sp[1]), 25)

            print(f"Vx: {speedX}, Vy: {speedY}")

            self.motors.setSpeed(*tuple(motor.motor7046.calculate_speed(speedX, speedY, 0)))

            sleep(delay)
            pv = self.getObjectLocation(obj)

            if pv[0] is None or pv[1] is None:
                self.motors.stop()
                return None

        self.log.info(f"Got to Object {obj.name} successfully... e: {pv[0] - sp[0]}, {pv[1] - sp[1]}")
        print(f"Got to Object {obj.name} successfully... e: {pv[0] - sp[0]}, {pv[1] - sp[1]}")
        return None

    def getBallStatus(self) -> data.BallStatus:
        vcnl_prox = self.vcnl.proximity
        cam_dist = self.serial.getBallLocation()
        print(f"{cam_dist=}, {vcnl_prox=}")

        cam_found = True if cam_dist[0] and cam_dist[1] else False
        if vcnl_prox < data.VCNL_PROX_NOT_DETECTED and not cam_found:
            return data.BallStatus.NOT_FOUND

        if cam_found and vcnl_prox < data.VCNL_PROX_NOT_DETECTED:
            return data.BallStatus.CAM_DETECTED

        if not cam_found and data.VCNL_PROX_IN_KICKER > vcnl_prox > data.VCNL_PROX_NOT_DETECTED:
            return data.BallStatus.VCNL_CLOSE

        if not cam_found and data.VCNL_PROX_IN_KICKER < vcnl_prox:
            return data.BallStatus.VCNL_IN_KICKER

        return data.BallStatus.CAM_DETECTED_AND_VCNL_CLOSE

    def getGoalStatus(self, obj: data.Object) -> data.GoalStatus:
        dis: tuple = self.getObjectLocation(obj)

        if not dis[0] or not dis[1]:
            return data.GoalStatus.NOT_FOUND

        if dis[0] < data.ROBOT_GOAL_DISTANCE[0] or dis[1] < data.ROBOT_GOAL_DISTANCE[1]:
            return data.GoalStatus.CLOSE

        return data.GoalStatus.FAR

    def getObjectLocation(self, obj: data.Object) -> tuple[float | None, float | None]:
        if obj == data.Object.Ball:
            return self.serial.getBallLocation()
        elif obj == data.Object.YellowGoal:
            return self.serial.getYellowGoalLocation()
        elif obj == data.Object.BlueGoal:
            return self.serial.getBlueGoalLocation()
        return (None, None)

    def hunt(self):
        while True:
            self.check_pause()
            status = self.getBallStatus()

            if status == data.BallStatus.CAM_DETECTED:
                print("Ball Detected!")
                self.dribbler.stop()
                self.goToBall()

            if status == data.BallStatus.NOT_FOUND:
                print("Ball Not Found!")
                self.servo.angle = data.GOOD_ANGLE
                self.dribbler.stop()
                if not self.spinSearch():
                    self.servo.angle = data.MIN_ANGLE
                    if not self.spinSearch():
                        self.gyroMovement.move_forward_cm(30, 30)

            if status == data.BallStatus.VCNL_CLOSE:
                print("Ball is Close!")
                self.dribbler.start()
                self.gyroMovement.move_forward_cm(15, 30)

            if status == data.BallStatus.CAM_DETECTED_AND_VCNL_CLOSE:
                print("Ball is Close but not that much!")
                self.dribbler.start()
                self.gyroMovement.move_forward_cm(30, 30)

            if status == data.BallStatus.VCNL_IN_KICKER:
                print("Ball in Kicker Position!")
                self.dribbler.start()
                obj: data.Object = data.Object.YellowGoal if data.SELF_IS_BLUE else data.Object.YellowGoal

                while True:
                    goalStatus = self.getGoalStatus(obj)

                    if goalStatus == data.GoalStatus.NOT_FOUND:
                        print("Searching for goal!")
                        self.spinSearch(obj=obj)

                    if goalStatus == data.GoalStatus.FAR:
                        print("Going to Goal!")
                        self.goToBall(obj=obj)

                    if goalStatus == data.GoalStatus.CLOSE:
                        print("Kicked Ball!!!!!")
                        self.dribbler.counterStart()
                        sleep(0.4)
                        if self.getBallStatus() == data.BallStatus.CAM_DETECTED:
                            print("Goal!!!!! Game finished!")
                        else:
                            break
            self.motors.stop()

    def __del__(self):
        self.motors.stop()


# class Keep:
#     def __init__(self):
#         # motors
#         self.i2c = I2C(data.I2C_ID)
#         self.servo = servo.Servo(data.SERVO_PIN, data.CHIP_ID)
#         self.motors = multipleMotors(data.MOTOR_PINS, data.CHIP_ID, verbose=False, speedVerbose=True)
#
#         # sensors
#         self.gyro = gyro.MPU6050(self.i2c)
#         self.serial = serial7046.Serial7046(data.SERIAL_FREQUENCY)
#
#         # race conditions
#         # self.lock = threading.Lock()
#         # self.condition = threading.Condition(self.lock)
#         # self.priority_active = False
#
#         # processes
#         # self.lineDetection = edgeLineDetection.EdgeLineDetection(pins=data.TCRT_PINS, chipID=data.CHIP_ID, motors=self.motors, parent=self)
#         self.gyroMovement = gyroMovement.GyroMovement(self.i2c, self.gyro, self.motors,
#                                                       pidValues=[0.25, 0.01, 0.01, 500, 100, 100])
#
#         self.log = logging.LoggerAdapter(
#             logging.getLogger(__name__),
#             {'cls': self.__class__.__name__}
#         )
#
#     def trackBall(self):
#         self.log.info("Tracking Ball")
#         print("Tracking Ball")
#
#         pid = PidCalc(1.2, 0.2, 0.1, 150, 100, 500, verbose=False)
#
#         while True:
#             deltaX = self.serial.getBallLocation()[0]
#
#             if deltaX == 0:
#                 continue
#
#             speedX = pid.pidCalc(deltaX)
#             self.motors.setSpeed(*tuple(motor.motor7046.calculate_speed(speedX, 0, 0)))


if __name__ == "__main__":
    # try:
    if data.SELF_IS_HUNTER:
        r = Hunt()
        # r.spinSearch(0.25)
        # r.spinToBall()
        # r.camSearch(delay=0.3)
        # r.spinToBall()
        # while True:
        #     pass
        # r.spinSearch()
        # r.spinToBall()
        r.hunt()
    else:
        pass
        # r = Keep()

        # r.trackBall()
    # except KeyboardInterrupt:
    #     r.motors.stop()