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

        # Line detection flags (True = line detected)
        self.line_detected = {
            'left': False,
            'right': False,
            'forward': False
        }
        self.flags_lock = threading.Lock()
        self.escape_lock = threading.Lock()

        self.currently_escaping = False

        # Setup gpiozero buttons with correct callbacks
        self.leftIRQ = gpiozero.Button(pins[0], bounce_time=0.05)
        self.leftIRQ.when_pressed = self.on_left_line_detected
        self.leftIRQ.when_released = self.on_left_line_cleared

        self.rightIRQ = gpiozero.Button(pins[1], bounce_time=0.05)
        self.rightIRQ.when_pressed = self.on_right_line_detected
        self.rightIRQ.when_released = self.on_right_line_cleared

        self.forwardIRQ = gpiozero.Button(pins[2], bounce_time=0.05)
        self.forwardIRQ.when_pressed = self.on_forward_line_detected
        self.forwardIRQ.when_released = self.on_forward_line_cleared

        if not parent:
            raise Exception("This process is an orphan :(")
        self.parent = parent

        self.log = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'cls': self.__class__.__name__}
        )

    # Left sensor callbacks
    def on_left_line_detected(self):
        with self.flags_lock:
            if not self.line_detected['left']:
                self.line_detected['left'] = True
                self.log.warning("Left line detected!")
                self._trigger_escape()

    def on_left_line_cleared(self):
        with self.flags_lock:
            self.line_detected['left'] = False
            self.log.info("Left line cleared")

    # Right sensor callbacks
    def on_right_line_detected(self):
        with self.flags_lock:
            if not self.line_detected['right']:
                self.line_detected['right'] = True
                self.log.warning("Right line detected!")
                self._trigger_escape()

    def on_right_line_cleared(self):
        with self.flags_lock:
            self.line_detected['right'] = False
            self.log.info("Right line cleared")

    # Forward sensor callbacks
    def on_forward_line_detected(self):
        with self.flags_lock:
            if not self.line_detected['forward']:
                self.line_detected['forward'] = True
                self.log.warning("Forward line detected!")
                self._trigger_escape()

    def on_forward_line_cleared(self):
        with self.flags_lock:
            self.line_detected['forward'] = False
            self.log.info("Forward line cleared")

    def _trigger_escape(self):
        """Execute escape in a separate thread to avoid blocking sensor callbacks"""
        thread = threading.Thread(target=self._execute_escape, daemon=True)
        thread.start()

    def _execute_escape(self):
        """Execute escape maneuver"""
        with self.escape_lock:
            if self.currently_escaping:
                return
            self.currently_escaping = True

            if self.line_detected['left'] and self.line_detected['right'] and self.line_detected['forward']:
                self.log.error("All TCRT detects a line! Please recalibrate the sensors")
                raise Exception("All TCRT detects a line! Please recalibrate the sensors")

            # TODO: If 'left' + 'right' could be forward or backward
            if self.line_detected['left'] and self.line_detected['right']:
                speeds = motor.motor7046.calculate_speed(0, 100, 0)
                self.log.warning("Left and right escape detected! Escaping Forward!")

            elif self.line_detected['left']:
                speeds = motor.motor7046.calculate_speed(-100, 0, 0)
                self.log.warning("Escaping left!")

            elif self.line_detected['right']:
                speeds = motor.motor7046.calculate_speed(100, 0, 0)
                self.log.warning("Escaping right!")

            elif self.line_detected['forward']:
                speeds = motor.motor7046.calculate_speed(0, 100, 0)
                self.log.warning("Escaping forward!")

            with self.parent.condition:
                self.parent.priority_active = True

                self.motors.setSpeed(*(tuple(speeds)), bypass_priority=True)
                sleep(0.15)
                self.motors.stop()

                self.parent.priority_active = False
                self.parent.condition.notify_all()
            self.currently_escaping = False