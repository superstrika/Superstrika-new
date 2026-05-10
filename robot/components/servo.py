import gpiozero
from time import sleep
import logging

class Servo:
    def __init__(self, pin: int):
        self.FREQ = 50

        self.servoAngle = 0

        self.servo = gpiozero.PWMLED(pin, frequency=self.FREQ)

        self.log = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'cls': self.__class__.__name__}
        )

    @staticmethod
    def calculateDuty(angle: int):
        return 2.5 + (angle / 180) * 10

    @property
    def angle(self):
        return self.servoAngle

    @angle.setter
    def angle(self, angle: int):
        self.setAngle(angle)

    def setAngle(self, angle: int, delay: float = 0.5):
        if angle < 0 or angle > 180:
            self.log.error("Error: angle must be between 0 and 180")
            raise Exception("Error: angle must be between 0 and 180")

        duty = map(Servo.calculateDuty(angle), 0, 100, 0, 1)
        self.servo.value = duty

        self.log.debug(f"Changed angle to {angle} in duty {duty}")

        self.servoAngle = angle

        sleep(delay)
        self.servo.value = 0