import gpiozero

def on():
    p = gpiozero.LED(8)
    p.on()
