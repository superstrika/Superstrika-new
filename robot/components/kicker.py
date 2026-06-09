import robot.components.motor as motor
import logging
from time import sleep
import time

class Kicker:
    GEAR_TEETH = 1

    def __init__(self, pin1, pin2):
        self.motor = motor.motor7046(pin1, pin2, switch=False)
        motor.speed = 0

        self.log = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'cls': self.__class__.__name__}
        )

    def loadPoint(self, speed=33):
        cur = time.time()
        self.motor.speed = speed
        sleep(0.30)
        self.motor.stophard()
        print(f"{time.time() - cur}")
        

    def load(self, p: int):
        for i in range(Kicker.GEAR_TEETH):
            self.motor.speed = i * p
            sleep(i + 0.3)

    def release(self):
        self.log.info("Releasing")
        self.motor.speed = 100
        sleep(0.1)
        self.motor.stophard()

if __name__ == "__main__":
    import robot.consts.data as data
    k = Kicker(*data.KICKER_PIN)
    k.loadPoint()
    input()
    k.release()