import serial
import time


def get_serial():
    # Use /dev/serial0 as the alias
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=2)
    ser.reset_input_buffer()
    return ser


ser = get_serial()
count = 0
print("Starts reciving...")
while True:
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            # if "P" in line:
            #     print("GOT P")
            #     ser.reset_input_buffer()
            #     time.sleep(2)
            #     continue
            if line:
                count += 1
                print(f"{count} Received: {line}")
        else:
            time.sleep(0.01)  # Don't hog CPU

    except (OSError, serial.SerialException) as e:
        print(f"Error {e}: Reconnecting...")
        try:
            ser.close()
            time.sleep(1)
            ser = get_serial()  # Hard rescet the connection
            ser.reset_input_buffer()
            print("Connected!")
        except:
            pass