import robot.components.motor as motor

class Dribbler:
    def __init__(self, pins: tuple[int, int]):
        self.dribbler = motor.motor7046(*pins)

    def start(self):
        self.dribbler.speed = 100

    def stop(self):
        self.dribbler.stop()

    def counterStart(self):
        self.dribbler.speed = 100

if __name__ == "__main__":
    import robot.consts.data as data

    s = Dribbler(data.DRIBBLER_PIN)
    s.start()
    input()
    s.stop()