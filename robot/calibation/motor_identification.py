from robot.components.motor import motor7046
from robot.processes.multipleMotors import multipleMotors
import robot.consts.data as data

def main() -> None:
    motors = multipleMotors(data.MOTOR_PINS)
    speed = -100

    for i in range(4):
        motors.setMotorOn(i, speed)
        input("Press Enter to continue...")

if __name__ == "__main__":
    main()