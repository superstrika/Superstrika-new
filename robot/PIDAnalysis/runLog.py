from .pidCalcLog import PidCalc
import robot.processes.multipleMotors as multipleMotors
import robot.components.camera as camera
import robot.consts.data as data
import logging
import sys
import os

def moveToBall(sp):
    os.makedirs(os.path.dirname(data.LOG_PATH), exist_ok=True)
    logging.basicConfig(filename=data.LOG_PATH, filemode='w', level=logging.DEBUG, format=data.LOG_FORMAT)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(data.LOG_FORMAT))

    log = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'cls': __name__}
        )
    log.logger.addHandler(console_handler)

    cam = camera.Camera7046()
    # motors = multipleMotors.multipleMotors(data.MOTOR_PINS)

    pidY = PidCalc(0.6, 0, 0, 100, verbose=True, csv_output="log/log.csv")

    pv = cam.getBallLocation()  # distance
    print(f"{pv=}")

    if pv[0] is None or pv[1] is None:
        # motors.stop()
        return None

    while (abs(pv[1] - sp[1]) > 1):

        speedY = pidY.pidCalc(pv[1] - sp[1])

        print(f"Vy: {speedY}, Pv: {pv}")

        # motors.setSpeed(0, speedY, 0)

        pv = cam.getBallLocation()

        if pv[0] is None or pv[1] is None:
            # motors.stop()
            return None

    print(f"Got to Ball successfully... e: {pv[0] - sp[0]}, {pv[1] - sp[1]}")
    return None

if __name__ == "__main__":
    moveToBall((0, 10))