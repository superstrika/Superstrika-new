gimport motor

class multipleMotors:
    def __init__(self, pins: list[int], parent=None):

        self.parent = parent

        motor1 = motor.motor7046(pins[0], pins[1], switch=False)
        motor2 = motor.motor7046(pins[2], pins[3], switch=False)
        motor3 = motor.motor7046(pins[4], pins[5], switch=True)
        motor4 = motor.motor7046(pins[6], pins[7], switch=True)

        self.motors: list[motor.motor7046] = [motor1, motor2, motor3, motor4]

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
                    print("Waiting for interrupt...")
                    self.parent.condition.wait()

    def setSpeed(self, V1, V2, V3, V4, bypass_priority=False):
        self.waitForLock(bypass_priority)

        self.motors[0].speed = V1
        self.motors[1].speed = V2
        self.motors[2].speed = V3
        self.motors[3].speed = V4