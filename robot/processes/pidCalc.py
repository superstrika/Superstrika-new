import time
import os
import logging

class PidCalc:
    def __init__(self, kp: float, ki: float, kd: float, kt: float, maxSpeed: float, maxIntegral: float,
                 name: str = "pidCalc", verbose: bool = True) -> None:

        self.kp: float = kp
        self.ki: float = ki
        self.kd: float = kd
        self.kt: float = kt

        self.count = 0

        self.prevError: float = 0
        self.integral: float = 0

        self.lastTime: float = time.time()

        self.maxSpeed: float = abs(maxSpeed)
        self.maxIntegral: float = abs(maxIntegral)

        self.name = name
        self.verbose = verbose

        self.log = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'cls': self.__class__.__name__}
        )

    def pidCalc(self, error: float) -> float:
        if self.verbose:
            os.system('cls' if os.name == 'nt' else 'clear')
        self.log.info(f"--------------------{self.name}--------------------------")
        self.count += 1
        dt = time.time() - self.lastTime

        self.integral += error * dt

        derivative = (error - self.prevError) / (self.kt * dt) if dt > 0.1 else 0.0
        if self.count < 5:
            derivative = 0

        speed = self.kp * error + self.ki * self.integral + self.kd * derivative

        if self.verbose:
            print(f"Integral: {self.integral}")
            print(f"Derivative: {derivative}")
            print(f"Error: {error}")
            print(f"Speed: {speed}")
            print(f"Last Error: {self.prevError}")
            print(f"Dt: {dt}")

        self.log.info(f"Integral: {self.integral}")
        self.log.info(f"Derivative: {derivative}")
        self.log.info(f"Error: {error}")
        self.log.info(f"Speed: {speed}")
        self.log.info(f"Last Error: {self.prevError}")
        self.log.info(f"Dt: {dt}")

        self.lastTime = time.time()
        self.prevError = error

        # speed = max(-self.maxSpeed, max(self.maxSpeed, speed))
        if abs(speed) > self.maxSpeed:
            if speed > 0:
                speed = self.maxSpeed
            else:
                speed = -self.maxSpeed

        if self.verbose:
            print("----------------------------------------------")
        self.log.info("----------------------------------------------")
        return speed
