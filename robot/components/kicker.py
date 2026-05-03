import motor
from time import sleep

class Kicker:
    GEAR_TEETH = 1

    def __init__(self, pin1, pin2):
        self.motor = motor.motor7046(pin1, pin2, switch=False)
        motor.speed = 0

    def loadPoint(self, speed=55):
        self.motor.speed = speed

    def load(self, p: int):
        for i in range(Kicker.GEAR_TEETH):
            if i * p > 100:
                self.motor.speed = 100
            else:
                self.motor.speed = i * p
            sleep(i + 0.3)

    def release(self):
        print("Releasing")
        self.motor.speed = -100
        sleep(0.5)
        self.motor.speed = 0