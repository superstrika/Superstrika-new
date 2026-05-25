from robot.processes.pidCalc import PidCalc
import robot.consts.data as data
import robot.processes.multipleMotors
import robot.components.camera

def go():
    motors = robot.processes.multipleMotors.multipleMotors(data.MOTOR_PINS)
    camera = robot.components.camera.Camera7046()


    sp = data.ROBOT_BALL_DISTANCE

    pidY = PidCalc(0.8, 0, 0, 100, verbose=False)
    pidX = PidCalc(0.01, 0, 0.1, 100, verbose=False)

    pv = camera.getBallLocation()  # distance

    if pv[0] is None or pv[1] is None:
        motors.stop()
        return None

    while (abs(pv[0] - sp[0]) > data.GO_TO_BALL_ERROR) or (abs(pv[1] - sp[1]) > data.GO_TO_BALL_ERROR):

        speedX = pidX.pidCalc(pv[0] - sp[0])
        speedY = max(pidY.pidCalc(pv[1] - sp[1]), 25)

        print(f"{speedX=}, {speedY=}")

        motors.setSpeed(speedX, speedY, 0)

        pv = camera.getBallLocation()  # distance

        if pv[0] is None or pv[1] is None:
            motors.stop()
            return None

    return None

if __name__ == "__main__":
    go()