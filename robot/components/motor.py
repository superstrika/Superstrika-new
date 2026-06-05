import gpiozero
import logging

class motor7046:
    _h = 0
    MIN_SPEED = 30

    def __init__(self, pin1, pin2, switch: bool = False):

        if switch:
            pin1, pin2 = pin2, pin1

        self.mot1 = gpiozero.PWMLED(pin1, frequency=800)
        self.mot2 = gpiozero.PWMLED(pin2, frequency=800)

        self._speed = 0.0
        self.mot1.value = 0  # start PWM with 0% duty cycle
        self.mot2.value = 0

        self.log = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'cls': self.__class__.__name__}
        )

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, speed: float):
        # self._speed = map(speed, -100, 100, -1, 1)
        self._speed = speed / 100
        self.log.debug(f"{self._speed}")
        pwm_value = abs(self._speed)

        if self._speed > 0:
            self.mot1.value = pwm_value
            self.mot2.value = 0
        elif self._speed < 0:
            self.mot1.value = 0
            self.mot2.value = pwm_value
        else:
            self.mot1.value = 0
            self.mot2.value = 0

        self.log.debug(f"Motor speed is now: {speed}")

    def stophard(self):
        self._speed = 0
        self.mot1.value = 1
        self.mot2.value = 1
        self.log.debug(f"Stopped hard!")

    def stop(self):
        self._speed = 0
        try:
            # Check if pins are open before using them
            if not getattr(self.mot1, 'closed', True):
                self.mot1.value = 0
            if not getattr(self.mot2, 'closed', True):
                self.mot2.value = 0
            self.log.debug(f"Motor speed is now: 0")
        except gpiozero.exc.GPIODeviceClosed:
            pass  # Already cleaned up by Python

    def __del__(self):
        self._speed = 0
        try:
            if not getattr(self.mot1, 'closed', True):
                self.mot1.value = 0
            if not getattr(self.mot2, 'closed', True):
                self.mot2.value = 0
        except gpiozero.exc.GPIODeviceClosed:
            pass

