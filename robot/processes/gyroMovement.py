from robot.processes.pidCalc import PidCalc as PidCalc
from robot.components.gyro import MPU6050
from robot.components.motor import motor7046
from robot.processes.multipleMotors import multipleMotors
from smbus2 import SMBus as I2C  # For RPI compatibility
from time import sleep
import robot.consts.data as data
import robot.components.motor as motor
import time


class GyroMovement:
    def __init__(self, i2c: I2C = None, gyro: MPU6050 = None, motors: multipleMotors = None):
        if i2c and not gyro:
            self.i2c = i2c
            self.gyro = MPU6050(self.i2c)
        elif not gyro:
            self.i2c = I2C(1)
            self.gyro = MPU6050(self.i2c)
        else:
            self.i2c = None
            self.gyro = gyro

        if motors:
            self.motors = motors
        else:
            self.motors = multipleMotors(data.MOTOR_PINS)

    def spinToAngle(self, setPoint: int, pidValues: tuple=(0.35, 0.15, 0.01, 100), errorOffset: float=0.5) -> None:
        pid = PidCalc(*pidValues)
        error: float = setPoint - self.gyro.get_z_angle()

        while abs(error) > errorOffset:
            speed: float = pid.pidCalc(error)

            if 10 < speed < 30:
                speed += 20

            if -10 > speed > -30:
                speed -= 20

            self.motors.setSpeed(0, 0, speed)

            sleep(0.3)
            error: float = setPoint - self.gyro.get_z_angle()

    def move_forward_cm(self, distance_cm: float, speed=(30,30), pidValues: tuple=(1.5, 0.01, 0.1, 100)):
        """
        Moves the robot forward for a specified distance with gyro heading correction.
        Note: This implementation uses time as a proxy for distance.
        For exact distance, motor encoders would be required.
        """
        # 1. Record the starting heading to maintain it
        target_heading = self.gyro.get_z_angle()
        pid = PidCalc(*pidValues)

        duration = distance_cm * 0.05
        start_time = time.time()

        try:
            while time.time() - start_time < duration:
                current_heading = self.gyro.get_z_angle()
                correction = pid.pidCalc(target_heading - current_heading)

                self.motors.setSpeed(*speed, correction)
                time.sleep(0.01)
        finally:
            self.motors.stop()

if __name__ == "__main__":
    s = GyroMovement()

    s.move_forward_cm(25, pidValues=(0.4, 0.01, 0.1, 100), speed=(25, 50))
