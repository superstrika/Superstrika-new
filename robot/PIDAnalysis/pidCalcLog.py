import time
import os
import logging
import csv
from datetime import datetime
import robot.consts.data as data

class PidCalc:
    def __init__(self, kp: float, ki: float, kd: float, maxSpeed: float, verbose: bool = True, csv_output: str = None) -> None:

        self.kp: float = kp
        self.ki: float = ki
        self.kd: float = kd

        self.prevError: float = 0
        self.integral: float = 0

        self.lastTime: float = time.time()

        self.maxSpeed: float = abs(maxSpeed)

        self.verbose = verbose

        # CSV logging
        self.csv_output = csv_output
        self.data_buffer = []  # Store data in RAM
        self.start_time = time.time()

        self.log = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'cls': self.__class__.__name__}
        )

    def pidCalc(self, error: float) -> float:
        if self.verbose:
            os.system('cls' if os.name == 'nt' else 'clear')
        self.log.info(f"-------------------- PID --------------------------")
        dt = time.time() - self.lastTime

        if error * self.prevError < 0:
            self.integral = 0

        self.integral += error * dt

        if dt > 0:
            derivative = (error - self.prevError) / dt
            out = self.kp * error + self.ki * self.integral + self.kd * derivative
            self.prevError = error
            self.lastTime = time.time()

            # Store data to buffer instead of logging every time
            if self.csv_output:
                timestamp = datetime.now().isoformat()
                self.data_buffer.append({
                    'Timestamp': timestamp,
                    'Error': error,
                    'Integral': self.integral,
                    'Derivative': derivative,
                    'Out': out
                })

            if self.verbose:
                self.log.debug(f"Integral: {self.integral}")
                self.log.debug(f"Derivative: {derivative}")
                self.log.debug(f"Error: {error}")
                self.log.debug(f"Out: {out}")
                self.log.debug(f"Last Error: {self.prevError}")
                self.log.debug(f"Dt: {dt}")
                self.log.debug("----------------------------------------------")

            return max(-self.maxSpeed, min(out, self.maxSpeed))
        return 0

    def write_csv(self) -> None:
        """Write collected data to CSV file"""
        if not self.csv_output or not self.data_buffer:
            return
        
        try:
            os.makedirs(os.path.dirname(self.csv_output), exist_ok=True)
            with open(self.csv_output, 'w', newline='') as csvfile:
                fieldnames = ['Timestamp', 'Error', 'Integral', 'Derivative', 'Out']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.data_buffer)
            self.log.info(f"PID data written to {self.csv_output}")
        except Exception as e:
            self.log.error(f"Failed to write CSV: {e}")

    def __del__(self):
        """Automatically write CSV on object deletion"""
        self.write_csv()

