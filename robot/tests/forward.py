from robot.processes.multipleMotors import multipleMotors
import robot.consts.data as data

def main():
    motors = multipleMotors(data.MOTOR_PINS)

    motors.setSpeed(0, 30, 0)
    input()
    motors.stop()

if __name__ == "__main__":
    main()