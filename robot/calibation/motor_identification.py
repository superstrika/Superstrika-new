from robot.components.motor import motor7046
from robot.processes.multipleMotors import multipleMotors
import robot.consts.data as data

def main() -> None:
    motors = multipleMotors(data.MOTOR_PINS)
    speed = -100

    print(speed)
    motors.setSpeed(speed, 0, 0, 0)
    input()
    motors.setSpeed(0, speed, 0, 0)
    input()
    motors.setSpeed(0, 0, speed, 0)
    input()
    motors.setSpeed(0, 0, 0, speed)
    input()

if __name__ == "__main__":
    main()