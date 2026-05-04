import robot.processes.multipleMotors as multipleMotors
import robot.components.motor as motor
import robot.consts.data as data
from time import sleep
import gpiozero
import logging
import threading


class EdgeLineDetection:
    def __init__(self, pins: list[int], motors: multipleMotors.multipleMotors = None, parent=None):
        if motors:
            self.motors = motors
        else:
            self.motors = multipleMotors.multipleMotors(data.MOTOR_PINS)

        self.leftIRQ = gpiozero.Button(pins[0])
        self.leftIRQ.when_activated = self.leftIRQ

        self.rightIRQ = gpiozero.Button(pins[1])
        self.rightIRQ.when_activated = self.rightIRQ

        self.forwardIRQ = gpiozero.Button(pins[2])
        self.forwardIRQ.when_activated = self.forwardIRQ

        if not parent:
            raise Exception("This process is an orphan :(")
        self.parent = parent

        self.escape_lock = threading.Lock()

        self.log = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'cls': self.__class__.__name__}
        )

    def escapeLeft(self):
        with self.escape_lock:
            print(f"Escaping left: {data.TCRT_PINS[0]}")
            speeds = motor.motor7046.calculate_speed(-100, 0, 0)

            with self.parent.condition:
                self.parent.priority_active = True

                self.motors.setSpeed(*(tuple(speeds)), bypass_priority=True)
                self.log.warning("Escaping left!")
                sleep(0.15)
                self.motors.stop()

                self.parent.priority_active = False
                self.parent.condition.notify_all()

    def escapeRight(self):
        with self.escape_lock:
            print(f"Escaping right: {data.TCRT_PINS[1]}")
            speeds = motor.motor7046.calculate_speed(100, 0, 0)

            with self.parent.condition:
                self.parent.priority_active = True

                self.motors.setSpeed(*(tuple(speeds)), bypass_priority=True)
                self.log.warning("Escaping right!")
                sleep(0.15)
                self.motors.stop()

                self.parent.priority_active = False
                self.parent.condition.notify_all()

    def escapeForward(self):
        with self.escape_lock:
            print(f"Escaping forward: {data.TCRT_PINS[2]}")
            speeds = motor.motor7046.calculate_speed(0, 100, 0)

            with self.parent.condition:
                self.parent.priority_active = True

                self.motors.setSpeed(*(tuple(speeds)), bypass_priority=True)
                self.log.warning("Escaping Forward!")
                sleep(0.15)
                self.motors.stop()

                self.parent.priority_active = False
                self.parent.condition.notify_all()

if __name__ == "__main__":
    e = EdgeLineDetection(data.TCRT_PINS)

    while True:
        sleep(0.1)