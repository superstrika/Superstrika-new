from time import sleep
import robot.components.servo as servo
import robot.consts.data as data


class servoCalibration:

    def __init__(self, servo_: int | servo.Servo, auto_calibrate: bool = False):
        if type(servo_) == type(servo.Servo):
            self._servo = servo_
        else:
            self._servo = servo.Servo(servo_)

        self.MIN_ANGLE = data.MIN_ANGLE
        self.MAX_ANGLE = data.MAX_ANGLE

        if auto_calibrate:
            self.calibrate()

    def calibrate(self):
        input("Press enter to start the calibration...")
        self._servo.angle = self.MAX_ANGLE

        print(f"Moving servo to {self.MAX_ANGLE} deg. Move the camera to the desired position.")

        input("To continue press enter...")
        self._servo.angle = self.MIN_ANGLE

        print(f"Moving servo to {self.MIN_ANGLE} deg. Make sure this is the desired \"min\" position.")

        print("Enter 'y' to repeat.")
        i_char = input()

        if i_char == 'y':
            self.calibrate()


if __name__ == "__main__":
    cal = servoCalibration(data.SERVO_PIN, True)