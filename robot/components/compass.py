#!/usr/bin/env python3
"""
HMC5883L compass (HW-007 / GY-271) on a Raspberry Pi 4 - heading only.

Wiring: VCC->pin 1 (3.3V), GND->pin 6, SDA->pin 3, SCL->pin 5
Setup:  sudo apt install -y i2c-tools python3-smbus2   (and enable I2C in raspi-config)

Heading uses only X and Y, so keep the board FLAT (chip facing up).
You rotate it around the Z axis (like a turntable). The "X" arrow printed on
the board is the direction the heading refers to: 0 = X arrow points north.

Run:
    python3 compass.py --calibrate   # spin the flat board slowly 2-3 full turns
    python3 compass.py
"""
import argparse
import json
import math
import os
import time

from smbus2 import SMBus

ADDR = 0x1E
DECLINATION_DEG = 5.0   # Israel ~ +5 deg E; set 0 for magnetic north
CAL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "compass_cal.json")


def s16(hi, lo):
    v = (hi << 8) | lo
    return v - 65536 if v & 0x8000 else v


def init(bus):
    bus.write_byte_data(ADDR, 0x00, 0x70)  # 8-sample average, 15 Hz
    bus.write_byte_data(ADDR, 0x01, 0x20)  # gain +/-1.3 Ga
    bus.write_byte_data(ADDR, 0x02, 0x00)  # continuous mode
    time.sleep(0.1)


def read_xy(bus):
    # Output registers are X, Z, Y (big-endian). Z is read but ignored.
    d = bus.read_i2c_block_data(ADDR, 0x03, 6)
    return s16(d[0], d[1]), s16(d[4], d[5])


def calibrate(bus, seconds=30):
    print(f"Keep the board flat and rotate it slowly 2-3 full turns ({seconds} s)...")
    xs, ys = [], []
    end = time.time() + seconds
    while time.time() < end:
        x, y = read_xy(bus)
        if x != -4096 and y != -4096:  # -4096 = overflow
            xs.append(x); ys.append(y)
        time.sleep(0.07)
    cal = {
        "x_off": (max(xs) + min(xs)) / 2, "y_off": (max(ys) + min(ys)) / 2,
        "x_rng": (max(xs) - min(xs)) / 2 or 1, "y_rng": (max(ys) - min(ys)) / 2 or 1,
    }
    with open(CAL_FILE, "w") as f:
        json.dump(cal, f)
    print("Saved:", cal)


def heading(x, y, cal):
    # Remove offset (hard iron) and equalise the X/Y scale so the circle is round.
    xc = (x - cal["x_off"]) / cal["x_rng"]
    yc = (y - cal["y_off"]) / cal["y_rng"]
    return (math.degrees(math.atan2(yc, xc)) + DECLINATION_DEG) % 360


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibrate", action="store_true")
    args = ap.parse_args()

    with SMBus(1) as bus:
        init(bus)
        if args.calibrate:
            calibrate(bus)
            return
        try:
            with open(CAL_FILE) as f:
                cal = json.load(f)
        except (OSError, ValueError):
            print("No calibration found - run with --calibrate first. Using raw values.")
            cal = {"x_off": 0, "y_off": 0, "x_rng": 1, "y_rng": 1}
        try:
            while True:
                x, y = read_xy(bus)
                print(f"{heading(x, y, cal):6.1f}°")
                time.sleep(0.2)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()