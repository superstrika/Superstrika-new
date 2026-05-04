import robot.components.motor as motor


def vectorSpeedCalculationTest():
    while True:
        Vx: int = int(input("Enter Vx: "))
        Vy: int = int(input("Enter Vy: "))
        Rot = input("Enter Rot (enter for 0): ")
        if Rot == "":
            Rot = 0
        else:
            Rot = int(Rot)

        print(motor.motor7046.calculate_speed(Vx, Vy, Rot))
        print("------------------------------------------")


def rotationSpeedCalculationTest():
    while True:
        speed: int = int(input("Enter speed: "))

        print(motor.motor7046.calculate_rotation_speed(speed))
        print("------------------------------------------")


if __name__ == "__main__":
    # vectorSpeedCalculationTest()
    rotationSpeedCalculationTest()