# Superstrika

Software for the **Superstrika** RoboCup Junior Soccer robot, developed by the team at **Gvanim School (Ein Shemer)**. The project runs on a Raspberry Pi and brings together robot movement, sensor input, ball detection, and match behaviour.

## What it does

- Drives a four-wheel omnidirectional base.
- Uses a camera model to detect the ball and goals.
- Reads hardware such as the MPU6050 gyro, VCNL4040 proximity sensor, line sensors, servo, dribbler, and kicker.
- Provides hunter behaviour, movement control with PID correction, calibration tools, and hardware tests.

## Dependencies installation

1. Install the system dependencies:

   ```bash
   sudo apt update
   sudo apt install neovim build-essential swig python3-dev liblgpio-dev
   ```

2. Create a virtual environment if one does not already exist:

   ```bash
   python3 -m venv venv
   ```

3. Activate it:

   ```bash
   source venv/bin/activate
   ```

4. Install the project requirements:

   ```bash
   pip3 install -r robot/requirements.txt
   ```

5. Install the vision packages:

   ```bash
   pip3 install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu ultralytics torch torchvision
   ```

## Running with Docker

The Docker image holds only the dependencies. The code is bind-mounted from this repo, so editing it on the Pi only needs a container restart. GitHub Actions rebuilds the image (`ghcr.io/superstrika/superstrika-new`) when `Dockerfile`, `constraints.txt` or `robot/requirements.txt` change.

Set up a new Pi (Docker installed, I2C/SPI/UART enabled in `raspi-config`):

```bash
git clone https://github.com/superstrika/Superstrika-new.git
cd Superstrika-new
docker compose pull
docker compose up -d
```

`robot-core` runs `main.py` and starts again automatically after a reboot. Everyday commands:

```bash
docker compose restart robot-core     # after editing code
docker compose logs -f robot-core     # watch output
docker compose up -d console          # start the web console (manual only, http://<pi>:8080)
docker compose stop console           # stop the web console
docker compose run --rm robot-core python3 -m robot.calibration.servo_calibration
```

The console launches `main.py` itself, so stop `robot-core` before using it to keep two processes off the same hardware.

## Project structure

```text
.
├── main.py                 # Selects and starts the current robot entry point
├── tests.py                # Top-level test script
├── robot/
│   ├── hunter.py           # Main attacking (hunter) behaviour
│   ├── keeper.py           # Goalkeeper behaviour
│   ├── joy_ride.py         # Manual movement sequence for testing
│   ├── components/         # Hardware drivers: motors, cameras, gyro, sensors, servo, kicker
│   ├── processes/          # Higher-level control: multi-motor drive, PID, gyro movement, line detection
│   ├── consts/             # Robot configuration, pins, constants, and enums
│   ├── models/             # ONNX models used for vision detection
│   ├── calibration/        # Motor and servo calibration scripts
│   ├── tests/              # Focused hardware and camera test scripts
│   ├── PIDAnalysis/        # PID logging and analysis utilities
│   ├── console/            # Local web console and its configuration
│   └── requirements.txt    # Python dependencies
├── startup/                # Raspberry Pi service/startup configuration
└── log/                    # Runtime log output
```

## Configuration and running

Hardware pins, sensor settings, camera dimensions, and game options are defined in `robot/consts/data.py`. The main application entry point is `main.py`; choose the behaviour or test you want to run there, then start it from the repository root:

```bash
python3 main.py
```

Useful standalone scripts include:

```bash
python3 -m robot.calibration.motor_identification
python3 -m robot.calibration.servo_calibration
python3 -m robot.tests.captureFrames
```

To inspect devices connected to the Raspberry Pi I2C bus:

```bash
sudo i2cdetect -y 1
```

## Special thanks

- [Gal Arbel](https://github.com/galarb) — Team mentor
- [Tomer Ozer](https://github.com/TomerOzer) — Team member
- [Yoav Aharoni](https://github.com/teddybearpc) — Team member
- [Noam Ron](https://github.com/NoamRon1) — Team member
- [Itamar Hoter Ishai](https://github.com/itamarhoter) — Team member

*Maintained by the Superstrika Team.*
