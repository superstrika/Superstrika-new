import logging
import robot.components.motor as motor

class multipleMotors:
    def __init__(self, pins: list[int], parent=None):

        self.parent = parent

        motor1 = motor.motor7046(pins[0], pins[1], switch=False) #FR
        motor2 = motor.motor7046(pins[2], pins[3], switch=True) #FL
        motor3 = motor.motor7046(pins[4], pins[5], switch=True) #BL
        motor4 = motor.motor7046(pins[6], pins[7], switch=False) #BR

        self.motors: list[motor.motor7046] = [motor1, motor2, motor3, motor4]

        self.log = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'cls': self.__class__.__name__}
        )

    def stop(self, bypass_priority=False):
        self.waitForLock(bypass_priority)
        for mot in self.motors:
            mot.stop()

    def stophard(self, bypass_priority=False):
        self.waitForLock(bypass_priority)
        for mot in self.motors:
            mot.stophard()

    def waitForLock(self, bypass_priority=False):
        # lock:
        if self.parent and not bypass_priority:
            with self.parent.condition:
                while self.parent.priority_active:
                    self.log.warning("Waiting for interrupt...")
                    self.parent.condition.wait()

    def setSpeed(self, Vx: float, Vy: float, rotation: float, bypass_priority: bool=False, back_only: bool=False):
        self.waitForLock(bypass_priority=bypass_priority)

        # Front Right
        wheel1_speed = (Vy - Vx + rotation) if not back_only else 0.0
        # Rear Right
        wheel2_speed = Vx + Vy + rotation
        # Rear Left
        wheel3_speed = Vx - Vy + rotation
        # Front Left
        wheel4_speed = (-Vx - Vy + rotation) if not back_only else 0.0

        speeds = [wheel1_speed, wheel2_speed, wheel3_speed, wheel4_speed]
        # print(f"{speeds=}")

        self.log.debug(f"{speeds=}")

        for i in range(len(self.motors)):
            self.motors[i].speed = max(-100, min(100, speeds[i])) if abs(speeds[i]) > 0.01 else 0

    def setMotorOn(self, motorIndex: int, speed: int = 100):
        if motorIndex > 3 or motorIndex < 0:
            raise ValueError("Motor index out of range")

        for i in range(len(self.motors)):
            if i == motorIndex:
                self.motors[i].speed = speed
            else:
                self.motors[i].speed = 0