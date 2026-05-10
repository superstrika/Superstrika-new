from pidCalcLog import PidCalc
import robot.processes.multipleMotors as multipleMotors
import robot.components.camera as camera
import robot.consts.data as data
import logging

def moveToBall():
    logging.basicConfig(filename=data.LOG_PATH, filemode='w', level=logging.DEBUG, format=data.LOG_FORMAT)

    sp = data.ROBOT_BALL_DISTANCE
    cam = camera.Camera7046()
    motors = multipleMotors.multipleMotors(data.MOTOR_PINS)

    pidY = PidCalc(0.6, 0, 0, 100, verbose=False, csv_output="log/log.csv")

    pv = cam.getBallLocation()  # distance
    print(f"{pv=}")

    if pv[0] is None or pv[1] is None:
        motors.stop()
        return None

    while (abs(pv[0] - sp[0]) > data.GO_TO_BALL_ERROR) or (abs(pv[1] - sp[1]) > data.GO_TO_BALL_ERROR):

        speedY = max(pidY.pidCalc(pv[1] - sp[1]), 25)

        print(f"Vy: {speedY}")

        motors.setSpeed(0, speedY, 0)

        pv = cam.getBallLocation()

        if pv[0] is None or pv[1] is None:
            motors.stop()
            return None

    print(f"Got to Ball successfully... e: {pv[0] - sp[0]}, {pv[1] - sp[1]}")
    return None