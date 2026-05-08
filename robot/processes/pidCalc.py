import time
import os
import logging

class PidCalc:
    def __init__(self, kp: float, ki: float, kd: float, maxSpeed: float, verbose: bool = True) -> None:

        self.kp: float = kp
        self.ki: float = ki
        self.kd: float = kd

        self.prevError: float = 0
        self.integral: float = 0

        self.lastTime: float = time.time()

        self.maxSpeed: float = abs(maxSpeed)

        self.verbose = verbose

        self.log = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'cls': self.__class__.__name__}
        )

    def pidCalc(self, error: float) -> float:
        if self.verbose:
            os.system('cls' if os.name == 'nt' else 'clear')
        self.log.info(f"-------------------- PID --------------------------")
        dt = time.time() - self.lastTime

        if error * self.prevError < 0:
            self.integral = 0

        self.integral += error * dt

        if dt > 0:
            derivative = (error - self.prevError) / dt
            out = self.kp * error + self.ki * self.integral + self.kd * derivative
            self.prevError = error
            self.lastTime = time.time()

            if self.verbose:
                self.log.debug(f"Integral: {self.integral}")
                self.log.debug(f"Derivative: {derivative}")
                self.log.debug(f"Error: {error}")
                self.log.debug(f"Out: {out}")
                self.log.debug(f"Last Error: {self.prevError}")
                self.log.debug(f"Dt: {dt}")
                self.log.debug("----------------------------------------------")

            return max(-self.maxSpeed, min(out, self.maxSpeed))
        return 0