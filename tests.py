import gpiozero
import time

try:
    # Use one of your motor pins to test initialization
    test_pin = gpiozero.PWMLED(23)
    print("GPIO System is working perfectly!")
    test_pin.value = 0.5
    time.sleep(1)
    test_pin.value = 0
except Exception as e:
    print(f"GPIO Error: {e}")