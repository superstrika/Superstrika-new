import serial
import logging
from robot.abstracts.ICamera import ICamera, DisplacementVector
from robot.consts.enum import Object, GoalStatus, BallStatus
import math

class OpenmvCamera(ICamera):
    def __init__(self, freq=115200):
        self.ser = serial.Serial(
            port='/dev/ttyACM0',
            baudrate=freq,
            timeout=2
        )

        self.log = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'cls': self.__class__.__name__}
        )

    def readMessage(self):
        while True:
            if self.ser.in_waiting > 0:
                return self.ser.readline().decode('utf-8').rstrip()

    def getBallLocation(self) -> tuple[float | None, float | None]:
        ballLocation: list[tuple[float, float]] = []
        try:
            self.ser.reset_input_buffer()
            for _ in range(2):
                response = self.readMessage()

                response: list[float] = response.split('#')
                for i in range(len(response)):
                    response[i] = float(response[i])
                ballLocation.append((response[0], response[1]))

            avgX: float | None = 0
            avgY: float | None = 0
            for r in ballLocation:
                avgX += r[0]
                avgY += r[1]
            avgX /= len(ballLocation)
            avgY /= len(ballLocation)

            if avgX == 999:
                avgX = None

            if avgY == 999:
                avgY = None

            return avgX, avgY

        except Exception as e:
            self.log.error(e)
            return None, None

    def isBallDetected(self) -> bool:
        dis = self.getBallLocation()
        if not dis[0] or not dis[1]:
            return False
        return True

    def getBlueGoalLocation(self) -> tuple[float | None, float | None]:
        goalLocation: list[tuple[float, float]] = []
        try:
            for _ in range(5):
                response = self.readMessage()

                response: list[float] = response.split('#')
                for i in range(len(response)):
                    response[i] = float(response[i])

                goalLocation.append((response[2], response[3]))

            avgX: float = 0
            avgY: float = 0
            for r in goalLocation:
                avgX += r[0]
                avgY += r[1]
            avgX /= len(goalLocation)
            avgY /= len(goalLocation)

            if avgX == 999:
                avgX = None

            if avgY == 999:
                avgY = None

            return avgX, avgY

        except Exception as e:
            self.log.error(e)
            return None, None

    def getYellowGoalLocation(self) -> tuple[float | None, float | None]:
        goalLocation: list[tuple[float, float]] = []
        try:
            for _ in range(5):
                response = self.readMessage()

                response: list[float] = response.split('#')
                for i in range(len(response)):
                    response[i] = float(response[i])

                goalLocation.append((response[4], response[5]))

            avgX: float = 0
            avgY: float = 0
            for r in goalLocation:
                avgX += r[0]
                avgY += r[1]
            avgX /= len(goalLocation)
            avgY /= len(goalLocation)

            if avgX == 999:
                avgX = None

            if avgY == 999:
                avgY = None

            return avgX, avgY

        except Exception as e:
            self.log.error(e)
            return None, None

    def getGoalLocation(self, blueGoal: bool) -> tuple[float | None, float | None]:
        if blueGoal:
            return self.getBlueGoalLocation()
        return self.getYellowGoalLocation()
    
    @staticmethod
    def convertToVector(info: tuple[float | None, float | None]) -> DisplacementVector | None:
        if not info[0] or not info[1]:
            return None
        
        return DisplacementVector(
            math.sqrt(info[0]**2 + info[1]**2),
            math.degrees(math.atan(info[0] / info[1]))
        )

    def getObjects(self) -> dict[Object, DisplacementVector]:
        return {
            Object.Ball: OpenmvCamera.convertToVector(self.getBallLocation()),
            Object.YellowGoal: OpenmvCamera.convertToVector(self.getYellowGoalLocation()),
            Object.BlueGoal: OpenmvCamera.convertToVector(self.getBlueGoalLocation())
        }

    def isObjectDetected(self, obj: Object) -> bool:
        if obj == Object.Ball:
            return not None in self.getBallLocation()
        
        if obj == Object.YellowGoal:
            return not None in self.getYellowGoalLocation()
        
        return not None in self.getBlueGoalLocation()


if __name__ == "__main__":
    ser = OpenmvCamera()
    while True:
        print(ser.getYellowGoalLocation())